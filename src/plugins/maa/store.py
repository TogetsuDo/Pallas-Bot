from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any

from ulid import ULID

from src.common.config import UserConfig
from src.common.db.modules import UserConfigModule

from .tasks import MaaTaskSpec, build_task_payload, normalize_device_id


@dataclass(slots=True)
class NotifyTarget:
    bot_id: int
    user_id: int
    group_id: int | None = None


@dataclass(slots=True)
class PendingTask:
    task_id: str
    user: str
    device: str
    task_type: str
    params: str | None
    notify: NotifyTarget
    created_at: float = field(default_factory=time.time)
    reported: bool = False


@dataclass(slots=True)
class DeviceRecord:
    device: str
    verified: bool = False
    last_seen: float = field(default_factory=time.time)


class MaaStore:
    """MAA 设备登记、任务队列（内存）；已绑定设备列表持久化到 UserConfig。"""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._seen: dict[tuple[str, str], float] = {}
        self._pending: dict[str, PendingTask] = {}
        self._active_device: dict[str, str] = {}

    async def touch_seen(self, user: str, device: str, ttl: int) -> None:
        norm = normalize_device_id(device)
        if not norm:
            return
        key = (user.strip(), norm)
        if not key[0] or not key[1]:
            return
        now = time.time()
        async with self._lock:
            self._seen[key] = now
            cutoff = now - ttl
            self._seen = {k: ts for k, ts in self._seen.items() if ts >= cutoff}

    async def was_seen(self, user: str, device: str, ttl: int) -> bool:
        norm = normalize_device_id(device)
        if not norm:
            return False
        key = (user.strip(), norm)
        now = time.time()
        async with self._lock:
            ts = self._seen.get(key)
            return ts is not None and now - ts <= ttl

    async def bind_device(self, qq_id: int, user: str, device: str, ttl: int) -> str | None:
        user_key = str(qq_id)
        norm_device = normalize_device_id(device)
        if not norm_device:
            return "设备标识符格式不正确。"
        if user.strip() != user_key:
            return "MAA 用户标识符须填写你的 QQ 号，与当前账号不一致。"
        if not await self.was_seen(user, norm_device, ttl):
            return "未检测到该设备向牛牛轮询，请先在 MAA 中配置远控端点并保存后再试。"
        cfg = UserConfig(qq_id)
        devices = await self._load_devices(cfg)
        devices[norm_device] = DeviceRecord(device=norm_device, verified=True, last_seen=time.time())
        payload = {k: {"verified": v.verified, "last_seen": v.last_seen} for k, v in devices.items()}
        await cfg._update("maa_devices", payload)
        async with self._lock:
            self._active_device[user_key] = norm_device
        return None

    async def list_devices(self, qq_id: int) -> list[DeviceRecord]:
        cfg = UserConfig(qq_id)
        return list((await self._load_devices(cfg)).values())

    async def get_active_device(self, qq_id: int) -> str | None:
        user_key = str(qq_id)
        async with self._lock:
            active = self._active_device.get(user_key)
        if active:
            return active
        devices = await self.list_devices(qq_id)
        verified = [d for d in devices if d.verified]
        if len(verified) == 1:
            return verified[0].device
        return None

    async def set_active_device(self, qq_id: int, device: str) -> str | None:
        devices = await self.list_devices(qq_id)
        matched = next((d for d in devices if d.device == device and d.verified), None)
        if not matched:
            return "未找到已绑定的该设备，请先使用「牛牛绑定MAA」完成绑定。"
        async with self._lock:
            self._active_device[str(qq_id)] = device
        return None

    async def enqueue(
        self,
        qq_id: int,
        specs: list[MaaTaskSpec],
        notify: NotifyTarget,
        *,
        attach_screenshot: bool,
    ) -> tuple[list[str], str | None]:
        user_key = str(qq_id)
        device = await self.get_active_device(qq_id)
        if not device:
            return [], "尚未绑定 MAA 设备，请私聊发送「牛牛绑定MAA <设备标识符>」。"
        devices = await self.list_devices(qq_id)
        if not any(d.device == device and d.verified for d in devices):
            return [], "当前设备未绑定或已失效，请重新绑定。"

        task_ids: list[str] = []
        async with self._lock:
            for spec in specs:
                task_id = str(ULID())
                self._pending[task_id] = PendingTask(
                    task_id=task_id,
                    user=user_key,
                    device=device,
                    task_type=spec.task_type,
                    params=spec.params,
                    notify=notify,
                )
                task_ids.append(task_id)
            if attach_screenshot and specs and specs[-1].task_type not in {"CaptureImage", "CaptureImageNow"}:
                shot_id = str(ULID())
                self._pending[shot_id] = PendingTask(
                    task_id=shot_id,
                    user=user_key,
                    device=device,
                    task_type="CaptureImage",
                    params=None,
                    notify=notify,
                )
                task_ids.append(shot_id)
        return task_ids, None

    async def pending_tasks_for(self, user: str, device: str) -> list[dict[str, Any]]:
        norm = normalize_device_id(device)
        if not norm:
            return []
        key_user, key_device = user.strip(), norm
        async with self._lock:
            items = [
                t for t in self._pending.values() if t.user == key_user and t.device == key_device and not t.reported
            ]
        return [
            build_task_payload(t.task_id, MaaTaskSpec(t.task_type, t.params))
            for t in sorted(items, key=lambda x: x.created_at)
        ]

    async def mark_reported(self, task_id: str) -> PendingTask | None:
        async with self._lock:
            task = self._pending.get(task_id)
            if not task:
                return None
            task.reported = True
            return task

    async def pending_count_for_user(self, qq_id: int) -> int:
        user_key = str(qq_id)
        async with self._lock:
            return sum(1 for t in self._pending.values() if t.user == user_key and not t.reported)

    async def is_device_verified(self, user: str, device: str) -> bool:
        try:
            qq_id = int(user.strip())
        except ValueError:
            return False
        devices = await self.list_devices(qq_id)
        norm = normalize_device_id(device)
        if not norm:
            return False
        return any(d.device == norm and d.verified for d in devices)

    async def _load_devices(self, cfg: UserConfig) -> dict[str, DeviceRecord]:
        coll = UserConfigModule.get_pymongo_collection()
        doc = await coll.find_one({"user_id": cfg.user_id}, projection={"maa_devices": 1})
        raw = (doc or {}).get("maa_devices")
        if not isinstance(raw, dict):
            return {}
        out: dict[str, DeviceRecord] = {}
        for device_id, meta in raw.items():
            if not isinstance(device_id, str) or not isinstance(meta, dict):
                continue
            out[device_id] = DeviceRecord(
                device=device_id,
                verified=bool(meta.get("verified")),
                last_seen=float(meta.get("last_seen") or 0),
            )
        return out


maa_store = MaaStore()

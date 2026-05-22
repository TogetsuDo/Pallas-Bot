"""分片 worker：跨片同步 repeater 内存近期群消息（供 learn / 接话上下文）。"""

from __future__ import annotations

import asyncio
import os
import time
import uuid
from collections import deque
from typing import TYPE_CHECKING, Any

from nonebot import logger

from src.common.paths import plugin_data_dir
from src.common.shard.registry.config import get_shard_registry_settings, is_sharding_active

if TYPE_CHECKING:
    from src.plugins.repeater.model import ChatData

_PLUGIN = "pallas_shard"
_TTL_SEC = 90.0
_MAX_GROUP_TAIL = 256
_seen_event_ids: deque[str] = deque(maxlen=8000)
_seen_set: set[str] = set()


def _coord_dir():
    from pathlib import Path

    root = Path(plugin_data_dir(_PLUGIN, create=True)) / "coord" / "repeater_buffer"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _session_lock_path(path) -> Any:
    return path.with_suffix(path.suffix + ".lock")


def _acquire_lock(lock_path, *, timeout: float = 3.0) -> int | None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            return os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            try:
                if time.time() - lock_path.stat().st_mtime > 10.0:
                    lock_path.unlink(missing_ok=True)
            except OSError:
                pass
            time.sleep(0.02)
    return None


def _release_lock(fd: int | None, lock_path) -> None:
    if fd is not None:
        try:
            os.close(fd)
        except OSError:
            pass
    try:
        lock_path.unlink(missing_ok=True)
    except OSError:
        pass


def _read(path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    import json

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return raw if isinstance(raw, dict) else None


def _write_atomic(path, data: dict[str, Any]) -> None:
    import json

    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def _mutate(path, fn) -> dict[str, Any] | None:
    lk = _session_lock_path(path)
    fd = _acquire_lock(lk)
    if fd is None:
        return _read(path)
    try:
        data = _read(path) or {}
        fn(data)
        _write_atomic(path, data)
        return data
    finally:
        _release_lock(fd, lk)


def _remember_event(event_id: str) -> None:
    if event_id in _seen_set:
        return
    _seen_event_ids.append(event_id)
    _seen_set.add(event_id)
    while len(_seen_set) > len(_seen_event_ids):
        _seen_set.clear()
        _seen_set.update(_seen_event_ids)
    overflow = len(_seen_event_ids) - _seen_event_ids.maxlen
    if overflow > 0:
        for _ in range(overflow):
            old = _seen_event_ids.popleft()
            _seen_set.discard(old)


def _registry_shard_ids() -> frozenset[int]:
    from src.common.shard.registry.store import load_shard_registry

    reg = load_shard_registry()
    return frozenset(int(s.id) for s in reg.shards)


def message_payload_from_chat_data(chat_data: ChatData) -> dict[str, Any]:
    return {
        "group_id": int(chat_data.group_id),
        "user_id": int(chat_data.user_id),
        "bot_id": int(chat_data.bot_id),
        "raw_message": str(chat_data.raw_message),
        "is_plain_text": bool(chat_data.is_plain_text),
        "plain_text": str(chat_data.plain_text),
        "keywords": str(chat_data.keywords),
        "time": int(chat_data.time),
    }


def publish_repeater_buffer_event_sync(chat_data: ChatData) -> None:
    if not is_sharding_active():
        return
    if get_shard_registry_settings().role != "worker":
        return
    event_id = uuid.uuid4().hex
    now = time.time()
    path = _coord_dir() / f"{event_id}.json"
    payload = {
        "event_id": event_id,
        "source_shard_id": int(get_shard_registry_settings().shard_id),
        "created_at": now,
        "expires_at": now + _TTL_SEC,
        "msg": message_payload_from_chat_data(chat_data),
        "applied_shard_ids": [],
    }
    _write_atomic(path, payload)


def schedule_publish_repeater_buffer(chat_data: ChatData) -> None:
    if not is_sharding_active():
        return

    async def job() -> None:
        try:
            await asyncio.to_thread(publish_repeater_buffer_event_sync, chat_data)
        except Exception as err:
            logger.debug(f"repeater_buffer publish: {err}")

    asyncio.create_task(job())


def _message_tail_dup(group_msgs: list, msg: dict[str, Any]) -> bool:
    uid = int(msg["user_id"])
    t = int(msg["time"])
    plain = str(msg.get("plain_text") or "")
    for m in group_msgs[-8:]:
        if int(m.user_id) == uid and int(m.time) == t and str(m.plain_text or "") == plain:
            return True
    return False


async def apply_repeater_buffer_message(msg: dict[str, Any]) -> bool:
    from src.common.db import Message as MessageModel
    from src.plugins.repeater.message_store import MessageStore

    group_id = int(msg["group_id"])
    async with MessageStore._message_lock:
        group_msgs = MessageStore._message_dict[group_id]
        if _message_tail_dup(group_msgs, msg):
            return False
        group_msgs.append(
            MessageModel.model_construct(
                group_id=group_id,
                user_id=int(msg["user_id"]),
                bot_id=int(msg["bot_id"]),
                raw_message=str(msg["raw_message"]),
                is_plain_text=bool(msg["is_plain_text"]),
                plain_text=str(msg["plain_text"]),
                keywords=str(msg["keywords"]),
                time=int(msg["time"]),
            )
        )
        if len(group_msgs) > _MAX_GROUP_TAIL:
            del group_msgs[: len(group_msgs) - _MAX_GROUP_TAIL]
    return True


async def poll_repeater_buffer_pending() -> None:
    if not is_sharding_active():
        return
    if get_shard_registry_settings().role != "worker":
        return
    local_shard = int(get_shard_registry_settings().shard_id)
    all_shards = _registry_shard_ids()
    now = time.time()
    for path in _coord_dir().glob("*.json"):
        if ".lock" in path.name:
            continue
        data = await asyncio.to_thread(_read, path)
        if not data:
            continue
        if now > float(data.get("expires_at") or 0):
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass
            continue
        event_id = str(data.get("event_id") or path.stem)
        if event_id in _seen_set:
            continue
        source = int(data.get("source_shard_id") or -1)
        if source == local_shard:
            _remember_event(event_id)
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass
            continue
        msg = data.get("msg")
        if not isinstance(msg, dict):
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass
            continue
        await apply_repeater_buffer_message(msg)
        _remember_event(event_id)

        def mark_applied(d: dict[str, Any]) -> None:
            applied = d.setdefault("applied_shard_ids", [])
            if local_shard not in applied:
                applied.append(local_shard)

        updated = await asyncio.to_thread(_mutate, path, mark_applied)
        targets = all_shards - {source}
        applied = frozenset(int(x) for x in (updated or data).get("applied_shard_ids") or [])
        if targets <= applied:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass


async def prune_stale_repeater_buffer_files() -> None:
    now = time.time()
    for path in _coord_dir().glob("*.json"):
        row = await asyncio.to_thread(_read, path)
        if row is None:
            continue
        if now > float(row.get("expires_at") or 0) + 30.0:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass

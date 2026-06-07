"""分片：AI 异步任务登记，供 hub 将 /callback 转发到对应 worker。"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from nonebot import logger

from src.foundation.paths import plugin_data_dir
from src.platform.shard.coord.ai_task_registry_redis import (
    read_ai_task_redis_sync,
    remove_ai_task_redis_sync,
    write_ai_task_redis_sync,
)
from src.platform.shard.coord.maa_route_registry import current_worker_port
from src.platform.shard.registry import get_shard_registry, worker_port_for_shard
from src.platform.shard.registry.config import get_shard_registry_settings, is_sharding_active
from src.platform.shard.registry.store import assign_bot_to_shard

_PLUGIN = "pallas_shard"
_DEFAULT_TTL_SEC = 86400.0


def ai_task_ttl_sec() -> float:
    raw = os.getenv("PALLAS_AI_TASK_TTL_SEC", "").strip()
    try:
        ttl = float(raw) if raw else _DEFAULT_TTL_SEC
    except ValueError:
        ttl = _DEFAULT_TTL_SEC
    return max(600.0, ttl)


def _tasks_dir() -> Path:
    root = Path(plugin_data_dir(_PLUGIN, create=True)) / "coord" / "ai_tasks"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _task_path(task_id: str) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in task_id)
    return _tasks_dir() / f"{safe}.json"


def _lock_path(path: Path) -> Path:
    return path.with_suffix(path.suffix + ".lock")


def _acquire_lock(lock_path: Path, *, timeout: float = 3.0) -> int | None:
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


def _release_lock(fd: int | None, lock_path: Path) -> None:
    if fd is not None:
        try:
            os.close(fd)
        except OSError:
            pass
    try:
        lock_path.unlink(missing_ok=True)
    except OSError:
        pass


def _read(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return raw if isinstance(raw, dict) else None


def _write_atomic(path: Path, data: dict[str, Any]) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def _is_stale(rec: dict[str, Any]) -> bool:
    start = float(rec.get("start_time") or 0)
    return start <= 0 or (time.time() - start) > ai_task_ttl_sec()


def build_ai_task_record(task_id: str, task_status: dict[str, Any]) -> dict[str, Any] | None:
    bot_raw = task_status.get("bot_id")
    if bot_raw is None:
        return None
    bot_id = str(bot_raw).strip()
    if not bot_id.isdigit():
        return None
    reg = get_shard_registry()
    local_port = current_worker_port()
    if local_port is not None:
        sid = int(get_shard_registry_settings().shard_id)
        port = int(local_port)
    else:
        sid = reg.shard_for_bot(bot_id)
        if sid is None:
            sid = assign_bot_to_shard(bot_id, registry=reg)
        port = worker_port_for_shard(int(sid), registry=reg)
    return {
        "task_id": task_id,
        "bot_id": bot_id,
        "group_id": task_status.get("group_id"),
        "shard_id": int(sid),
        "worker_port": int(port),
        "start_time": float(task_status.get("start_time") or time.time()),
    }


def register_ai_task_file_sync(rec: dict[str, Any]) -> bool:
    task_id = str(rec.get("task_id") or "").strip()
    if not task_id:
        return False
    path = _task_path(task_id)
    lk = _lock_path(path)
    fd = _acquire_lock(lk)
    if fd is None:
        logger.warning("ai_task registry file lock timeout: task_id={}", task_id)
        return False
    try:
        _write_atomic(path, rec)
        return True
    finally:
        _release_lock(fd, lk)


def register_ai_task(task_id: str, task_status: dict[str, Any]) -> None:
    if not is_sharding_active():
        return
    rec = build_ai_task_record(task_id, task_status)
    if rec is None:
        return
    ttl = int(ai_task_ttl_sec())
    write_ai_task_redis_sync(rec, ttl_sec=ttl)
    register_ai_task_file_sync(rec)


def remove_ai_task(task_id: str) -> None:
    if not is_sharding_active():
        return
    remove_ai_task_redis_sync(task_id)
    path = _task_path(task_id)
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


def get_ai_task_record(task_id: str) -> dict[str, Any] | None:
    if not is_sharding_active():
        return None
    rec = read_ai_task_redis_sync(task_id)
    if rec is None:
        rec = _read(_task_path(task_id))
    if not rec or _is_stale(rec):
        remove_ai_task(task_id)
        return None
    return rec


def resolve_worker_port_for_task(task_id: str) -> int | None:
    rec = get_ai_task_record(task_id)
    if not rec:
        return None
    try:
        return int(rec["worker_port"])
    except (KeyError, TypeError, ValueError):
        return None

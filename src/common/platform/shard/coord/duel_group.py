"""跨 worker 同群决斗互斥：共享 data 层占用，避免多片同时开战。"""

from __future__ import annotations

import json
import os
import time
from typing import Any

from src.common.foundation.paths import plugin_data_dir
from src.common.platform.shard.registry.config import (
    get_shard_registry_settings,
    is_sharding_active,
)

_PLUGIN = "pallas_shard"
_BUSY_TTL_SEC = 7200.0
# 占用后若未登记双牛对局（如主持牛校验失败），超过该秒数视为孤儿锁可回收
_ORPHAN_BUSY_MIN_AGE_SEC = 30.0
_local_busy: set[int] = set()


def _coord_dir():
    from pathlib import Path

    root = Path(plugin_data_dir(_PLUGIN, create=True)) / "coord" / "duel_group"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _lock_path(group_id: int):
    return _coord_dir() / f"{int(group_id)}.json"


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
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return raw if isinstance(raw, dict) else None


def _write_atomic(path, data: dict[str, Any]) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def _mutate(path, fn, *, retries: int = 8) -> dict[str, Any] | None:
    for attempt in range(max(1, retries)):
        lk = _session_lock_path(path)
        fd = _acquire_lock(lk)
        if fd is None:
            if attempt + 1 < retries:
                time.sleep(0.03 * (attempt + 1))
                continue
            return _read(path)
        try:
            data = _read(path) or {}
            fn(data)
            _write_atomic(path, data)
            return data
        finally:
            _release_lock(fd, lk)
    return _read(path)


def _has_live_session(data: dict[str, Any]) -> bool:
    pair = data.get("session_pair")
    if not isinstance(pair, (list, tuple)) or len(pair) != 2:
        return False
    until = float(data.get("session_until") or 0)
    return until > time.time()


def is_orphan_duel_group_lock(data: dict[str, Any] | None) -> bool:
    """文件层 busy 但无有效 session：多为非主持牛开团后未 end 的泄漏。"""
    if not data or not data.get("busy"):
        return False
    acquired = float(data.get("acquired_at") or 0)
    if acquired <= 0 or time.time() < acquired + _ORPHAN_BUSY_MIN_AGE_SEC:
        return False
    return not _has_live_session(data)


def mark_duel_group_session(group_id: int, bot_a: int, bot_b: int) -> None:
    """双牛对局已开始：写入共享文件，供跨 worker 孤儿锁判断。"""
    gid = int(group_id)
    if not is_sharding_active():
        return
    path = _lock_path(gid)
    now = time.time()

    def stamp(data: dict[str, Any]) -> None:
        data["session_pair"] = [int(bot_a), int(bot_b)]
        data["session_until"] = now + _BUSY_TTL_SEC

    _mutate(path, stamp)


def try_begin_duel_group(group_id: int) -> bool:
    """同群同时进行中的决斗至多一场（分片时跨 worker）。"""
    gid = int(group_id)
    if not is_sharding_active():
        if gid in _local_busy:
            return False
        _local_busy.add(gid)
        return True

    path = _lock_path(gid)
    now = time.time()
    sid = get_shard_registry_settings().shard_id
    acquired = False

    def claim(data: dict[str, Any]) -> None:
        nonlocal acquired
        until = float(data.get("until") or 0)
        if until > now and data.get("busy"):
            acquired = False
            return
        data.update({
            "group_id": gid,
            "busy": True,
            "until": now + _BUSY_TTL_SEC,
            "shard_id": int(sid),
            "acquired_at": now,
        })
        acquired = True

    _mutate(path, claim)
    return acquired


def end_duel_group(group_id: int) -> None:
    gid = int(group_id)
    if not is_sharding_active():
        _local_busy.discard(gid)
        return

    path = _lock_path(gid)

    def release(data: dict[str, Any]) -> None:
        data["busy"] = False
        data["until"] = 0
        data.pop("session_pair", None)
        data.pop("session_until", None)

    _mutate(path, release)


async def prune_stale_duel_group_files(*, max_age_sec: float = 3600.0) -> int:
    root = _coord_dir()
    if not root.is_dir():
        return 0
    now = time.time()
    removed = 0
    for path in root.glob("*.json"):
        try:
            raw = _read(path)
            if isinstance(raw, dict) and raw.get("busy") and float(raw.get("until") or 0) > now:
                continue
            if now - path.stat().st_mtime <= max_age_sec:
                continue
            path.unlink(missing_ok=True)
            removed += 1
        except OSError:
            pass
    return removed


async def try_reclaim_orphan_duel_group(group_id: int) -> bool:
    """
    回收泄漏的群决斗占用：busy 较久且协调文件无有效 session_pair。
    不依赖本 worker 内存 duel_pair，避免分片下误判/漏判。
    """
    gid = int(group_id)
    if not is_sharding_active():
        if gid not in _local_busy:
            return False
        from src.plugins.duel.duel_session import get_duel_pair

        if await get_duel_pair(gid) is not None:
            return False
        _local_busy.discard(gid)
        return True

    path = _lock_path(gid)
    data = _read(path)
    if not is_orphan_duel_group_lock(data):
        return False
    end_duel_group(gid)
    return True

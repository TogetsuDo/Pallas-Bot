"""分片 worker：跨片同步 repeater 牛牛回复缓存（供「不可以」等 ban 匹配）。"""

from __future__ import annotations

import asyncio
import os
import time
import uuid
from collections import deque
from typing import Any

from nonebot import logger

from src.foundation.paths import plugin_data_dir
from src.platform.shard.registry.config import get_shard_registry_settings, is_sharding_active

_PLUGIN = "pallas_shard"
_REDIS_CHANNEL = "pallas:repeater_reply_buffer"
_TTL_SEC = 120.0
_MAX_BOT_TAIL = 64
_seen_event_ids: deque[str] = deque(maxlen=8000)
_seen_set: set[str] = set()
_redis_listener_started = False


def _coord_dir():
    from pathlib import Path

    root = Path(plugin_data_dir(_PLUGIN, create=True)) / "coord" / "repeater_reply_buffer"
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
    from src.platform.shard.registry.store import get_shard_registry

    reg = get_shard_registry()
    return frozenset(int(s.id) for s in reg.shards)


def reply_record_payload(group_id: int, bot_id: int, record: dict[str, Any]) -> dict[str, Any]:
    return {
        "group_id": int(group_id),
        "bot_id": int(bot_id),
        "time": int(record.get("time") or 0),
        "pre_raw_message": str(record.get("pre_raw_message") or ""),
        "pre_keywords": str(record.get("pre_keywords") or ""),
        "reply": str(record.get("reply") or ""),
        "reply_keywords": str(record.get("reply_keywords") or ""),
    }


def buffer_event_envelope(
    group_id: int,
    bot_id: int,
    record: dict[str, Any],
    *,
    event_id: str | None = None,
) -> dict[str, Any]:
    return {
        "event_id": event_id or uuid.uuid4().hex,
        "source_shard_id": int(get_shard_registry_settings().shard_id),
        "record": reply_record_payload(group_id, bot_id, record),
    }


def publish_repeater_reply_buffer_redis_sync(envelope: dict[str, Any]) -> bool:
    from src.platform.coord.redis_settings import coord_redis_enabled

    if not coord_redis_enabled():
        return False
    from src.platform.coord.redis_claim import get_coord_redis_client

    client = get_coord_redis_client()
    if client is None:
        return False
    import json

    try:
        body = json.dumps(envelope, ensure_ascii=False, separators=(",", ":"))
        client.publish(_REDIS_CHANNEL, body)
        return True
    except Exception:
        return False


def publish_repeater_reply_buffer_file_sync(envelope: dict[str, Any]) -> None:
    event_id = str(envelope["event_id"])
    now = time.time()
    path = _coord_dir() / f"{event_id}.json"
    payload = {
        **envelope,
        "created_at": now,
        "expires_at": now + _TTL_SEC,
        "applied_shard_ids": [],
    }
    _write_atomic(path, payload)


def publish_repeater_reply_record_sync(group_id: int, bot_id: int, record: dict[str, Any]) -> None:
    if not is_sharding_active():
        return
    if get_shard_registry_settings().role != "worker":
        return
    envelope = buffer_event_envelope(group_id, bot_id, record)
    if publish_repeater_reply_buffer_redis_sync(envelope):
        return
    publish_repeater_reply_buffer_file_sync(envelope)


def schedule_publish_repeater_reply_record(group_id: int, bot_id: int, record: dict[str, Any]) -> None:
    if not is_sharding_active():
        return

    async def job() -> None:
        try:
            await asyncio.to_thread(publish_repeater_reply_record_sync, group_id, bot_id, record)
        except Exception as err:
            logger.debug(f"repeater_reply_buffer publish: {err}")

    asyncio.create_task(job())


def _record_tail_dup(records: list, record: dict[str, Any]) -> bool:
    t = int(record.get("time") or 0)
    reply = str(record.get("reply") or "")
    keywords = str(record.get("reply_keywords") or "")
    for item in records[-8:]:
        if int(item.get("time") or 0) == t and str(item.get("reply") or "") == reply:
            if str(item.get("reply_keywords") or "") == keywords:
                return True
    return False


async def apply_repeater_reply_record(record: dict[str, Any]) -> bool:
    from src.plugins.repeater.model import Chat

    group_id = int(record["group_id"])
    bot_id = int(record["bot_id"])
    entry = {
        "time": int(record.get("time") or 0),
        "pre_raw_message": str(record.get("pre_raw_message") or ""),
        "pre_keywords": str(record.get("pre_keywords") or ""),
        "reply": str(record.get("reply") or ""),
        "reply_keywords": str(record.get("reply_keywords") or ""),
    }
    async with Chat._reply_lock:
        bucket = Chat._reply_dict[group_id][bot_id]
        if _record_tail_dup(bucket, entry):
            return False
        bucket.append(entry)
        if len(bucket) > _MAX_BOT_TAIL:
            del bucket[: len(bucket) - _MAX_BOT_TAIL]
    return True


async def ingest_repeater_reply_buffer_event(data: dict[str, Any]) -> None:
    event_id = str(data.get("event_id") or "")
    if not event_id or event_id in _seen_set:
        return
    local_shard = int(get_shard_registry_settings().shard_id)
    source = int(data.get("source_shard_id") or -1)
    if source == local_shard:
        _remember_event(event_id)
        return
    record = data.get("record")
    if not isinstance(record, dict):
        return
    await apply_repeater_reply_record(record)
    _remember_event(event_id)


async def poll_repeater_reply_buffer_pending() -> None:
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
        record = data.get("record")
        if not isinstance(record, dict):
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass
            continue
        await ingest_repeater_reply_buffer_event(data)

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


async def repeater_reply_buffer_redis_listen_loop() -> None:
    from src.platform.coord.redis_claim import get_coord_redis_client
    from src.platform.coord.redis_settings import coord_redis_enabled

    while True:
        if not is_sharding_active() or get_shard_registry_settings().role != "worker":
            return
        if not coord_redis_enabled():
            await asyncio.sleep(5.0)
            continue
        client = get_coord_redis_client()
        if client is None:
            await asyncio.sleep(5.0)
            continue
        pubsub = None
        try:
            pubsub = client.pubsub(ignore_subscribe_messages=True)
            await asyncio.to_thread(pubsub.subscribe, _REDIS_CHANNEL)
            while is_sharding_active():
                raw = await asyncio.to_thread(pubsub.get_message, timeout=1.0)
                if not raw or raw.get("type") != "message":
                    continue
                import json

                body = raw.get("data")
                if isinstance(body, bytes):
                    body = body.decode("utf-8")
                if not isinstance(body, str):
                    continue
                try:
                    data = json.loads(body)
                except json.JSONDecodeError:
                    continue
                if isinstance(data, dict):
                    await ingest_repeater_reply_buffer_event(data)
        except Exception as err:
            logger.debug(f"repeater_reply_buffer redis listen: {err}")
            await asyncio.sleep(2.0)
        finally:
            if pubsub is not None:
                try:
                    await asyncio.to_thread(pubsub.close)
                except Exception:
                    pass


def start_repeater_reply_buffer_redis_listener() -> None:
    global _redis_listener_started
    if _redis_listener_started or not is_sharding_active():
        return
    if get_shard_registry_settings().role != "worker":
        return
    from src.platform.coord.redis_settings import coord_redis_enabled

    if not coord_redis_enabled():
        return
    _redis_listener_started = True
    asyncio.create_task(repeater_reply_buffer_redis_listen_loop())


async def prune_stale_repeater_reply_buffer_files() -> None:
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

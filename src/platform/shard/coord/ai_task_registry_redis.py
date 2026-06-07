"""分片 AI 任务登记：Redis SETEX（不可用时由 ai_task_registry 回退文件）。"""

from __future__ import annotations

import json
from typing import Any

_KEY_PREFIX = "pallas:ai_task:"


def ai_task_redis_key(task_id: str) -> str:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in task_id)
    return f"{_KEY_PREFIX}{safe}"


def write_ai_task_redis_sync(rec: dict[str, Any], *, ttl_sec: int) -> bool:
    from src.platform.coord.redis_claim import get_coord_redis_client
    from src.platform.coord.redis_settings import coord_redis_enabled

    if not coord_redis_enabled():
        return False
    client = get_coord_redis_client()
    if client is None:
        return False
    task_id = str(rec.get("task_id") or "").strip()
    if not task_id:
        return False
    try:
        body = json.dumps(rec, ensure_ascii=False, separators=(",", ":"))
        client.set(ai_task_redis_key(task_id), body, ex=max(60, int(ttl_sec)))
        return True
    except Exception:
        return False


def read_ai_task_redis_sync(task_id: str) -> dict[str, Any] | None:
    from src.platform.coord.redis_claim import get_coord_redis_client
    from src.platform.coord.redis_settings import coord_redis_enabled

    if not coord_redis_enabled():
        return None
    client = get_coord_redis_client()
    if client is None:
        return None
    try:
        raw = client.get(ai_task_redis_key(task_id))
    except Exception:
        return None
    if raw is None:
        return None
    try:
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        data = json.loads(str(raw))
    except (TypeError, ValueError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def remove_ai_task_redis_sync(task_id: str) -> None:
    from src.platform.coord.redis_claim import get_coord_redis_client
    from src.platform.coord.redis_settings import coord_redis_enabled

    if not coord_redis_enabled():
        return
    client = get_coord_redis_client()
    if client is None:
        return
    try:
        client.delete(ai_task_redis_key(task_id))
    except Exception:
        return

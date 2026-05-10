"""定时清理 message 中过期的 is_dream 梦库记录。"""

from __future__ import annotations

import re
import time

from nonebot import logger
from nonebot_plugin_apscheduler import scheduler

from src.common.db import get_db_backend

from .config import plugin_config
from .history_bottle import DREAM_KEY_PREFIX


async def delete_expired_dream_messages(*, retention_days: int) -> int:
    backend = get_db_backend()
    now = int(time.time())
    cutoff = now - max(7, int(retention_days)) * 86400
    if backend == "mongodb":
        return await _mongo_delete_expired(cutoff)
    if backend == "postgresql":
        return await _pg_delete_expired(cutoff)
    return 0


async def _mongo_delete_expired(cutoff: int) -> int:
    from src.common.db.modules import Message

    coll = Message.get_pymongo_collection()
    key_pat = f"^{re.escape(DREAM_KEY_PREFIX)}"
    q = {"keywords": {"$regex": key_pat}, "time": {"$lt": cutoff}}
    try:
        r = await coll.delete_many(q)
        return int(r.deleted_count)
    except Exception as e:
        logger.warning("dream library_cleanup mongo delete_many failed: {}", e)
        return 0


async def _pg_delete_expired(cutoff: int) -> int:
    from sqlalchemy import delete

    from src.common.db.repository_pg import MessageRow, get_session

    try:
        async with get_session() as session:
            stmt = delete(MessageRow).where(
                MessageRow.keywords.startswith(DREAM_KEY_PREFIX),
                MessageRow.time < cutoff,
            )
            r = await session.execute(stmt)
            await session.commit()
            return int(r.rowcount or 0)
    except Exception as e:
        logger.warning("dream library_cleanup pg delete failed: {}", e)
        return 0


@scheduler.scheduled_job(
    "cron",
    hour=plugin_config.dream_library_cleanup_cron_hour,
    minute=plugin_config.dream_library_cleanup_cron_minute,
)
async def dream_library_cleanup_job() -> None:
    n = await delete_expired_dream_messages(retention_days=plugin_config.dream_message_retention_days)
    if n:
        logger.info("dream library_cleanup removed {} expired is_dream row(s)", n)

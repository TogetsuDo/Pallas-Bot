from __future__ import annotations

import re

from nonebot import logger

from src.common.foundation.db import get_db_backend

from .dedupe_keys import dream_text_dedupe_key
from .history_bottle import DREAM_KEY_PREFIX, dream_history_bot_ids

_STRIP_CQ_IMG_URL = re.compile(r",\s*url=[^,\]]*")
_AFTER_AT_PREFIX = re.compile(r"^@\S+\s*[：:]\s*(.+)$", re.DOTALL)


def strip_cq_image_urls(raw: str) -> str:
    return _STRIP_CQ_IMG_URL.sub("", raw or "")


def dream_ban_plain_variants(plain: str) -> set[str]:
    s = (plain or "").strip()
    out: set[str] = set()
    if not s:
        return out
    out.add(s)
    dk = dream_text_dedupe_key(s)
    if dk:
        out.add(dk)
    m = _AFTER_AT_PREFIX.match(s)
    if m:
        inner = m.group(1).strip()
        if inner:
            out.add(inner)
            ik = dream_text_dedupe_key(inner)
            if ik:
                out.add(ik)
    for p in list(out):
        if len(p) > 4000:
            out.add(p[:4000])
    return {x for x in out if x}


async def delete_dream_messages_from_ban_reply(*, bot_id: int, reply_cq_raw: str, reply_plain: str) -> int:
    raw_norm = strip_cq_image_urls(reply_cq_raw or "")
    plains = dream_ban_plain_variants(reply_plain)
    bot_ids = dream_history_bot_ids(bot_id)
    backend = get_db_backend()
    if backend == "mongodb":
        return await _mongo_delete(bot_ids, raw_norm, plains)
    if backend == "postgresql":
        return await _pg_delete(bot_ids, raw_norm, plains)
    return 0


async def _mongo_delete(bot_ids: list[int], raw_norm: str, plains: set[str]) -> int:
    from src.common.foundation.db.modules import Message

    coll = Message.get_pymongo_collection()
    key_pat = f"^{re.escape(DREAM_KEY_PREFIX)}"
    q: dict = {"bot_id": {"$in": bot_ids}, "keywords": {"$regex": key_pat}}
    ors: list[dict] = []
    if plains:
        ors.append({"plain_text": {"$in": list(plains)}})
    if raw_norm.strip():
        ors.append({"raw_message": raw_norm})
    if not ors:
        return 0
    q["$or"] = ors
    try:
        r = await coll.delete_many(q)
        return int(r.deleted_count)
    except Exception as e:
        logger.debug(f"bot [{bot_ids[0]}] dream ban cleanup mongo delete_many failed: {e}")
        return 0


async def _pg_delete(bot_ids: list[int], raw_norm: str, plains: set[str]) -> int:
    from sqlalchemy import delete, or_

    from src.common.foundation.db.repository_pg import MessageRow, get_session

    if not plains and not (raw_norm or "").strip():
        return 0
    conds = []
    if plains:
        conds.append(MessageRow.plain_text.in_(list(plains)))
    if (raw_norm or "").strip():
        conds.append(MessageRow.raw_message == raw_norm)
    if not conds:
        return 0
    try:
        async with get_session() as session:
            stmt = delete(MessageRow).where(
                MessageRow.bot_id.in_(bot_ids),
                MessageRow.keywords.startswith(DREAM_KEY_PREFIX),
                or_(*conds),
            )
            r = await session.execute(stmt)
            await session.commit()
            return int(r.rowcount or 0)
    except Exception as e:
        logger.debug(f"bot [{bot_ids[0]}] dream ban cleanup pg delete failed: {e}")
        return 0

"""Learner 上下文：内存近期链不足时从 DB 补齐。"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.foundation.db import Message as MessageModel

    from .model import ChatData

_GROUP_TAIL_LIMIT = 8


async def group_messages_before(chat_data: ChatData) -> list[MessageModel]:
    from .message_store import MessageStore, message_repo

    group_id = int(chat_data.group_id)
    before_time = int(chat_data.time)
    mem = [m for m in MessageStore._message_dict.get(group_id, []) if int(m.time) < before_time]
    if mem:
        return mem[-_GROUP_TAIL_LIMIT:]
    try:
        rows = await message_repo.find_recent_in_group(
            group_id,
            before_time=before_time,
            limit=_GROUP_TAIL_LIMIT,
        )
    except Exception:
        return []
    return list(rows)


async def user_message_before_in_group(chat_data: ChatData, group_msgs: list[MessageModel]) -> MessageModel | None:
    user_id = int(chat_data.user_id)
    before_time = int(chat_data.time)
    for msg in group_msgs[:-3:-1]:
        if int(msg.user_id) == user_id:
            return msg
    from .message_store import message_repo

    try:
        rows = await message_repo.find_recent_in_group(
            int(chat_data.group_id),
            before_time=before_time,
            user_id=user_id,
            limit=1,
        )
    except Exception:
        return None
    return rows[-1] if rows else None

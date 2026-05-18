from __future__ import annotations

import asyncio
import hashlib
import re
from collections import deque

_GROUP_EVENT_DEDUP_MAX = 4000
_group_event_dedup_lock = asyncio.Lock()
_group_event_sigs: deque[tuple[int, int, str, int]] = deque()
_group_event_sig_set: set[tuple[int, int, str, int]] = set()


def normalize_group_raw_message(raw_message: str) -> str:
    # 与 ChatData / learn 侧一致，避免图片子类型差异导致去重失败
    return re.sub(r"\.image,.+?\]", ".image]", raw_message)


def cross_bot_group_message_key(
    group_id: int,
    user_id: int,
    raw_message: str,
    message_time: int,
) -> int:
    """各 Bot 连接的 message_id 不同；同一条物理消息用此键做抢占/去重。"""
    norm = normalize_group_raw_message(raw_message)
    payload = f"{group_id}:{user_id}:{message_time}:{norm}"
    return int(hashlib.sha256(payload.encode("utf-8")).hexdigest()[:15], 16)


async def should_skip_duplicate_group_event(
    group_id: int,
    user_id: int,
    norm_raw: str,
    message_time: int,
) -> bool:
    sig = (group_id, user_id, norm_raw, message_time)
    async with _group_event_dedup_lock:
        if sig in _group_event_sig_set:
            return True
        while len(_group_event_sigs) >= _GROUP_EVENT_DEDUP_MAX:
            old = _group_event_sigs.popleft()
            _group_event_sig_set.discard(old)
        _group_event_sigs.append(sig)
        _group_event_sig_set.add(sig)
        return False

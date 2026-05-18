"""多 Bot 同群：协议可能对同一条群消息向每个连接各上报一次，用内容签名去重/抢占。"""

from __future__ import annotations

import asyncio
import hashlib
import re
import time
from collections import deque

from src.common.multi_bot_message_claim import try_claim_message

_GROUP_EVENT_DEDUP_MAX = 4000
_group_event_dedup_lock = asyncio.Lock()
_group_event_sigs: deque[tuple[int, int, str, int]] = deque()
_group_event_sig_set: set[tuple[int, int, str, int]] = set()

_CROSS_BOT_CLAIM_MAX = 4000
_cross_bot_claim_lock = asyncio.Lock()
_cross_bot_claim_owners: dict[tuple[str, tuple[int, int, str, int]], int] = {}


def normalize_group_raw_message(raw_message: str) -> str:
    # 与 ChatData / learn 侧一致，避免图片子类型差异导致去重失败
    return re.sub(r"\.image,.+?\]", ".image]", raw_message)


def normalize_group_plaintext(plaintext: str) -> str:
    return re.sub(r"\s+", " ", plaintext.strip())


def normalize_message_time(message_time: int) -> int:
    t = int(message_time)
    if t > 10_000_000_000:
        return t // 1000
    return t


def cross_bot_message_signature(
    group_id: int,
    user_id: int,
    message_body: str,
    message_time: int,
    *,
    use_plaintext: bool = True,
) -> tuple[int, int, str, int]:
    body = normalize_group_plaintext(message_body) if use_plaintext else normalize_group_raw_message(message_body)
    return (group_id, user_id, body, normalize_message_time(message_time))


def cross_bot_group_message_key(
    group_id: int,
    user_id: int,
    message_body: str,
    message_time: int,
    *,
    use_plaintext: bool = True,
) -> int:
    """各 Bot 连接的 message_id 不同；同一条物理消息用此键做文件抢占。"""
    sig = cross_bot_message_signature(
        group_id,
        user_id,
        message_body,
        message_time,
        use_plaintext=use_plaintext,
    )
    payload = f"{sig[0]}:{sig[1]}:{sig[3]}:{sig[2]}"
    return int(hashlib.sha256(payload.encode("utf-8")).hexdigest()[:15], 16)


def _prune_cross_bot_claims() -> None:
    if len(_cross_bot_claim_owners) <= _CROSS_BOT_CLAIM_MAX:
        return
    for key in list(_cross_bot_claim_owners.keys())[: _CROSS_BOT_CLAIM_MAX // 2]:
        _cross_bot_claim_owners.pop(key, None)


async def try_claim_cross_bot_message_memory(
    plugin: str,
    group_id: int,
    user_id: int,
    message_body: str,
    message_time: int,
    bot_id: int,
    *,
    use_plaintext: bool = True,
) -> bool:
    sig = cross_bot_message_signature(
        group_id,
        user_id,
        message_body,
        message_time,
        use_plaintext=use_plaintext,
    )
    key = (plugin, sig)
    async with _cross_bot_claim_lock:
        owner = _cross_bot_claim_owners.get(key)
        if owner is None:
            _cross_bot_claim_owners[key] = bot_id
            _prune_cross_bot_claims()
            return True
        return owner == bot_id


async def try_claim_cross_bot_message(
    plugin: str,
    group_id: int,
    user_id: int,
    message_body: str,
    message_time: int,
    bot_id: int,
    *,
    use_plaintext: bool = True,
) -> bool:
    """同进程内存抢占 + 跨进程文件抢占（共享 data/ 时生效）。"""
    if not await try_claim_cross_bot_message_memory(
        plugin,
        group_id,
        user_id,
        message_body,
        message_time,
        bot_id,
        use_plaintext=use_plaintext,
    ):
        return False
    claim_key = cross_bot_group_message_key(
        group_id,
        user_id,
        message_body,
        message_time,
        use_plaintext=use_plaintext,
    )
    return await try_claim_message(plugin, group_id, claim_key, bot_id)


async def should_skip_duplicate_group_event(
    group_id: int,
    user_id: int,
    norm_raw: str,
    message_time: int,
) -> bool:
    sig = (group_id, user_id, norm_raw, normalize_message_time(message_time))
    async with _group_event_dedup_lock:
        if sig in _group_event_sig_set:
            return True
        while len(_group_event_sigs) >= _GROUP_EVENT_DEDUP_MAX:
            old = _group_event_sigs.popleft()
            _group_event_sig_set.discard(old)
        _group_event_sigs.append(sig)
        _group_event_sig_set.add(sig)
        return False


_DRAW_CHEER_GATE_LOCK = asyncio.Lock()
_draw_cheer_gate_until: dict[int, tuple[int, float]] = {}


async def try_begin_group_draw_cheer(group_id: int, bot_id: int, *, gate_sec: float) -> bool:
    """同群「欢呼吧」占位：在锁内判定，避免多 Bot 同时通过冷却检查。"""
    ttl = max(1.0, float(gate_sec))
    now = time.time()
    async with _DRAW_CHEER_GATE_LOCK:
        rec = _draw_cheer_gate_until.get(group_id)
        if rec is not None:
            owner, until = rec
            if now < until:
                return owner == bot_id
        _draw_cheer_gate_until[group_id] = (bot_id, now + ttl)
        if len(_draw_cheer_gate_until) > 2000:
            expired = [g for g, (_, u) in _draw_cheer_gate_until.items() if u <= now]
            for g in expired:
                _draw_cheer_gate_until.pop(g, None)
        return True

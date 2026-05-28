"""ingress / repeater 共用的联邦群消息抢占入口。"""

from __future__ import annotations

import asyncio
import os
import time
from typing import TYPE_CHECKING

from src.features.community_stats.store import load_or_create_deployment_id

if TYPE_CHECKING:
    from nonebot.adapters.onebot.v11 import GroupMessageEvent
from src.platform.federate.config import federate_ingress_active
from src.platform.federate.dedup import try_claim_cross_federate_message
from src.platform.multi_bot.dedup import cross_bot_message_signature

FEDERATE_INGRESS_CLAIM_PLUGIN = "federate_ingress"
_WIN_CACHE_TTL_SEC = float(os.getenv("PALLAS_FEDERATE_WIN_CACHE_SEC", "8"))
_WIN_CACHE_MAX = 20_000
_win_cache: dict[tuple[str, tuple[int, int, str] | tuple[int, int, str, int], str], float] = {}
_win_lock = asyncio.Lock()


def reset_federate_ingress_win_cache_for_tests() -> None:
    _win_cache.clear()


def federate_ingress_cached_win(
    event: GroupMessageEvent,
    *,
    plugin: str = FEDERATE_INGRESS_CLAIM_PLUGIN,
    include_message_time: bool = True,
) -> bool:
    """本进程是否已缓存赢得联邦 ingress（供 repeater 跳过二次 Redis）。"""
    if not federate_ingress_active():
        return True
    plain = (event.get_plaintext() or "").strip()
    body = plain or event.raw_message
    deployment_id = load_or_create_deployment_id().strip().lower()
    if not deployment_id:
        return False
    sig = cross_bot_message_signature(
        int(event.group_id),
        int(event.user_id),
        body,
        event.time,
        use_plaintext=True,
        include_message_time=include_message_time,
    )
    cache_key = (plugin, sig, deployment_id)
    now = time.monotonic()
    exp = _win_cache.get(cache_key)
    return exp is not None and now < exp


async def claim_federate_group_message_ingress(
    event: GroupMessageEvent,
    *,
    plugin: str = FEDERATE_INGRESS_CLAIM_PLUGIN,
    include_message_time: bool = True,
) -> bool:
    """未启用联邦 ingress 或本 deployment 抢占成功时返回 True。"""
    if not federate_ingress_active():
        return True
    plain = (event.get_plaintext() or "").strip()
    body = plain or event.raw_message
    deployment_id = load_or_create_deployment_id().strip().lower()
    if not deployment_id:
        return False
    sig = cross_bot_message_signature(
        int(event.group_id),
        int(event.user_id),
        body,
        event.time,
        use_plaintext=True,
        include_message_time=include_message_time,
    )
    cache_key = (plugin, sig, deployment_id)
    now = time.monotonic()
    async with _win_lock:
        exp = _win_cache.get(cache_key)
        if exp is not None and now < exp:
            return True
        if len(_win_cache) > _WIN_CACHE_MAX:
            stale = [k for k, e in _win_cache.items() if now >= e]
            for k in stale:
                _win_cache.pop(k, None)
            if len(_win_cache) > _WIN_CACHE_MAX:
                _win_cache.clear()

    won = await try_claim_cross_federate_message(
        plugin,
        int(event.group_id),
        int(event.user_id),
        body,
        event.time,
        deployment_id,
        use_plaintext=True,
        include_message_time=include_message_time,
    )
    if won:
        expire_at = time.monotonic() + _WIN_CACHE_TTL_SEC
        async with _win_lock:
            _win_cache[cache_key] = expire_at
    return won

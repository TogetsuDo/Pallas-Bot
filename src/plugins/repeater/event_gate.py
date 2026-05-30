from __future__ import annotations

import asyncio
from collections import defaultdict, deque
from types import SimpleNamespace
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nonebot.adapters.onebot.v11 import GroupMessageEvent

from src.platform.federate.ingress import (
    claim_federate_group_message_ingress,
    federate_ingress_cached_win,
)
from src.platform.ingress.fanout_bypass import ingress_fanout_bypasses_claim
from src.platform.ingress.plugin_command_plaintext import is_plugin_command_plaintext
from src.platform.multi_bot.dedup import (
    normalize_group_raw_message,
    should_skip_duplicate_group_event,
    try_claim_cross_bot_message,
    try_claim_group_message_once,
)
from src.platform.shard.registry.config import is_sharding_active

from .fanout_reply import repeater_fanout_enabled
from .shard_opt import repeater_worker_handles_message

message_id_lock = asyncio.Lock()
message_id_dict = defaultdict(lambda: deque(maxlen=100))


async def remember_group_message_id(group_id: int, message_id: int) -> bool:
    """同群同 message_id 在本进程内只放行一次。"""
    async with message_id_lock:
        bucket = message_id_dict[group_id]
        if message_id in bucket:
            return False
        bucket.append(message_id)
        return True


async def build_repeater_event_context(bot_id: int, event: GroupMessageEvent):
    if not repeater_worker_handles_message(bot_id):
        return None

    plain_body = event.get_plaintext()
    if plain_body and is_plugin_command_plaintext(plain_body):
        return None
    if ingress_fanout_bypasses_claim(plain_body):
        return None

    if not await remember_group_message_id(event.group_id, event.message_id):
        return None

    norm_raw = normalize_group_raw_message(event.raw_message)
    if await should_skip_duplicate_group_event(
        event.group_id,
        event.user_id,
        norm_raw,
        event.time,
    ):
        return None

    if not federate_ingress_cached_win(event, include_message_time=True):
        if not await claim_federate_group_message_ingress(event, include_message_time=True):
            return None

    sharding_active = is_sharding_active()
    if not sharding_active:
        if not await try_claim_group_message_once(
            "repeater_ingress",
            event.group_id,
            event.user_id,
            plain_body,
            event.time,
        ):
            return None
    elif not repeater_fanout_enabled():
        if not await try_claim_cross_bot_message(
            "repeater_reply",
            event.group_id,
            event.user_id,
            plain_body,
            event.time,
            bot_id,
            use_plaintext=True,
        ):
            return None

    return SimpleNamespace(
        plain_body=plain_body,
        norm_raw=norm_raw,
        sharding_active=sharding_active,
    )

"""ingress / repeater 共用的联邦群消息抢占入口。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.common.community_stats.store import load_or_create_deployment_id

if TYPE_CHECKING:
    from nonebot.adapters.onebot.v11 import GroupMessageEvent
from src.common.federate.config import federate_ingress_active
from src.common.federate.dedup import try_claim_cross_federate_message

FEDERATE_INGRESS_CLAIM_PLUGIN = "federate_ingress"


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
    return await try_claim_cross_federate_message(
        plugin,
        int(event.group_id),
        int(event.user_id),
        body,
        event.time,
        load_or_create_deployment_id(),
        use_plaintext=True,
        include_message_time=include_message_time,
    )

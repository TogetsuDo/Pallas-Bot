from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message
from nonebot.exception import IgnoredException

from src.platform.shard.registry import config as shard_cfg


@pytest.mark.asyncio
async def test_unified_ingress_once_discards_second_bot(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(shard_cfg, "is_sharding_active", lambda: False)
    monkeypatch.setattr("src.plugins.ingress_gate.ingress_gate_active", lambda: True)
    monkeypatch.setattr("src.plugins.ingress_gate.fleet_bot_ids_contains", lambda _uid: False)
    monkeypatch.setattr(
        "src.plugins.ingress_gate.claim_federate_group_message_ingress",
        AsyncMock(return_value=True),
    )
    monkeypatch.setattr("src.plugins.ingress_gate.ingress_fanout_bypasses_claim", lambda _plain: False)
    from src.plugins.ingress_gate import ingress_group_message_gate

    class FakeBot:
        def __init__(self, self_id: int):
            self.self_id = str(self_id)

    event = GroupMessageEvent.model_construct(
        time=100,
        self_id=111,
        post_type="message",
        message_type="group",
        sub_type="normal",
        user_id=999,
        group_id=12345,
        message_id=1,
        message=Message("测试 ingress"),
        raw_message="测试 ingress",
    )

    bot_a = FakeBot(111)
    bot_b = FakeBot(222)

    await ingress_group_message_gate(bot_a, event)
    with pytest.raises(IgnoredException):
        await ingress_group_message_gate(bot_b, event)


@pytest.mark.asyncio
async def test_unified_ingress_fanout_allows_all_bots(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(shard_cfg, "is_sharding_active", lambda: False)
    monkeypatch.setattr("src.plugins.ingress_gate.ingress_gate_active", lambda: True)
    monkeypatch.setattr("src.plugins.ingress_gate.fleet_bot_ids_contains", lambda _uid: False)
    monkeypatch.setattr(
        "src.plugins.ingress_gate.claim_federate_group_message_ingress",
        AsyncMock(return_value=True),
    )
    monkeypatch.setattr("src.plugins.ingress_gate.ingress_fanout_bypasses_claim", lambda _plain: True)
    from src.plugins.ingress_gate import ingress_group_message_gate

    class FakeBot:
        def __init__(self, self_id: int):
            self.self_id = str(self_id)

    event = GroupMessageEvent.model_construct(
        time=100,
        self_id=111,
        post_type="message",
        message_type="group",
        sub_type="normal",
        user_id=999,
        group_id=12345,
        message_id=1,
        message=Message("牛牛喝酒"),
        raw_message="牛牛喝酒",
    )

    await ingress_group_message_gate(FakeBot(111), event)
    await ingress_group_message_gate(FakeBot(222), event)

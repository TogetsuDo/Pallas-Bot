from __future__ import annotations

import asyncio

from src.common.shard.coord import bot_action as ba_mod
from src.common.shard import presence as presence_mod
from src.plugins.repeater import fanout_reply as fanout_mod


def test_bot_has_cluster_connection_local(monkeypatch):
    monkeypatch.setattr(presence_mod, "bot_has_local_connection", lambda qq: qq == 100)
    monkeypatch.setattr(presence_mod, "is_sharding_active", lambda: True)
    monkeypatch.setattr(presence_mod, "get_cluster_online_bot_ids", lambda: frozenset({200}))
    assert presence_mod.bot_has_cluster_connection(100) is True
    assert presence_mod.bot_has_cluster_connection(200) is True
    assert presence_mod.bot_has_cluster_connection(300) is False


def test_invoke_bot_action_skips_offline_remote(monkeypatch):
    monkeypatch.setattr(ba_mod, "is_sharding_active", lambda: True)
    monkeypatch.setattr(presence_mod, "bot_has_local_connection", lambda qq: False)
    monkeypatch.setattr(presence_mod, "bot_has_cluster_connection", lambda qq: False)

    async def run() -> None:
        ok, result = await ba_mod.invoke_bot_action("send_group_msg", 2868075548, {"group_id": 1})
        assert ok is False
        assert result is None

    asyncio.run(run())


def test_list_fanout_bot_ids_filters_offline(monkeypatch):
    async def fake_list(group_id: int) -> list[int]:
        return [100, 200, 300]

    monkeypatch.setattr(fanout_mod, "is_sharding_active", lambda: True)
    monkeypatch.setattr(presence_mod, "get_cluster_online_bot_ids", lambda: frozenset({100, 200}))
    monkeypatch.setattr(
        "src.plugins.duel.duel_bots.list_group_online_bot_ids",
        fake_list,
    )
    async def always_true(bid: int, gid: int) -> bool:
        return True

    monkeypatch.setattr(fanout_mod, "bot_may_repeater_reply", always_true)

    async def run() -> None:
        ids = await fanout_mod.list_fanout_bot_ids(1)
        assert ids == [100, 200]

    asyncio.run(run())

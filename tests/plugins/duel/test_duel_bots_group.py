from __future__ import annotations

import pytest

from src.plugins.duel import duel_bots as mod


@pytest.mark.asyncio
async def test_list_local_fleet_bots_does_not_return_full_scope_on_probe_miss(monkeypatch) -> None:
    scope = frozenset({923722427, 3887247010, 2995241261})

    class Caller:
        async def get_group_member_list(self, **kwargs):
            return []

        async def get_group_member_info(self, group_id: int, user_id: int, **kwargs):
            if user_id == 923722427:
                return {"user_id": user_id}
            raise Exception("not in group")

    async def fake_probe(_caller, _gid, catalog):
        return []

    monkeypatch.setattr(mod, "get_bots", lambda: {str(q): object() for q in scope})
    monkeypatch.setattr(
        "src.common.platform.shard.presence.pick_local_query_bot",
        lambda: Caller(),
    )
    monkeypatch.setattr(
        "src.common.platform.multi_bot.fleet.get_catalog_bot_ids",
        lambda: set(scope),
    )
    monkeypatch.setattr(mod, "probe_fleet_bots_in_group", fake_probe)

    ids = await mod.list_local_fleet_bots_in_group(626266902)
    assert ids == [923722427]

from __future__ import annotations

import pytest
from packages.duel import duel_bots as mod


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
        "pallas.core.platform.shard.presence.pick_local_query_bot",
        lambda: Caller(),
    )
    monkeypatch.setattr(
        "pallas.core.platform.multi_bot.fleet.get_catalog_bot_ids",
        lambda: set(scope),
    )
    monkeypatch.setattr(mod, "probe_fleet_bots_in_group", fake_probe)

    ids = await mod.list_local_fleet_bots_in_group(626266902)
    assert ids == [923722427]


def test_parse_duel_at_qqs_skips_raw_regex_when_no_at(monkeypatch) -> None:
    class _Pattern:
        def finditer(self, _raw):
            raise AssertionError("raw regex should be skipped without at marker")

    monkeypatch.setattr(mod, "_AT_CQ_RE", _Pattern())

    event = type("E", (), {"message": (), "raw_message": "普通文本"})()
    assert mod.parse_duel_at_qqs(event) == []


def test_raw_message_has_at_fast_returns_false_without_at(monkeypatch) -> None:
    class _Pattern:
        def search(self, _raw):
            raise AssertionError("raw regex should be skipped without at marker")

    monkeypatch.setattr(mod, "_AT_CQ_RE", _Pattern())

    event = type("E", (), {"raw_message": "普通文本"})()
    assert mod.raw_message_has_at(event) is False

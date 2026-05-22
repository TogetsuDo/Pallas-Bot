from __future__ import annotations

import pytest

from src.plugins.repeater.shard_opt import (
    repeater_scheduler_runs_on_worker,
    repeater_worker_handles_message,
)


@pytest.mark.asyncio
async def test_repeater_fanout_enabled_for_group_requires_two_bots(monkeypatch):
    from src.plugins.repeater import fanout_reply

    monkeypatch.setattr(fanout_reply, "is_sharding_active", lambda: True)
    monkeypatch.setattr(
        fanout_reply,
        "get_repeater_config",
        lambda: type("C", (), {"fanout_enabled": True})(),
    )

    async def one(_gid: int) -> int:
        return 1

    monkeypatch.setattr(fanout_reply, "count_fanout_capable_bots", one)
    assert await fanout_reply.repeater_fanout_enabled_for_group(1) is False

    async def two(_gid: int) -> int:
        return 2

    monkeypatch.setattr(fanout_reply, "count_fanout_capable_bots", two)
    assert await fanout_reply.repeater_fanout_enabled_for_group(1) is True


def test_repeater_worker_handles_unified(monkeypatch):
    monkeypatch.setattr(
        "src.common.shard.registry.config.is_sharding_active",
        lambda: False,
    )
    assert repeater_worker_handles_message(999) is True


def test_repeater_worker_handles_only_representative(monkeypatch):
    monkeypatch.setattr(
        "src.common.shard.registry.config.is_sharding_active",
        lambda: True,
    )
    monkeypatch.setattr(
        "src.common.shard.local_representative.is_local_worker_representative",
        lambda bid: bid == 100,
    )
    assert repeater_worker_handles_message(100) is True
    assert repeater_worker_handles_message(200) is False


def test_scheduler_skips_worker_without_rep(monkeypatch):
    monkeypatch.setattr(
        "src.common.shard.registry.config.is_sharding_active",
        lambda: True,
    )
    monkeypatch.setattr(
        "src.common.shard.local_representative.local_worker_representative_bot_id",
        lambda: None,
    )
    assert repeater_scheduler_runs_on_worker() is False

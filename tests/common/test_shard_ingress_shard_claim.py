from __future__ import annotations

import pytest

from src.common.multi_bot.dedup import try_claim_cross_shard_message


@pytest.mark.asyncio
async def test_cross_shard_claim_one_shard_wins() -> None:
    plugin = "test_ingress_shard"
    gid, uid, body, t = 1, 2, "hello", 100
    assert await try_claim_cross_shard_message(plugin, gid, uid, body, t, shard_id=0)
    assert await try_claim_cross_shard_message(plugin, gid, uid, body, t, shard_id=0)
    assert not await try_claim_cross_shard_message(plugin, gid, uid, body, t, shard_id=1)

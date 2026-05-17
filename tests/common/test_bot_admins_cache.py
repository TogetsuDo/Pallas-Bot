from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_get_bot_admins_gate_cache(beanie_fixture, monkeypatch):
    from src.common.config import get_bot_admins
    from src.common.config import bot_admins_cache as cache
    from src.common.db import make_bot_config_repository

    await cache.reset_bot_admins_cache()
    repo = make_bot_config_repository()
    await repo.upsert_field(88001, "admins", [111, 222])

    calls: list[int] = []
    real_load = cache._load_admins_db

    async def counting_load(bot_id: int):
        calls.append(bot_id)
        return await real_load(bot_id)

    monkeypatch.setattr(cache, "_load_admins_db", counting_load)

    a = await get_bot_admins(88001)
    b = await get_bot_admins(88001)
    assert a == [111, 222]
    assert b == [111, 222]
    assert len(calls) == 1

    await cache.invalidate_bot_admins_cache(88001)
    c = await get_bot_admins(88001)
    assert c == [111, 222]
    assert len(calls) == 2

    await cache.reset_bot_admins_cache()

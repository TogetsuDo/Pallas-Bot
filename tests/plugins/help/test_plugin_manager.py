"""
Tests for src/plugins/help/plugin_manager.py after refactor to Repository.

覆盖 BotConfig/GroupConfig 的读写是否全部走 repo，不再直调 Beanie Document。
"""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_is_plugin_disabled_creates_bot_config_on_first_access(beanie_fixture):
    from src.plugins.help import plugin_manager

    # 首次查询时 bot config 不存在，函数应 auto-create
    result = await plugin_manager.is_plugin_disabled("foo", bot_id=12345)
    assert result is False

    bot_cfg = await plugin_manager.bot_config_repo.get(12345, ignore_cache=True)
    assert bot_cfg is not None
    assert bot_cfg.disabled_plugins == []


@pytest.mark.asyncio
async def test_is_plugin_disabled_globally_disabled(beanie_fixture):
    from src.plugins.help import plugin_manager

    await plugin_manager.bot_config_repo.upsert_field(99, "disabled_plugins", ["bad_plugin"])
    assert await plugin_manager.is_plugin_disabled("bad_plugin", bot_id=99) is True
    assert await plugin_manager.is_plugin_disabled("good_plugin", bot_id=99) is False


@pytest.mark.asyncio
async def test_is_plugin_disabled_group_level(beanie_fixture):
    from src.plugins.help import plugin_manager

    await plugin_manager.group_config_repo.upsert_field(101, "disabled_plugins", ["chat"])
    assert await plugin_manager.is_plugin_disabled("chat", group_id=101, bot_id=1) is True
    assert await plugin_manager.is_plugin_disabled("other", group_id=101, bot_id=1) is False


@pytest.mark.asyncio
async def test_is_plugin_globally_disabled(beanie_fixture):
    from src.plugins.help import plugin_manager

    assert await plugin_manager.is_plugin_globally_disabled("x", bot_id=500) is False
    await plugin_manager.bot_config_repo.upsert_field(500, "disabled_plugins", ["x"])
    assert await plugin_manager.is_plugin_globally_disabled("x", bot_id=500) is True


@pytest.mark.asyncio
async def test_get_bot_config_creates_if_missing(beanie_fixture):
    from src.plugins.help import plugin_manager

    cfg, created = await plugin_manager.get_bot_config(777)
    assert created is True
    assert cfg.account == 777

    cfg2, created2 = await plugin_manager.get_bot_config(777)
    assert created2 is False
    assert cfg2.account == 777


@pytest.mark.asyncio
async def test_get_group_config_creates_if_missing(beanie_fixture):
    from src.plugins.help import plugin_manager

    cfg, created = await plugin_manager.get_group_config(8888)
    assert created is True
    assert cfg.group_id == 8888


@pytest.mark.asyncio
async def test_update_bot_config_roundtrip(beanie_fixture, tmp_path, monkeypatch):
    from src.plugins.help import plugin_manager

    # 避免真实改 help 缓存目录
    monkeypatch.setattr(plugin_manager, "clear_help_cache", lambda *a, **k: None)

    await plugin_manager.get_bot_config(123)
    updated = await plugin_manager.update_bot_config(123, ["p1", "p2"])
    assert updated.disabled_plugins == ["p1", "p2"]

    # 再次验证读 path
    cfg = await plugin_manager.bot_config_repo.get(123, ignore_cache=True)
    assert cfg is not None
    assert cfg.disabled_plugins == ["p1", "p2"]


@pytest.mark.asyncio
async def test_update_group_config_roundtrip(beanie_fixture, monkeypatch):
    from src.plugins.help import plugin_manager

    monkeypatch.setattr(plugin_manager, "clear_help_cache", lambda *a, **k: None)

    await plugin_manager.get_group_config(321)
    updated = await plugin_manager.update_group_config(321, ["p3"])
    assert updated.disabled_plugins == ["p3"]


@pytest.mark.asyncio
async def test_collect_disabled_plugin_names_merges_bot_and_group(beanie_fixture):
    from src.plugins.help import plugin_manager

    await plugin_manager.bot_config_repo.upsert_field(10, "disabled_plugins", ["g"])
    await plugin_manager.group_config_repo.upsert_field(2000, "disabled_plugins", ["c"])
    merged = await plugin_manager.collect_disabled_plugin_names(10, 2000, ignore_cache=True)
    assert merged == frozenset({"g", "c"})
    for name in ("g", "c", "other"):
        exp = await plugin_manager.is_plugin_disabled(name, group_id=2000, bot_id=10, ignore_cache=True)
        assert (name in merged) is exp


@pytest.mark.asyncio
async def test_collect_disabled_plugin_names_bot_only(beanie_fixture):
    from src.plugins.help import plugin_manager

    merged = await plugin_manager.collect_disabled_plugin_names(30001, None, ignore_cache=True)
    assert merged == frozenset()
    assert await plugin_manager.is_plugin_disabled("x", group_id=None, bot_id=30001, ignore_cache=True) is False


@pytest.mark.asyncio
async def test_collect_disabled_plugin_names_gate_cache(beanie_fixture, monkeypatch):
    from src.plugins.help import plugin_manager

    await plugin_manager.reset_disabled_plugin_gate_cache()
    bot_calls: list[int] = []
    group_calls: list[int] = []
    real_load_bot = plugin_manager.load_disabled_bot_names_from_db
    real_load_group = plugin_manager.load_disabled_group_names_from_db

    async def counting_load_bot(bot_id, *, ignore_cache=False):
        bot_calls.append(int(bot_id))
        return await real_load_bot(bot_id, ignore_cache=ignore_cache)

    async def counting_load_group(group_id, *, ignore_cache=False):
        group_calls.append(int(group_id))
        return await real_load_group(group_id, ignore_cache=ignore_cache)

    monkeypatch.setattr(plugin_manager, "load_disabled_bot_names_from_db", counting_load_bot)
    monkeypatch.setattr(plugin_manager, "load_disabled_group_names_from_db", counting_load_group)

    await plugin_manager.bot_config_repo.upsert_field(77, "disabled_plugins", ["a"])
    first = await plugin_manager.collect_disabled_plugin_names(77, 5001)
    second = await plugin_manager.collect_disabled_plugin_names(77, 5001)
    assert first == frozenset({"a"})
    assert second == frozenset({"a"})
    assert bot_calls == [77]
    assert group_calls == [5001]

    await plugin_manager.invalidate_disabled_plugin_gate_cache(bot_id=77)
    third = await plugin_manager.collect_disabled_plugin_names(77, 5001)
    assert third == frozenset({"a"})
    assert bot_calls == [77, 77]
    assert group_calls == [5001]

    await plugin_manager.reset_disabled_plugin_gate_cache()


@pytest.mark.asyncio
async def test_collect_disabled_plugin_names_reuses_bot_scope_across_groups(beanie_fixture, monkeypatch):
    from src.plugins.help import plugin_manager

    await plugin_manager.reset_disabled_plugin_gate_cache()
    await plugin_manager.bot_config_repo.upsert_field(901, "disabled_plugins", ["a"])

    calls: list[int] = []
    real_get = plugin_manager.bot_config_repo.get

    async def counting_get(bot_id, *, ignore_cache=False):
        calls.append(int(bot_id))
        return await real_get(bot_id, ignore_cache=ignore_cache)

    monkeypatch.setattr(plugin_manager.bot_config_repo, "get", counting_get)

    first = await plugin_manager.collect_disabled_plugin_names(901, 5001)
    second = await plugin_manager.collect_disabled_plugin_names(901, 5002)

    assert first == frozenset({"a"})
    assert second == frozenset({"a"})
    assert calls == [901]

    await plugin_manager.reset_disabled_plugin_gate_cache()


@pytest.mark.asyncio
async def test_collect_disabled_plugin_names_does_not_create_empty_bot_config(beanie_fixture):
    from src.plugins.help import plugin_manager

    await plugin_manager.reset_disabled_plugin_gate_cache()

    bot_id = 30002
    merged = await plugin_manager.collect_disabled_plugin_names(bot_id, None, ignore_cache=True)

    assert merged == frozenset()
    assert await plugin_manager.bot_config_repo.get(bot_id, ignore_cache=True) is None


@pytest.mark.asyncio
async def test_collect_disabled_plugin_names_short_circuits_when_pg_not_ready(monkeypatch):
    from src.plugins.help import plugin_manager

    await plugin_manager.reset_disabled_plugin_gate_cache()

    async def fail_load(bot_id, group_id, *, ignore_cache=False):  # noqa: ARG001
        raise AssertionError("should not load disabled plugin names when PG is not ready")

    monkeypatch.setattr(plugin_manager, "load_disabled_plugin_names_from_db", fail_load)
    monkeypatch.setattr("src.foundation.db.get_db_backend", lambda: "postgresql")
    monkeypatch.setattr("src.foundation.db.repository_pg.is_pg_initialized", lambda: False)

    merged = await plugin_manager.collect_disabled_plugin_names(77, 5001)
    assert merged == frozenset()

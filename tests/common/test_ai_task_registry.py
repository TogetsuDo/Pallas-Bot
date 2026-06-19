from __future__ import annotations

import time
from types import SimpleNamespace

import pytest
from nonebot.matcher import current_bot as nb_current_bot
from nonebot.matcher import current_event as nb_current_event

from pallas.core.foundation.config import TaskManager
from pallas.core.platform.shard.coord import ai_task_registry as mod


@pytest.fixture(autouse=True)
def clear_redis_caches():
    from pallas.core.platform.coord import redis_claim as rc
    from pallas.core.platform.coord import redis_settings as rs

    rs.clear_coord_redis_settings_cache()
    rc.clear_coord_redis_client_cache()
    yield
    rs.clear_coord_redis_settings_cache()
    rc.clear_coord_redis_client_cache()


def test_ai_task_registry_survives_long_queue_delay(fake_coord_redis, monkeypatch) -> None:
    monkeypatch.setattr(mod.shard_ctx, "sharding_active", lambda: True)
    monkeypatch.setattr(mod, "current_worker_port", lambda: 7973)
    monkeypatch.setattr(mod, "get_shard_registry_settings", lambda: SimpleNamespace(shard_id=3))

    start = 1000.0
    monkeypatch.setattr(mod.time, "time", lambda: start)
    mod.register_ai_task(
        "task-1",
        {
            "bot_id": "123456",
            "group_id": 42,
            "start_time": start,
        },
    )

    monkeypatch.setattr(mod.time, "time", lambda: start + 601.0)
    rec = mod.get_ai_task_record("task-1")

    assert rec is not None
    assert rec["worker_port"] == 7973


async def test_task_manager_keeps_ai_task_beyond_legacy_10min(monkeypatch) -> None:
    start = 1000.0
    TaskManager._tasks = {
        "task-1": {
            "bot_id": "123456",
            "group_id": 42,
            "start_time": start,
        }
    }
    monkeypatch.setattr("pallas.core.foundation.config.time.time", lambda: start + 601.0)
    monkeypatch.setattr("pallas.core.platform.shard.coord.ai_task_registry.ai_task_ttl_sec", lambda: 86400.0)

    await TaskManager.refresh()

    assert "task-1" in TaskManager._tasks


@pytest.mark.asyncio
async def test_task_manager_rekey_task_moves_local_and_shared_registry(monkeypatch) -> None:
    now = time.time()
    TaskManager._tasks = {
        "task-local": {
            "bot_id": "123456",
            "group_id": 42,
            "task_type": "sing",
            "start_time": now,
        }
    }

    registered: list[tuple[str, dict]] = []
    removed: list[str] = []

    def fake_register(task_id: str, task_status: dict) -> None:
        registered.append((task_id, dict(task_status)))

    def fake_remove(task_id: str) -> None:
        removed.append(task_id)

    monkeypatch.setattr("pallas.core.platform.shard.coord.ai_task_registry.register_ai_task", fake_register)
    monkeypatch.setattr("pallas.core.platform.shard.coord.ai_task_registry.remove_ai_task", fake_remove)

    await TaskManager.rekey_task("task-local", "task-remote")

    assert "task-local" not in TaskManager._tasks
    assert TaskManager._tasks["task-remote"]["task_type"] == "sing"
    assert removed == ["task-local"]
    assert registered == [
        (
            "task-remote",
            {
                "bot_id": "123456",
                "group_id": 42,
                "task_type": "sing",
                "start_time": now,
            },
        )
    ]


@pytest.mark.asyncio
async def test_task_manager_media_task_prefers_current_matcher_bot_binding(monkeypatch) -> None:
    TaskManager._tasks = {}
    registered: list[tuple[str, dict]] = []

    def fake_register(task_id: str, task_status: dict) -> None:
        registered.append((task_id, dict(task_status)))

    monkeypatch.setattr("pallas.core.platform.shard.coord.ai_task_registry.register_ai_task", fake_register)
    token_bot = nb_current_bot.set(SimpleNamespace(self_id="2927116873"))
    token_event = nb_current_event.set(SimpleNamespace(self_id="2927116873", group_id=626266902, user_id=123456789))
    try:
        await TaskManager.add_task(
            "media-task-1",
            {
                "bot_id": "3234802804",
                "group_id": 626266902,
                "task_type": "sing",
            },
        )
    finally:
        nb_current_event.reset(token_event)
        nb_current_bot.reset(token_bot)

    assert TaskManager._tasks["media-task-1"]["bot_id"] == 2927116873
    assert TaskManager._tasks["media-task-1"]["group_id"] == 626266902
    assert TaskManager._tasks["media-task-1"]["user_id"] == 123456789
    assert registered == [
        (
            "media-task-1",
            {
                "bot_id": 2927116873,
                "group_id": 626266902,
                "task_type": "sing",
                "user_id": 123456789,
            },
        )
    ]


@pytest.mark.asyncio
async def test_task_manager_non_media_task_keeps_original_bot_binding(monkeypatch) -> None:
    TaskManager._tasks = {}
    registered: list[tuple[str, dict]] = []

    def fake_register(task_id: str, task_status: dict) -> None:
        registered.append((task_id, dict(task_status)))

    monkeypatch.setattr("pallas.core.platform.shard.coord.ai_task_registry.register_ai_task", fake_register)
    token_bot = nb_current_bot.set(SimpleNamespace(self_id="2927116873"))
    token_event = nb_current_event.set(SimpleNamespace(self_id="2927116873", group_id=626266902, user_id=123456789))
    try:
        await TaskManager.add_task(
            "llm-task-1",
            {
                "bot_id": "3234802804",
                "group_id": 626266902,
                "task_type": "llm_chat",
            },
        )
    finally:
        nb_current_event.reset(token_event)
        nb_current_bot.reset(token_bot)

    assert TaskManager._tasks["llm-task-1"]["bot_id"] == "3234802804"
    assert registered == [
        (
            "llm-task-1",
            {
                "bot_id": "3234802804",
                "group_id": 626266902,
                "task_type": "llm_chat",
            },
        )
    ]


def test_ai_task_registry_uses_redis(fake_coord_redis, monkeypatch) -> None:
    now = 1000.0
    monkeypatch.setattr(mod.shard_ctx, "sharding_active", lambda: True)
    monkeypatch.setattr(mod, "current_worker_port", lambda: 7973)
    monkeypatch.setattr(mod, "get_shard_registry_settings", lambda: SimpleNamespace(shard_id=3))
    monkeypatch.setattr(mod.time, "time", lambda: now)

    mod.register_ai_task(
        "task-redis",
        {"bot_id": "123456", "group_id": 42, "start_time": now},
    )

    rec = mod.get_ai_task_record("task-redis")
    assert rec is not None
    assert rec["worker_port"] == 7973
    assert mod.ai_task_redis_key("task-redis") in fake_coord_redis[0]

    mod.remove_ai_task("task-redis")
    assert mod.get_ai_task_record("task-redis") is None


def test_ai_task_registry_requires_redis_when_sharding(monkeypatch) -> None:
    now = 2000.0
    monkeypatch.setattr(mod.shard_ctx, "sharding_active", lambda: True)
    monkeypatch.setattr(mod, "current_worker_port", lambda: 7974)
    monkeypatch.setattr(mod, "get_shard_registry_settings", lambda: SimpleNamespace(shard_id=4))
    monkeypatch.setattr(mod.time, "time", lambda: now)
    monkeypatch.setattr("pallas.core.platform.coord.redis_settings.coord_redis_enabled", lambda: False)

    mod.register_ai_task(
        "task-none",
        {"bot_id": "654321", "group_id": 99, "start_time": now},
    )

    assert mod.get_ai_task_record("task-none") is None

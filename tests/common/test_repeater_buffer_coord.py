from __future__ import annotations

import asyncio
from contextlib import suppress

import pytest

from src.foundation.db import Message as MessageModel
from src.platform.shard.coord import repeater_buffer as mod
from src.plugins.repeater.message_store import MessageStore
from src.plugins.repeater.model import Chat


def test_repeater_buffer_cross_shard_append(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "_coord_dir", lambda: tmp_path)
    monkeypatch.setattr(mod, "_registry_shard_ids", lambda: frozenset({0, 1}))
    MessageStore._message_dict.clear()
    Chat._recent_topics.clear()

    event_id = "evt1"
    path = tmp_path / f"{event_id}.json"
    mod._write_atomic(
        path,
        {
            "event_id": event_id,
            "source_shard_id": 0,
            "created_at": 1.0,
            "expires_at": mod.time.time() + 60,
            "msg": {
                "group_id": 100,
                "user_id": 42,
                "bot_id": 300,
                "raw_message": "hello",
                "is_plain_text": True,
                "plain_text": "hello",
                "keywords": "hello",
                "time": 1700000000,
            },
            "applied_shard_ids": [],
        },
    )

    settings = type("S", (), {"role": "worker", "shard_id": 1, "enabled": True})()
    monkeypatch.setattr(mod, "get_shard_registry_settings", lambda: settings)
    monkeypatch.setattr(mod, "is_sharding_active", lambda: True)

    asyncio.run(mod.poll_repeater_buffer_pending())

    msgs = MessageStore._message_dict.get(100) or []
    assert len(msgs) == 1
    assert msgs[0].plain_text == "hello"
    assert list(Chat._recent_topics[100]) == []


def test_publish_prefers_redis_over_file(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "_coord_dir", lambda: tmp_path)
    monkeypatch.setattr(mod, "publish_repeater_buffer_redis_sync", lambda env: True)
    monkeypatch.setattr(mod, "is_sharding_active", lambda: True)
    monkeypatch.setattr(
        mod,
        "get_shard_registry_settings",
        lambda: type("S", (), {"role": "worker", "shard_id": 0, "enabled": True})(),
    )
    wrote: list[str] = []
    monkeypatch.setattr(
        mod,
        "publish_repeater_buffer_file_sync",
        lambda env: wrote.append(str(env["event_id"])),
    )

    chat = type(
        "Chat",
        (),
        {
            "group_id": 1,
            "user_id": 2,
            "bot_id": 3,
            "raw_message": "hi",
            "plain_text": "hi",
            "is_plain_text": True,
            "keywords": "hi",
            "_keywords_list": ["hi"],
            "time": 99,
        },
    )()
    mod.publish_repeater_buffer_event_sync(chat)
    assert wrote == []


def test_repeater_buffer_cross_shard_append_topics(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "_coord_dir", lambda: tmp_path)
    monkeypatch.setattr(mod, "_registry_shard_ids", lambda: frozenset({0, 1}))
    MessageStore._message_dict.clear()
    Chat._recent_topics.clear()

    event_id = "evt-topics"
    path = tmp_path / f"{event_id}.json"
    mod._write_atomic(
        path,
        {
            "event_id": event_id,
            "source_shard_id": 0,
            "created_at": 1.0,
            "expires_at": mod.time.time() + 60,
            "msg": {
                "group_id": 200,
                "user_id": 43,
                "bot_id": 301,
                "raw_message": "草",
                "is_plain_text": True,
                "plain_text": "草",
                "keywords": "草",
                "topics": ["草", "热梗"],
                "time": 1700000001,
            },
            "applied_shard_ids": [],
        },
    )

    settings = type("S", (), {"role": "worker", "shard_id": 1, "enabled": True})()
    monkeypatch.setattr(mod, "get_shard_registry_settings", lambda: settings)
    monkeypatch.setattr(mod, "is_sharding_active", lambda: True)

    asyncio.run(mod.poll_repeater_buffer_pending())

    assert list(Chat._recent_topics[200]) == ["草", "热梗"]


def test_repeater_buffer_duplicate_tail_does_not_append_topics() -> None:
    MessageStore._message_dict.clear()
    Chat._recent_topics.clear()
    MessageStore._message_dict[100] = [
        MessageModel.model_construct(
            group_id=100,
            user_id=42,
            bot_id=300,
            raw_message="hello",
            is_plain_text=True,
            plain_text="hello",
            keywords="hello",
            time=1700000000,
        )
    ]
    Chat._recent_topics[100].append("existing")
    msg = {
        "group_id": 100,
        "user_id": 42,
        "bot_id": 300,
        "raw_message": "hello",
        "is_plain_text": True,
        "plain_text": "hello",
        "keywords": "hello",
        "topics": ["new-topic"],
        "time": 1700000000,
    }

    assert asyncio.run(mod.apply_repeater_buffer_message(msg)) is False
    assert list(Chat._recent_topics[100]) == ["existing"]


def test_repeater_buffer_skips_duplicate_tail(tmp_path, monkeypatch):
    MessageStore._message_dict.clear()
    MessageStore._message_dict[100] = [
        MessageModel.model_construct(
            group_id=100,
            user_id=42,
            bot_id=300,
            raw_message="hello",
            is_plain_text=True,
            plain_text="hello",
            keywords="hello",
            time=1700000000,
        )
    ]
    msg = {
        "group_id": 100,
        "user_id": 42,
        "bot_id": 300,
        "raw_message": "hello",
        "is_plain_text": True,
        "plain_text": "hello",
        "keywords": "hello",
        "time": 1700000000,
    }
    assert asyncio.run(mod.apply_repeater_buffer_message(msg)) is False
    assert len(MessageStore._message_dict[100]) == 1


@pytest.mark.asyncio
async def test_schedule_publish_repeater_buffer_reuses_single_worker(monkeypatch):
    created: list[str | None] = []
    published: list[dict[str, object]] = []
    real_create_task = asyncio.create_task

    async def fake_to_thread(fn, *args, **kwargs):
        return fn(*args, **kwargs)

    def fake_create_task(coro, *args, **kwargs):
        created.append(kwargs.get("name"))
        return real_create_task(coro)

    monkeypatch.setattr(mod, "is_sharding_active", lambda: True)
    monkeypatch.setattr(mod, "publish_repeater_buffer_payload_sync", lambda payload: published.append(dict(payload)))
    monkeypatch.setattr(mod.asyncio, "to_thread", fake_to_thread)
    monkeypatch.setattr(mod.asyncio, "create_task", fake_create_task)
    monkeypatch.setattr(mod, "_publish_pending", mod.deque())
    monkeypatch.setattr(mod, "_publish_event", None)
    monkeypatch.setattr(mod, "_publish_worker_task", None)
    monkeypatch.setattr(mod, "_publish_worker_loop_ref", None)

    chat = type(
        "Chat",
        (),
        {
            "group_id": 1,
            "user_id": 2,
            "bot_id": 3,
            "raw_message": "hi",
            "plain_text": "hi",
            "is_plain_text": True,
            "keywords": "hi",
            "_keywords_list": ["hi"],
            "time": 99,
        },
    )()

    mod.schedule_publish_repeater_buffer(chat)
    mod.schedule_publish_repeater_buffer(chat)
    mod.schedule_publish_repeater_buffer(chat)

    await asyncio.sleep(0)
    await asyncio.sleep(0)

    worker = mod._publish_worker_task
    if worker is not None:
        worker.cancel()
        with suppress(asyncio.CancelledError):
            await worker

    assert len(created) == 1
    assert len(published) == 3


@pytest.mark.asyncio
async def test_schedule_publish_repeater_buffer_drops_oldest_when_queue_full(monkeypatch):
    published: list[dict[str, object]] = []

    async def fake_to_thread(fn, *args, **kwargs):
        return fn(*args, **kwargs)

    monkeypatch.setattr(mod, "is_sharding_active", lambda: True)
    monkeypatch.setattr(mod, "publish_repeater_buffer_payload_sync", lambda payload: published.append(dict(payload)))
    monkeypatch.setattr(mod.asyncio, "to_thread", fake_to_thread)
    monkeypatch.setattr(mod, "_PUBLISH_QUEUE_MAX", 2)
    monkeypatch.setattr(mod, "_publish_pending", mod.deque())
    monkeypatch.setattr(mod, "_publish_event", None)
    monkeypatch.setattr(mod, "_publish_worker_task", None)
    monkeypatch.setattr(mod, "_publish_worker_loop_ref", None)

    def make_chat(idx: int):
        return type(
            "Chat",
            (),
            {
                "group_id": 1,
                "user_id": idx,
                "bot_id": 3,
                "raw_message": f"m{idx}",
                "plain_text": f"m{idx}",
                "is_plain_text": True,
                "keywords": f"m{idx}",
                "_keywords_list": [f"m{idx}"],
                "time": 100 + idx,
            },
        )()

    mod.schedule_publish_repeater_buffer(make_chat(1))
    mod.schedule_publish_repeater_buffer(make_chat(2))
    mod.schedule_publish_repeater_buffer(make_chat(3))

    await asyncio.sleep(0)
    await asyncio.sleep(0)

    worker = mod._publish_worker_task
    if worker is not None:
        worker.cancel()
        with suppress(asyncio.CancelledError):
            await worker

    assert [item["plain_text"] for item in published] == ["m2", "m3"]

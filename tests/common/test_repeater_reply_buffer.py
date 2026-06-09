"""repeater_reply_buffer 跨片同步与 ban 多牛匹配。"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from contextlib import suppress
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def test_should_publish_reply_record_skips_placeholders():
    from src.plugins.repeater.model import Chat
    from src.plugins.repeater.reply_record_sync import should_publish_reply_record

    assert should_publish_reply_record({"reply": "hello", "reply_keywords": "kw"}) is True
    assert should_publish_reply_record({"reply": Chat.REPLY_FLAG, "reply_keywords": Chat.REPLY_FLAG}) is False
    assert should_publish_reply_record({"reply": Chat.SPEAK_FLAG, "reply_keywords": Chat.SPEAK_FLAG}) is False
    assert should_publish_reply_record({"reply": "  ", "reply_keywords": "kw"}) is False
    assert should_publish_reply_record({"reply": "实际发言", "reply_keywords": Chat.SPEAK_FLAG}) is True


def test_publish_reply_record_skips_coord_when_placeholder():
    from src.plugins.repeater.model import Chat
    from src.plugins.repeater.reply_record_sync import publish_reply_record

    with patch(
        "src.platform.shard.coord.repeater_reply_buffer.schedule_publish_repeater_reply_record",
        MagicMock(),
    ) as mock_schedule:
        with patch("src.platform.shard.registry.config.is_sharding_active", return_value=True):
            publish_reply_record(1, 2, {"reply": Chat.REPLY_FLAG, "reply_keywords": Chat.REPLY_FLAG})
    mock_schedule.assert_not_called()


@pytest.mark.asyncio
async def test_apply_repeater_reply_record_merges_into_chat_reply_dict():
    from src.platform.shard.coord.repeater_reply_buffer import apply_repeater_reply_record
    from src.plugins.repeater.model import Chat

    group_id = 90001
    bot_id = 80001
    record = {
        "group_id": group_id,
        "bot_id": bot_id,
        "time": 123,
        "pre_raw_message": "hello",
        "pre_keywords": "hello_kw",
        "reply": "world",
        "reply_keywords": "world_kw",
    }

    try:
        assert await apply_repeater_reply_record(record) is True
        assert Chat._reply_dict[group_id][bot_id][-1]["reply"] == "world"
        assert await apply_repeater_reply_record(record) is False
    finally:
        Chat._reply_dict[group_id].pop(bot_id, None)


@pytest.mark.asyncio
async def test_ban_searches_other_bot_reply_cache():
    from src.plugins.repeater.ban_manager import BanManager

    group_id = 90002
    primary_bot = 80002
    other_bot = 80003
    reply_dict = defaultdict(lambda: defaultdict(list))
    reply_dict[group_id][other_bot] = [
        {
            "time": 100,
            "pre_raw_message": "trigger",
            "pre_keywords": "trigger_kw",
            "reply": "bad line",
            "reply_keywords": "bad_kw",
        }
    ]

    BanManager._blacklist_answer.clear()
    BanManager._blacklist_answer_reserve.clear()

    try:
        with patch(
            "src.plugins.repeater.ban_manager.context_repo.append_ban",
            new_callable=AsyncMock,
        ) as mock_append:
            result = await BanManager.ban(group_id, primary_bot, "bad line", "test", reply_dict)

        assert result is True
        assert mock_append.call_count == 1
        pre_kw, ban_obj = mock_append.call_args.args
        assert pre_kw == "trigger_kw"
        assert ban_obj.keywords == "bad_kw"
    finally:
        BanManager._blacklist_answer.clear()
        BanManager._blacklist_answer_reserve.clear()


@pytest.mark.asyncio
async def test_schedule_publish_repeater_reply_record_reuses_single_worker(monkeypatch):
    from src.platform.shard.coord import repeater_reply_buffer as mod

    created: list[str | None] = []
    published: list[dict[str, object]] = []
    real_create_task = asyncio.create_task

    async def fake_to_thread(fn, *args, **kwargs):
        return fn(*args, **kwargs)

    def fake_create_task(coro, *args, **kwargs):
        created.append(kwargs.get("name"))
        return real_create_task(coro)

    monkeypatch.setattr(mod, "is_sharding_active", lambda: True)
    monkeypatch.setattr(mod, "publish_repeater_reply_payload_sync", lambda payload: published.append(dict(payload)))
    monkeypatch.setattr(mod.asyncio, "to_thread", fake_to_thread)
    monkeypatch.setattr(mod.asyncio, "create_task", fake_create_task)
    monkeypatch.setattr(mod, "_publish_pending", mod.deque())
    monkeypatch.setattr(mod, "_publish_event", None)
    monkeypatch.setattr(mod, "_publish_worker_task", None)
    monkeypatch.setattr(mod, "_publish_worker_loop_ref", None)

    record = {
        "time": 1,
        "pre_raw_message": "q",
        "pre_keywords": "qk",
        "reply": "a",
        "reply_keywords": "ak",
    }
    mod.schedule_publish_repeater_reply_record(1, 2, record)
    mod.schedule_publish_repeater_reply_record(1, 2, record)
    mod.schedule_publish_repeater_reply_record(1, 2, record)

    await asyncio.sleep(0)
    await asyncio.sleep(0)

    worker = mod._publish_worker_task
    if worker is not None:
        worker.cancel()
        with suppress(asyncio.CancelledError):
            await worker

    assert len(created) == 1
    assert len(published) == 3

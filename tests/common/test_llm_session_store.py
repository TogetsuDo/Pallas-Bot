from __future__ import annotations

import pytest

from pallas.product.llm.behavior import BehaviorAction, BehaviorOutcome, BehaviorRun, BehaviorScene
from pallas.product.llm.behavior_store import append_behavior_run
from pallas.product.llm.config import LlmConfig, clear_llm_config_cache
from pallas.product.llm.session_store import (
    append_llm_message,
    build_llm_chat_messages,
    clear_llm_messages,
    clear_user_llm_messages,
    get_llm_history_session_detail,
    is_llm_session_store_available,
    list_group_ambient_messages,
    list_llm_history_sessions,
    list_user_llm_messages,
    sanitize_stored_content,
    user_ttl_seconds,
)


def test_sanitize_stored_content_strips_control_chars() -> None:
    raw = "hello\x00world"
    assert sanitize_stored_content("user", raw, max_len=200) == "helloworld"


def test_sanitize_stored_content_strips_vision_segments(monkeypatch: pytest.MonkeyPatch) -> None:
    clear_llm_config_cache()
    monkeypatch.setenv("LLM_SESSION_STRIP_VISION_ENABLED", "1")
    raw = "[CQ:image,file=abc] 看看"
    assert sanitize_stored_content("user", raw, max_len=200) == "[图片] 看看"
    assert sanitize_stored_content("assistant", raw, max_len=200) == raw


def test_user_ttl_private_vs_group() -> None:
    cfg = LlmConfig()
    assert user_ttl_seconds(12345, cfg) == 0
    assert user_ttl_seconds(0, cfg) == 259200
    assert user_ttl_seconds(None, cfg) == 259200


@pytest.mark.asyncio
async def test_llm_session_store_noop_when_disabled(monkeypatch) -> None:
    clear_llm_config_cache()
    monkeypatch.setenv("LLM_SESSION_ENABLED", "0")
    assert is_llm_session_store_available() is False
    ok = await append_llm_message(1, 100, 200, "user", "hi")
    assert ok is False
    assert await list_user_llm_messages(1, 100, 200) == []


@pytest.mark.asyncio
async def test_llm_session_user_window_independent(pg_engine, monkeypatch) -> None:
    clear_llm_config_cache()
    monkeypatch.setenv("LLM_SESSION_ENABLED", "1")
    cfg = LlmConfig(
        llm_session_enabled=True,
        llm_session_user_window=2,
        llm_session_group_window=2,
        llm_session_user_ttl_sec=0,
    )
    monkeypatch.setattr("pallas.product.llm.session_store.get_llm_config", lambda: cfg)
    monkeypatch.setattr("pallas.product.llm.session_store.is_postgresql_backend", lambda: True)

    for index in range(3):
        assert await append_llm_message(10001, 20002, 30003, "user", f"a-{index}") is True
    for index in range(3):
        assert await append_llm_message(10001, 20002, 40004, "user", f"b-{index}") is True

    user_a = await list_user_llm_messages(10001, 20002, 30003)
    user_b = await list_user_llm_messages(10001, 20002, 40004)
    assert [turn.content for turn in user_a] == ["a-1", "a-2"]
    assert [turn.content for turn in user_b] == ["b-1", "b-2"]

    ambient = await list_group_ambient_messages(10001, 20002)
    assert len(ambient) == 2
    assert {turn.content for turn in ambient} == {"a-2", "b-2"}


@pytest.mark.asyncio
async def test_build_llm_chat_messages_user_thread_and_ambient(pg_engine, monkeypatch) -> None:
    clear_llm_config_cache()
    cfg = LlmConfig(
        llm_session_enabled=True,
        llm_session_user_window=8,
        llm_session_group_window=4,
        llm_session_user_ttl_sec=0,
    )
    monkeypatch.setattr("pallas.product.llm.session_store.get_llm_config", lambda: cfg)
    monkeypatch.setattr("pallas.product.llm.session_store.is_postgresql_backend", lambda: True)

    await append_llm_message(1, 100, 200, "user", "other-user-msg")
    await append_llm_message(1, 100, 200, "assistant", "reply-to-other")
    await append_llm_message(1, 100, 300, "user", "my-old")
    await append_llm_message(1, 100, 300, "assistant", "my-reply")

    messages = await build_llm_chat_messages(1, 100, 300, "my-new", cfg=cfg)
    assert messages[-1].role == "user"
    assert "my-new" in messages[-1].content
    assert any("群环境摘录" in item.content for item in messages)
    assert any("my-old" in item.content for item in messages)


@pytest.mark.asyncio
async def test_clear_user_llm_messages(pg_engine, monkeypatch) -> None:
    clear_llm_config_cache()
    cfg = LlmConfig(llm_session_enabled=True, llm_session_user_ttl_sec=0)
    monkeypatch.setattr("pallas.product.llm.session_store.get_llm_config", lambda: cfg)
    monkeypatch.setattr("pallas.product.llm.session_store.is_postgresql_backend", lambda: True)

    await append_llm_message(1, 100, 200, "user", "a")
    await append_llm_message(1, 100, 300, "user", "b")
    assert await clear_user_llm_messages(1, 100, 200) == 1
    assert await list_user_llm_messages(1, 100, 200) == []
    assert len(await list_user_llm_messages(1, 100, 300)) == 1

    assert await clear_llm_messages(1, 100) == 1


@pytest.mark.asyncio
async def test_list_llm_history_sessions_and_detail(pg_engine, monkeypatch) -> None:
    clear_llm_config_cache()
    cfg = LlmConfig(
        llm_session_enabled=True,
        llm_session_user_window=20,
        llm_session_group_window=20,
        llm_session_user_ttl_sec=0,
    )
    monkeypatch.setattr("pallas.product.llm.session_store.get_llm_config", lambda: cfg)
    monkeypatch.setattr("pallas.product.llm.session_store.is_postgresql_backend", lambda: True)

    await append_llm_message(10, 100, 200, "user", "u200-1")
    await append_llm_message(10, 100, 200, "assistant", "a200-1")
    await append_llm_message(10, 100, 300, "user", "u300-1")
    await append_llm_message(10, 100, 300, "assistant", "a300-1")
    await append_llm_message(10, 0, 400, "user", "private-1")

    sessions = await list_llm_history_sessions(bot_id=10, group_id=100, limit=10)
    assert [row.user_id for row in sessions] == [300, 200]
    assert sessions[0].last_content == "a300-1"
    assert sessions[0].turn_count == 2

    detail = await get_llm_history_session_detail(bot_id=10, group_id=100, user_id=200, limit=10)
    assert detail is not None
    assert detail.session.user_id == 200
    assert [turn.content for turn in detail.turns] == ["u200-1", "a200-1"]


@pytest.mark.asyncio
async def test_llm_history_detail_includes_behavior_runs(pg_engine, monkeypatch, tmp_path) -> None:
    clear_llm_config_cache()
    monkeypatch.setenv("PALLAS_DATA_DIR", str(tmp_path))
    cfg = LlmConfig(
        llm_session_enabled=True,
        llm_session_user_window=20,
        llm_session_group_window=20,
        llm_session_user_ttl_sec=0,
    )
    monkeypatch.setattr("pallas.product.llm.session_store.get_llm_config", lambda: cfg)
    monkeypatch.setattr("pallas.product.llm.session_store.is_postgresql_backend", lambda: True)

    await append_llm_message(10, 100, 200, "user", "u200-1")
    await append_llm_message(10, 100, 200, "assistant", "a200-1")
    append_behavior_run(
        BehaviorRun(
            request_id="req-1",
            bot_id=10,
            group_id=100,
            user_id=200,
            scene=BehaviorScene.PROVOCATION,
            selected_pattern_ids=["p1"],
            selected_actions=[BehaviorAction.LIGHT_TEASE_AND_CLOSE],
            final_outcome=BehaviorOutcome.NEUTRAL,
        )
    )

    detail = await get_llm_history_session_detail(bot_id=10, group_id=100, user_id=200, limit=10)
    assert detail is not None
    assert detail.behavior_runs[0]["request_id"] == "req-1"
    assert detail.behavior_runs[0]["selected_actions"] == ["light_tease_and_close"]

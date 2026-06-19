from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest


@pytest.mark.asyncio
async def test_handle_llm_chat_records_route_and_fallback_meta(monkeypatch: pytest.MonkeyPatch) -> None:
    from packages.llm_chat import chat_message as mod

    event = SimpleNamespace(
        to_me=True,
        self_id="10001",
        group_id=20002,
        user_id=30003,
        message_id=40004,
        time=123456,
        raw_message="[CQ:at,qq=10001] 你好",
        get_plaintext=lambda: "你好",
        get_message=lambda: "[CQ:at,qq=10001] 你好",
        get_session_id=lambda: "group_20002_30003",
    )
    bot = SimpleNamespace(self_id="10001")

    added: dict[str, object] = {}

    async def fake_add_task(task_id: str, payload: dict) -> None:
        added["task_id"] = task_id
        added["payload"] = payload

    monkeypatch.setattr(mod, "is_llm_chat_service_enabled", lambda: True)
    monkeypatch.setattr(
        mod,
        "get_llm_chat_config",
        lambda: SimpleNamespace(
            llm_chat_system_prompt_path="",
            llm_chat_min_priority=40,
        ),
    )
    monkeypatch.setattr(
        mod,
        "get_llm_config",
        lambda: SimpleNamespace(
            llm_memory_rag_enabled=False,
            llm_relationship_notes_enabled=False,
            llm_select_enabled=True,
            llm_polish_lite_enabled=False,
            llm_polish_enabled=False,
            llm_chat_cooldown_sec=3,
            llm_chat_queue_merge=True,
        ),
    )
    monkeypatch.setattr(
        mod,
        "build_persona_llm_context",
        AsyncMock(
            return_value=(
                SimpleNamespace(system="sys", metadata=SimpleNamespace(persona={})),
                None,
                None,
            )
        ),
    )
    monkeypatch.setattr(mod, "append_memory_context", AsyncMock(side_effect=lambda prompt, **_: prompt))
    monkeypatch.setattr(mod, "append_relationship_context", AsyncMock(side_effect=lambda prompt, **_: prompt))
    monkeypatch.setattr(mod, "GroupMessageEvent", SimpleNamespace)
    monkeypatch.setattr(mod, "evaluate_llm_reply_gate", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(mod, "check_llm_chat_gate", AsyncMock(return_value=None))
    monkeypatch.setattr(mod, "refresh_llm_chat_cooldown", AsyncMock())
    monkeypatch.setattr(
        mod,
        "merge_queued_chat",
        lambda *_args, **_kwargs: SimpleNamespace(text="[CQ:at,qq=10001] 你好", merged=False),
    )
    monkeypatch.setattr(mod, "latest_llm_assistant_reply", AsyncMock(return_value="上一句"))
    monkeypatch.setattr(
        mod,
        "submit_chat_task",
        AsyncMock(return_value=SimpleNamespace(ok=True, task_id="ai-task-1", status="queued")),
    )
    monkeypatch.setattr(mod.TaskManager, "add_task", fake_add_task)

    bundle = SimpleNamespace(
        message_pool=["候选一", "候选二"],
        answer_list=["候选一"],
    )

    class FakeChat:
        def __init__(self, _event):
            pass

        async def find_reply_bundle(self):
            return bundle

    monkeypatch.setitem(__import__("sys").modules, "packages.repeater.model", SimpleNamespace(Chat=FakeChat))
    monkeypatch.setattr(mod, "maybe_submit_repeater_corpus_llm", AsyncMock(return_value=False))

    await mod.handle_llm_chat(bot, event)

    payload = added["payload"]
    assert isinstance(payload, dict)
    assert payload["task_type"] == "llm_chat"
    assert payload["fallback_text"] == "候选一"
    assert payload["llm_route"] == "corpus_select"
    assert payload["last_reply_text"] == "上一句"

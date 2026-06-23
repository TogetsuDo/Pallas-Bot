from __future__ import annotations

import pytest

from pallas.product.llm.config import LlmConfig
from pallas.product.llm.kernel.observability import build_conversation_kernel_status
from pallas.product.llm.memory.inject import append_memory_context, append_relationship_context


@pytest.mark.asyncio
async def test_append_memory_context_skips_when_policy_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = LlmConfig(llm_chat_enabled=True, llm_memory_rag_enabled=True)
    monkeypatch.setattr(
        "pallas.product.llm.memory.inject.can_read_persistent_memory",
        lambda _cfg=None: False,
    )
    result = await append_memory_context("base", bot_id=1, group_id=2, query_text="银灰", cfg=cfg)
    assert result == "base"


@pytest.mark.asyncio
async def test_append_relationship_context_skips_when_policy_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = LlmConfig(llm_chat_enabled=True, llm_relationship_notes_enabled=True)
    monkeypatch.setattr(
        "pallas.product.llm.memory.inject.can_read_persistent_memory",
        lambda _cfg=None: False,
    )
    result = await append_relationship_context(
        "base",
        bot_id=1,
        group_id=2,
        user_id=3,
        cfg=cfg,
    )
    assert result == "base"


def test_build_conversation_kernel_status_exposes_summary_gate() -> None:
    status = build_conversation_kernel_status(
        LlmConfig(
            llm_chat_enabled=True,
            llm_session_enabled=True,
            llm_session_summary_enabled=True,
            llm_memory_rag_enabled=True,
        )
    )
    assert status["runtime_state_summary_active"] is True
    policy = status["memory_policy"]
    assert policy["read_session"] is True
    assert policy["write_session"] is True
    assert policy["runtime_state_summary_enabled"] is True
    assert policy["read_persistent_memory"] is True

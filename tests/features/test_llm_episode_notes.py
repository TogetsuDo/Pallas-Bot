from __future__ import annotations

import pytest

from pallas.product.llm.config import LlmConfig
from pallas.product.llm.memory.inject import append_memory_context
from pallas.product.llm.memory.policy import classify_memory_candidate


def test_episode_note_accepts_teach_fact() -> None:
    assert classify_memory_candidate("记住：本群管银灰厨") == "episode_note"


def test_episode_note_rejects_short_emotion() -> None:
    assert classify_memory_candidate("记住：我今天烦") is None


@pytest.mark.asyncio
async def test_injected_episode_notes_do_not_exceed_cap(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "pallas.product.llm.memory.store.retrieve_memory_entries",
        lambda bot_id, group_id, query_text, cfg=None: [
            "第一条旧事",
            "第二条旧事",
            "第三条旧事",
            "第四条旧事",
        ],
    )
    cfg = LlmConfig(llm_memory_rag_enabled=True, llm_memory_rag_top_k=4, llm_memory_content_max_len=200)
    out = await append_memory_context(
        "基础 system",
        bot_id=10001,
        group_id=12345,
        query_text="今天聊什么",
        cfg=cfg,
    )
    lines = [line for line in out.splitlines() if line.startswith("- ")]
    assert len(lines) <= 3

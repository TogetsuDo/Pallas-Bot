"""启发式 auto_episode 与 file ingest。"""

from __future__ import annotations

import pytest

from pallas.product.llm.config import LlmConfig
from pallas.product.llm.knowledge.file_ingest import (
    load_file_knowledge_decl,
    reset_file_knowledge_registration_for_tests,
)
from pallas.product.llm.memory.auto_episode import (
    clear_auto_episode_cooldown_for_tests,
    maybe_auto_save_episode,
)


@pytest.mark.asyncio
async def test_auto_episode_skips_low_value(monkeypatch: pytest.MonkeyPatch) -> None:
    clear_auto_episode_cooldown_for_tests()
    called = {"n": 0}

    async def fake_save(*_a, **_k):
        called["n"] += 1
        return True

    monkeypatch.setattr(
        "pallas.product.llm.memory.auto_episode.is_llm_memory_store_available",
        lambda: True,
    )
    monkeypatch.setattr(
        "pallas.product.llm.memory.auto_episode.can_read_persistent_memory",
        lambda _cfg=None: True,
    )
    monkeypatch.setattr("pallas.product.llm.memory.auto_episode.save_memory_entry", fake_save)
    cfg = LlmConfig(llm_memory_auto_episode_enabled=True, llm_memory_auto_episode_cooldown_sec=0)
    assert await maybe_auto_save_episode(bot_id=1, group_id=2, user_text="好烦", cfg=cfg) is False
    assert called["n"] == 0


@pytest.mark.asyncio
async def test_auto_episode_saves_valuable_note(monkeypatch: pytest.MonkeyPatch) -> None:
    clear_auto_episode_cooldown_for_tests()
    called: dict[str, str] = {}

    async def fake_save(_bot, _gid, content, *, source="teach", cfg=None):
        called["content"] = content
        called["source"] = source
        return True

    monkeypatch.setattr(
        "pallas.product.llm.memory.auto_episode.is_llm_memory_store_available",
        lambda: True,
    )
    monkeypatch.setattr(
        "pallas.product.llm.memory.auto_episode.can_read_persistent_memory",
        lambda _cfg=None: True,
    )
    monkeypatch.setattr("pallas.product.llm.memory.auto_episode.save_memory_entry", fake_save)
    cfg = LlmConfig(llm_memory_auto_episode_enabled=True, llm_memory_auto_episode_cooldown_sec=0)
    ok = await maybe_auto_save_episode(
        bot_id=1,
        group_id=2,
        user_text="记住：本群周五固定开黑",
        cfg=cfg,
    )
    assert ok is True
    assert called["source"] == "auto_episode"
    assert "开黑" in called["content"]


def test_file_ingest_loads_markdown(tmp_path) -> None:
    reset_file_knowledge_registration_for_tests()
    (tmp_path / "sample.md").write_text(
        "# Demo\n\n## 什么是 Pallas\n\nPallas-Bot 是群聊机器人。\n",
        encoding="utf-8",
    )
    decl = load_file_knowledge_decl(root=tmp_path)
    assert decl is not None
    assert decl.source_id == "pallas.file_ingest"
    assert decl.chunks
    titles = {c.title for c in decl.chunks}
    assert "什么是 Pallas" in titles

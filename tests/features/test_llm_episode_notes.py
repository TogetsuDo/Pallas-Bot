from __future__ import annotations

from types import SimpleNamespace

import pytest

from pallas.product.llm.config import LlmConfig
from pallas.product.llm.memory.inject import append_memory_context
from pallas.product.llm.memory.policy import classify_memory_candidate
from pallas.product.llm.memory.store import derive_memory_keywords


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


@pytest.mark.asyncio
async def test_append_memory_context_falls_back_to_group_ambient_candidates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_retrieve(bot_id: int, group_id: int | None, query_text: str, *, cfg=None):
        return []

    monkeypatch.setattr("pallas.product.llm.memory.inject.retrieve_memory_entries", fake_retrieve)

    from pallas.product.llm.session_store import LlmChatTurn

    async def fake_ambient(bot_id: int, group_id: int | None, *, limit=None, cfg=None):
        return [
            LlmChatTurn(role="user", content="本群今天都在聊银灰模组", user_id=1, created_at=10),
            LlmChatTurn(role="user", content="我今天烦", user_id=2, created_at=11),
            LlmChatTurn(role="assistant", content="这个不该入旧事", user_id=10001, created_at=12),
        ]

    monkeypatch.setattr(
        "pallas.product.llm.memory.inject.list_group_ambient_messages",
        fake_ambient,
    )

    cfg = LlmConfig(llm_memory_rag_enabled=True, llm_memory_rag_top_k=3, llm_memory_content_max_len=200)
    out = await append_memory_context(
        "基础 system",
        bot_id=10001,
        group_id=12345,
        query_text="银灰怎么配队",
        cfg=cfg,
    )

    assert "本群今天都在聊银灰模组" in out
    assert "我今天烦" not in out
    assert "这个不该入旧事" not in out


@pytest.mark.asyncio
async def test_append_memory_context_prefers_stored_entries_before_ambient_candidates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_retrieve(bot_id: int, group_id: int | None, query_text: str, *, cfg=None):
        return ["已存旧事"]

    monkeypatch.setattr("pallas.product.llm.memory.inject.retrieve_memory_entries", fake_retrieve)

    from pallas.product.llm.session_store import LlmChatTurn

    async def fake_ambient(bot_id: int, group_id: int | None, *, limit=None, cfg=None):
        return [
            LlmChatTurn(role="user", content="本群今天都在聊银灰模组", user_id=1, created_at=10),
            LlmChatTurn(role="user", content="本群管银灰厨", user_id=2, created_at=11),
        ]

    monkeypatch.setattr(
        "pallas.product.llm.memory.inject.list_group_ambient_messages",
        fake_ambient,
    )

    cfg = LlmConfig(llm_memory_rag_enabled=True, llm_memory_rag_top_k=3, llm_memory_content_max_len=200)
    out = await append_memory_context(
        "基础 system",
        bot_id=10001,
        group_id=12345,
        query_text="银灰怎么配队",
        cfg=cfg,
    )

    lines = [line for line in out.splitlines() if line.startswith("- ")]
    assert lines[0] == "- 已存旧事"
    assert len(lines) <= 3


@pytest.mark.asyncio
async def test_append_memory_context_sorts_ambient_candidates_by_query_relevance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_retrieve(bot_id: int, group_id: int | None, query_text: str, *, cfg=None):
        return []

    monkeypatch.setattr("pallas.product.llm.memory.inject.retrieve_memory_entries", fake_retrieve)

    from pallas.product.llm.session_store import LlmChatTurn

    async def fake_ambient(bot_id: int, group_id: int | None, *, limit=None, cfg=None):
        return [
            LlmChatTurn(role="user", content="本群都在聊麦哲伦皮肤", user_id=1, created_at=10),
            LlmChatTurn(role="user", content="本群都在聊银灰模组", user_id=2, created_at=11),
            LlmChatTurn(role="user", content="本群最近常提玛恩纳", user_id=3, created_at=12),
        ]

    monkeypatch.setattr(
        "pallas.product.llm.memory.inject.list_group_ambient_messages",
        fake_ambient,
    )

    cfg = LlmConfig(llm_memory_rag_enabled=True, llm_memory_rag_top_k=3, llm_memory_content_max_len=200)
    out = await append_memory_context(
        "基础 system",
        bot_id=10001,
        group_id=12345,
        query_text="银灰怎么配队",
        cfg=cfg,
    )

    lines = [line for line in out.splitlines() if line.startswith("- ")]
    assert lines[0] == "- 本群都在聊银灰模组"


@pytest.mark.asyncio
async def test_save_memory_entry_updates_existing_duplicate(monkeypatch: pytest.MonkeyPatch) -> None:
    existing = SimpleNamespace(
        id=7,
        bot_id=10001,
        group_id=12345,
        keywords=derive_memory_keywords("本群管银灰厨"),
        content="本群管银灰厨",
        source="teach",
        created_at=10,
        updated_at=10,
    )
    added: list[object] = []
    flushed = False
    committed = False

    class FakeScalarResult:
        def scalar_one_or_none(self):
            return existing

        def scalar_one(self):
            return 1

    class FakeSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        def add(self, obj):
            added.append(obj)

        async def flush(self):
            nonlocal flushed
            flushed = True

        async def commit(self):
            nonlocal committed
            committed = True

        async def execute(self, _stmt):
            return FakeScalarResult()

    monkeypatch.setattr("pallas.product.llm.memory.store.is_llm_memory_store_available", lambda: True)
    monkeypatch.setattr("pallas.product.llm.memory.store.get_session", lambda *args, **kwargs: FakeSession())

    from pallas.product.llm.memory.store import save_memory_entry

    cfg = LlmConfig(llm_memory_rag_enabled=True, llm_memory_content_max_len=200)
    saved = await save_memory_entry(10001, 12345, "记住：本群管银灰厨", cfg=cfg)

    assert saved is True
    assert added == []
    assert flushed is False
    assert committed is True
    assert existing.content == "本群管银灰厨"
    assert existing.source == "episode_note"
    assert existing.updated_at >= existing.created_at


@pytest.mark.asyncio
async def test_save_memory_entry_reuses_semantic_duplicate_with_normalized_content(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    existing = SimpleNamespace(
        id=8,
        bot_id=10001,
        group_id=12345,
        keywords=derive_memory_keywords("本群管银灰厨"),
        content="本群管银灰厨",
        source="teach",
        created_at=10,
        updated_at=10,
    )

    class FakeRowsResult:
        def scalar_one_or_none(self):
            return None

        def scalars(self):
            return self

        def all(self):
            return [existing]

    class FakeCountResult:
        def scalar_one(self):
            return 1

    class FakeSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        def add(self, obj):
            raise AssertionError("should not add new row for semantic duplicate")

        async def flush(self):
            raise AssertionError("should not flush for semantic duplicate reuse")

        async def commit(self):
            return None

        async def execute(self, _stmt):
            text = str(_stmt)
            if "count(" in text.lower():
                return FakeCountResult()
            return FakeRowsResult()

    monkeypatch.setattr("pallas.product.llm.memory.store.is_llm_memory_store_available", lambda: True)
    monkeypatch.setattr("pallas.product.llm.memory.store.get_session", lambda *args, **kwargs: FakeSession())

    from pallas.product.llm.memory.store import save_memory_entry

    cfg = LlmConfig(llm_memory_rag_enabled=True, llm_memory_content_max_len=200)
    saved = await save_memory_entry(10001, 12345, "记住：本群管银灰厨。", cfg=cfg)

    assert saved is True
    assert existing.content == "本群管银灰厨"
    assert existing.source == "episode_note"


@pytest.mark.asyncio
async def test_save_memory_entry_new_episode_note_uses_episode_note_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    added: list[object] = []

    class FakeExactResult:
        def scalar_one_or_none(self):
            return None

    class FakeRowsResult:
        def scalars(self):
            return self

        def all(self):
            return []

    class FakeCountResult:
        def scalar_one(self):
            return 1

    class FakeSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        def add(self, obj):
            added.append(obj)

        async def flush(self):
            return None

        async def commit(self):
            return None

        async def execute(self, _stmt):
            text = str(_stmt)
            if "count(" in text.lower():
                return FakeCountResult()
            if "order by" in text.lower():
                return FakeRowsResult()
            return FakeExactResult()

    monkeypatch.setattr("pallas.product.llm.memory.store.is_llm_memory_store_available", lambda: True)
    monkeypatch.setattr("pallas.product.llm.memory.store.get_session", lambda *args, **kwargs: FakeSession())

    from pallas.product.llm.memory.store import save_memory_entry

    cfg = LlmConfig(llm_memory_rag_enabled=True, llm_memory_content_max_len=200)
    saved = await save_memory_entry(10001, 12345, "记住：本群今天都在聊银灰", cfg=cfg)

    assert saved is True
    assert len(added) == 1
    assert added[0].source == "episode_note"

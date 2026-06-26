"""记忆检索 hybrid RAG。"""

from __future__ import annotations

from pallas.product.llm.memory.retrieve import memory_relevance_score, rank_memory_candidates


def test_rank_memory_candidates_keyword_mode() -> None:
    rows = rank_memory_candidates(
        "牛牛喜欢摸鱼",
        [
            {"keywords": "摸鱼,休息", "content": "群里常说摸鱼"},
            {"keywords": "加班", "content": "周末要加班"},
        ],
        mode="keyword",
    )
    assert rows
    assert "摸鱼" in rows[0]["content"] or "摸鱼" in rows[0]["keywords"]


def test_rank_memory_candidates_embedding_fallback(monkeypatch) -> None:
    monkeypatch.setattr(
        "pallas.product.llm.knowledge.embedding_client.fetch_embeddings_sync",
        lambda *_args, **_kwargs: None,
    )
    rows = rank_memory_candidates(
        "摸鱼",
        [{"keywords": "摸鱼", "content": "今天摸鱼"}],
        mode="embedding",
    )
    assert len(rows) == 1
    assert rows[0]["score"] == memory_relevance_score("摸鱼", keywords="摸鱼", content="今天摸鱼")


def test_rank_memory_candidates_hybrid_prefers_embedding(monkeypatch) -> None:
    def fake_vectors(texts, **_kwargs):
        vectors = []
        for text in texts:
            if "摸鱼" in text:
                vectors.append([1.0, 0.0])
            else:
                vectors.append([0.0, 1.0])
        return vectors

    monkeypatch.setattr(
        "pallas.product.llm.knowledge.embedding_client.fetch_embeddings_sync",
        fake_vectors,
    )
    rows = rank_memory_candidates(
        "摸鱼话题",
        [
            {"keywords": "摸鱼", "content": "摸鱼快乐"},
            {"keywords": "加班", "content": "周末加班"},
        ],
        mode="hybrid",
    )
    assert rows[0]["keywords"] == "摸鱼"

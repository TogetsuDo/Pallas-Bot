"""可插拔向量检索后端（hybrid RAG MVP）。"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from pallas.core.foundation.config.repo_settings import repo_env_raw_value

if TYPE_CHECKING:
    from pallas.product.llm.knowledge.models import KnowledgeSourceDecl, RetrievedKnowledgeChunk


class VectorRetrieveBackend(Protocol):
    def retrieve(
        self,
        decl: KnowledgeSourceDecl,
        query_text: str,
        *,
        top_k: int,
        max_chunk_len: int,
    ) -> list[RetrievedKnowledgeChunk]: ...


class KeywordVectorBackend:
    def retrieve(
        self,
        decl: KnowledgeSourceDecl,
        query_text: str,
        *,
        top_k: int,
        max_chunk_len: int,
    ) -> list[RetrievedKnowledgeChunk]:
        from pallas.product.llm.knowledge.retrieve import retrieve_chunks_keyword

        return retrieve_chunks_keyword(decl, query_text, top_k=top_k, max_chunk_len=max_chunk_len)


class EmbeddingAugmentedBackend:
    """关键词检索；`LLM_VECTOR_RETRIEVE=embedding` 时走同路径并预留 AI embedding 对接。"""

    def retrieve(
        self,
        decl: KnowledgeSourceDecl,
        query_text: str,
        *,
        top_k: int,
        max_chunk_len: int,
    ) -> list[RetrievedKnowledgeChunk]:
        return KeywordVectorBackend().retrieve(decl, query_text, top_k=top_k, max_chunk_len=max_chunk_len)


_active_backend: VectorRetrieveBackend | None = None


def get_vector_retrieve_backend() -> VectorRetrieveBackend:
    global _active_backend
    if _active_backend is not None:
        return _active_backend
    mode = str(repo_env_raw_value("LLM_VECTOR_RETRIEVE") or "keyword").strip().lower()
    if mode in ("embedding", "hybrid", "vector"):
        _active_backend = EmbeddingAugmentedBackend()
    else:
        _active_backend = KeywordVectorBackend()
    return _active_backend


def set_vector_retrieve_backend(backend: VectorRetrieveBackend | None) -> None:
    global _active_backend
    _active_backend = backend

"""记忆条目相关性打分（关键词 + 可选 hybrid embedding）。"""

from __future__ import annotations

import re
from typing import Any

from pallas.product.llm.knowledge.vector_backend import VectorRetrieveMode, blend_hybrid_score, vector_retrieve_mode

_TOKEN_RE = re.compile(r"[\u4e00-\u9fff]{2,}|[a-z0-9]{2,}", re.IGNORECASE)


_CJK_RUN_RE = re.compile(r"[\u4e00-\u9fff]+")


def tokenize_for_memory(text: str) -> set[str]:
    tokens = {match.group(0).lower() for match in _TOKEN_RE.finditer(text or "")}
    for match in _CJK_RUN_RE.finditer(text or ""):
        run = match.group(0)
        if len(run) >= 2:
            tokens.update(run[idx : idx + 2] for idx in range(len(run) - 1))
    return tokens


def memory_relevance_score(query: str, *, keywords: str, content: str) -> int:
    query_text = (query or "").strip().lower()
    if not query_text:
        return 0
    score = 0
    for kw in (keywords or "").split(","):
        part = kw.strip().lower()
        if len(part) >= 2 and part in query_text:
            score += 5
    query_tokens = tokenize_for_memory(query)
    if not query_tokens:
        return score
    for field in (keywords, content):
        field_tokens = tokenize_for_memory(field)
        score += len(query_tokens.intersection(field_tokens)) * 3
        lowered = (field or "").lower()
        for token in query_tokens:
            if len(token) >= 2 and token in lowered:
                score += 2
    return score


def memory_embedding_text(*, keywords: str, content: str) -> str:
    kw = (keywords or "").strip()
    body = (content or "").strip()
    if kw and body:
        return f"{kw}\n{body}"
    return kw or body


def rank_memory_candidates(
    query_text: str,
    candidates: list[dict[str, Any]],
    *,
    mode: VectorRetrieveMode | None = None,
) -> list[dict[str, Any]]:
    """为记忆候选打分并降序排序；embedding API 不可用时回落关键词。"""
    query = (query_text or "").strip()
    if not query or not candidates:
        return []

    active_mode = mode or vector_retrieve_mode()
    scored: list[dict[str, Any]] = []
    for item in candidates:
        keywords = str(item.get("keywords") or "")
        content = str(item.get("content") or "")
        kw_score = memory_relevance_score(query, keywords=keywords, content=content)
        row = dict(item)
        row["score"] = kw_score
        scored.append(row)

    if active_mode == "keyword":
        scored.sort(key=lambda item: int(item.get("score") or 0), reverse=True)
        return [item for item in scored if int(item.get("score") or 0) > 0]

    from pallas.product.llm.knowledge.embedding_client import fetch_embeddings_sync
    from pallas.product.llm.knowledge.embedding_score import embedding_relevance_score

    embed_inputs = [query]
    indexed: list[tuple[int, dict[str, Any], int]] = []
    for item in scored:
        text = memory_embedding_text(
            keywords=str(item.get("keywords") or ""),
            content=str(item.get("content") or ""),
        )
        if not text.strip():
            continue
        embed_inputs.append(text)
        indexed.append((len(embed_inputs) - 1, item, int(item.get("score") or 0)))

    vectors = fetch_embeddings_sync(embed_inputs)
    if vectors is None or len(vectors) != len(embed_inputs):
        scored.sort(key=lambda item: int(item.get("score") or 0), reverse=True)
        return [item for item in scored if int(item.get("score") or 0) > 0]

    query_vec = vectors[0]
    for vec_idx, item, kw_score in indexed:
        emb_score = embedding_relevance_score(query_vec, vectors[vec_idx])
        if active_mode == "hybrid":
            item["score"] = blend_hybrid_score(embedding_score=emb_score, keyword_score=kw_score)
        else:
            item["score"] = emb_score

    scored.sort(key=lambda item: int(item.get("score") or 0), reverse=True)
    return [item for item in scored if int(item.get("score") or 0) > 0]

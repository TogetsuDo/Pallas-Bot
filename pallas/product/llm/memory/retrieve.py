"""记忆条目相关性打分（关键词重叠，无 embedding 依赖）。"""

from __future__ import annotations

import re

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

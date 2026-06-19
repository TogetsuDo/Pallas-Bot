"""群梗/教导记忆：PG 存储与检索。"""

from __future__ import annotations

import operator
import time

from sqlalchemy import delete, func, select

from pallas.core.foundation.db.repository_pg import LlmMemoryEntryRow, get_session, is_pg_initialized
from pallas.core.foundation.db.runtime import is_postgresql_backend
from pallas.product.llm.config import LlmConfig, get_llm_config
from pallas.product.llm.memory.policy import classify_memory_candidate, normalize_episode_note
from pallas.product.llm.memory.retrieve import memory_relevance_score
from pallas.product.llm.session_store import normalize_group_scope
from pallas.product.persona.prompt_guard import sanitize_prompt_block, sanitize_prompt_literal


def is_llm_memory_store_available() -> bool:
    cfg = get_llm_config()
    return cfg.llm_memory_rag_enabled and is_postgresql_backend() and is_pg_initialized()


def derive_memory_keywords(content: str, *, max_len: int = 120) -> str:
    from pallas.product.llm.memory.retrieve import tokenize_for_memory

    tokens = sorted(tokenize_for_memory(content), key=len, reverse=True)
    picked: list[str] = []
    total = 0
    for token in tokens:
        if token in picked:
            continue
        if total + len(token) + (1 if picked else 0) > max_len:
            break
        picked.append(token)
        total += len(token) + (1 if picked else 0)
    return ",".join(picked[:12])


def canonicalize_memory_content(content: str) -> str:
    text = (content or "").strip()
    return text.rstrip("。！？!?；;，,、")


def memory_entries_semantically_match(left: str, right: str) -> bool:
    lhs = canonicalize_memory_content(left)
    rhs = canonicalize_memory_content(right)
    return bool(lhs and rhs and lhs == rhs)


async def find_reusable_memory_entry(
    session,
    *,
    bot_id: int,
    group_id: int,
    safe_content: str,
    keywords: str,
) -> LlmMemoryEntryRow | None:
    exact = (
        await session.execute(
            select(LlmMemoryEntryRow).where(
                LlmMemoryEntryRow.bot_id == bot_id,
                LlmMemoryEntryRow.group_id == group_id,
                LlmMemoryEntryRow.content == safe_content,
            )
        )
    ).scalar_one_or_none()
    if exact is not None:
        return exact

    rows = (
        (
            await session.execute(
                select(LlmMemoryEntryRow)
                .where(
                    LlmMemoryEntryRow.bot_id == bot_id,
                    LlmMemoryEntryRow.group_id == group_id,
                )
                .order_by(LlmMemoryEntryRow.updated_at.desc(), LlmMemoryEntryRow.id.desc())
                .limit(32)
            )
        )
        .scalars()
        .all()
    )
    for row in rows:
        if memory_entries_semantically_match(str(row.content or ""), safe_content):
            return row
        row_keywords = str(row.keywords or "")
        row_content = canonicalize_memory_content(str(row.content or ""))
        if keywords and row_keywords and row_keywords == keywords and row_content:
            return row
    return None


async def save_memory_entry(
    bot_id: int,
    group_id: int | None,
    content: str,
    *,
    source: str = "teach",
    cfg: LlmConfig | None = None,
) -> bool:
    if not is_llm_memory_store_available():
        return False
    c = cfg or get_llm_config()
    safe_content = sanitize_prompt_block(content, max_len=c.llm_memory_content_max_len)
    normalized_source = (source or "").strip()
    if (source or "").strip() == "teach":
        normalized_source = classify_memory_candidate(safe_content) or "teach"
        safe_content = normalize_episode_note(safe_content, max_len=c.llm_memory_content_max_len)
    if not safe_content:
        return False
    scope_gid = normalize_group_scope(group_id)
    now = int(time.time())
    keywords = derive_memory_keywords(safe_content)
    async with get_session() as session:
        safe_source = sanitize_prompt_literal(normalized_source, max_len=16) or "teach"
        existing = await find_reusable_memory_entry(
            session,
            bot_id=int(bot_id),
            group_id=scope_gid,
            safe_content=safe_content,
            keywords=keywords,
        )
        if existing is not None:
            existing.keywords = keywords
            existing.content = safe_content
            existing.source = safe_source
            existing.updated_at = now
        else:
            session.add(
                LlmMemoryEntryRow(
                    bot_id=int(bot_id),
                    group_id=scope_gid,
                    keywords=keywords,
                    content=safe_content,
                    source=safe_source,
                    created_at=now,
                    updated_at=now,
                )
            )
            await session.flush()
        await trim_group_memory_entries(
            session,
            bot_id=int(bot_id),
            group_id=scope_gid,
            max_entries=c.llm_memory_max_per_group,
        )
        await session.commit()
    return True


async def trim_group_memory_entries(
    session,
    *,
    bot_id: int,
    group_id: int,
    max_entries: int,
) -> None:
    if max_entries <= 0:
        return
    count = (
        await session.execute(
            select(func.count())
            .select_from(LlmMemoryEntryRow)
            .where(
                LlmMemoryEntryRow.bot_id == bot_id,
                LlmMemoryEntryRow.group_id == group_id,
            )
        )
    ).scalar_one()
    overflow = int(count) - max_entries
    if overflow <= 0:
        return
    stale_ids = (
        (
            await session.execute(
                select(LlmMemoryEntryRow.id)
                .where(
                    LlmMemoryEntryRow.bot_id == bot_id,
                    LlmMemoryEntryRow.group_id == group_id,
                )
                .order_by(LlmMemoryEntryRow.updated_at.asc(), LlmMemoryEntryRow.id.asc())
                .limit(overflow)
            )
        )
        .scalars()
        .all()
    )
    if stale_ids:
        await session.execute(delete(LlmMemoryEntryRow).where(LlmMemoryEntryRow.id.in_(stale_ids)))


async def retrieve_memory_entries(
    bot_id: int,
    group_id: int | None,
    query_text: str,
    *,
    cfg: LlmConfig | None = None,
) -> list[str]:
    if not is_llm_memory_store_available():
        return []
    c = cfg or get_llm_config()
    scope_gid = normalize_group_scope(group_id)
    top_k = max(1, min(int(c.llm_memory_rag_top_k), 8))
    async with get_session(read_only=True) as session:
        rows = (
            (
                await session.execute(
                    select(LlmMemoryEntryRow)
                    .where(
                        LlmMemoryEntryRow.bot_id == int(bot_id),
                        LlmMemoryEntryRow.group_id.in_([scope_gid, 0]),
                    )
                    .order_by(LlmMemoryEntryRow.updated_at.desc(), LlmMemoryEntryRow.id.desc())
                    .limit(max(50, top_k * 10))
                )
            )
            .scalars()
            .all()
        )
    scored: list[tuple[int, str]] = []
    for row in rows:
        score = memory_relevance_score(
            query_text,
            keywords=str(row.keywords or ""),
            content=str(row.content or ""),
        )
        if score <= 0:
            continue
        scored.append((score, str(row.content or "").strip()))
    scored.sort(key=operator.itemgetter(0), reverse=True)
    seen: set[str] = set()
    out: list[str] = []
    for _, content in scored:
        if not content or content in seen:
            continue
        seen.add(content)
        out.append(content)
        if len(out) >= min(top_k, 3):
            break
    return out

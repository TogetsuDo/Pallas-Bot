"""学习写入后异步 mirror 到联邦 / 社区语料源。"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from nonebot import logger

from src.features.corpus.config import CorpusConfig, community_contribute_enabled

if TYPE_CHECKING:
    from src.foundation.db.modules import Context
    from src.foundation.db.repository import ContextRepository


def schedule_corpus_write(task: asyncio.Task[Any]) -> None:
    def done_cb(fut: asyncio.Task[Any]) -> None:
        try:
            fut.result()
        except asyncio.CancelledError:
            return
        except Exception as e:
            logger.warning(f"corpus mirror failed: {e}")

    task.add_done_callback(done_cb)


async def mirror_upsert_answer(
    *,
    fed: ContextRepository | None,
    community: ContextRepository | None,
    cfg: CorpusConfig,
    keywords: str,
    group_id: int,
    answer_keywords: str,
    answer_time: int,
    message: str,
    append_on_existing: bool,
) -> None:
    if cfg.fed_contribute and fed is not None:
        await fed.upsert_answer(
            keywords=keywords,
            group_id=group_id,
            answer_keywords=answer_keywords,
            answer_time=answer_time,
            message=message,
            append_on_existing=append_on_existing,
        )
    if community_contribute_enabled(cfg) and community is not None:
        await community.upsert_answer(
            keywords=keywords,
            group_id=0,
            answer_keywords=answer_keywords,
            answer_time=answer_time,
            message=message,
            append_on_existing=append_on_existing,
        )


async def mirror_insert(
    *,
    fed: ContextRepository | None,
    community: ContextRepository | None,
    cfg: CorpusConfig,
    context: Context,
) -> None:
    if cfg.fed_contribute and fed is not None:
        await fed.insert(context)
    if community_contribute_enabled(cfg) and community is not None:
        await community.insert(context)


def schedule_mirror_upsert_answer(
    *,
    fed: ContextRepository | None,
    community: ContextRepository | None,
    cfg: CorpusConfig,
    keywords: str,
    group_id: int,
    answer_keywords: str,
    answer_time: int,
    message: str,
    append_on_existing: bool,
) -> None:
    if not cfg.fed_contribute and not community_contribute_enabled(cfg):
        return
    from src.foundation.db.pool_budget import pg_pool_under_pressure

    if pg_pool_under_pressure(threshold=0.78):
        from src.foundation.db.pool_diagnostics import note_mirror_skipped_pressure

        note_mirror_skipped_pressure()
        return
    task = asyncio.create_task(
        mirror_upsert_answer(
            fed=fed,
            community=community,
            cfg=cfg,
            keywords=keywords,
            group_id=group_id,
            answer_keywords=answer_keywords,
            answer_time=answer_time,
            message=message,
            append_on_existing=append_on_existing,
        )
    )
    schedule_corpus_write(task)


def schedule_mirror_insert(
    *,
    fed: ContextRepository | None,
    community: ContextRepository | None,
    cfg: CorpusConfig,
    context: Context,
) -> None:
    if not cfg.fed_contribute and not community_contribute_enabled(cfg):
        return
    from src.foundation.db.pool_budget import pg_pool_under_pressure

    if pg_pool_under_pressure(threshold=0.78):
        from src.foundation.db.pool_diagnostics import note_mirror_skipped_pressure

        note_mirror_skipped_pressure()
        return
    task = asyncio.create_task(
        mirror_insert(
            fed=fed,
            community=community,
            cfg=cfg,
            context=context,
        )
    )
    schedule_corpus_write(task)

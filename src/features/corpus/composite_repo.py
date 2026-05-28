"""多读源 ContextRepository：local + 可选 fed / community。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nonebot import logger

from src.features.corpus.config import CorpusConfig, get_corpus_config, remote_corpus_find_enabled
from src.features.corpus.merge import merge_contexts
from src.features.corpus.write_fanout import schedule_mirror_insert, schedule_mirror_upsert_answer

if TYPE_CHECKING:
    from src.foundation.db.modules import Answer, Ban, Context
    from src.foundation.db.repository import ContextRepository


class CompositeContextRepository:
    """多读源 merge；写路由 local + 可选异步 mirror。"""

    def __init__(
        self,
        local: ContextRepository,
        *,
        fed: ContextRepository | None = None,
        community: ContextRepository | None = None,
        cfg: CorpusConfig | None = None,
    ) -> None:
        self._local = local
        self._fed = fed
        self._community = community
        self._cfg = cfg or get_corpus_config()

    def _repo_for(self, source_id: str) -> ContextRepository | None:
        if source_id == "local":
            return self._local
        if source_id == "fed":
            return self._fed
        if source_id == "community":
            return self._community
        return None

    async def find_by_keywords(self, keywords: str) -> Context | None:
        from src.features.corpus.find_cache import cached_find_by_keywords

        return await cached_find_by_keywords(keywords, self._find_by_keywords_merged)

    async def _find_by_keywords_merged(self, keywords: str) -> Context | None:
        merged: Context | None = None
        remote_find = remote_corpus_find_enabled(self._cfg)
        for source_id in self._cfg.merge_order:
            if not remote_find and source_id != "local":
                continue
            repo = self._repo_for(source_id)
            if repo is None:
                continue
            try:
                ctx = await repo.find_by_keywords(keywords)
            except Exception as e:
                if source_id != "local" and self._cfg.on_remote_failure == "local_only":
                    logger.warning(f"corpus {source_id} find_by_keywords failed: {e}")
                    continue
                raise
            merged = merge_contexts(merged, ctx, strategy=self._cfg.merge_strategy)
        return merged

    async def context_exists_by_keywords(self, keywords: str) -> bool:
        if await self._local.context_exists_by_keywords(keywords):
            return True
        if not remote_corpus_find_enabled(self._cfg):
            return False
        for source_id in ("fed", "community"):
            repo = self._repo_for(source_id)
            if repo is None:
                continue
            try:
                if await repo.context_exists_by_keywords(keywords):
                    return True
            except Exception as e:
                if self._cfg.on_remote_failure == "local_only":
                    logger.warning(f"corpus {source_id} context_exists failed: {e}")
                    continue
                raise
        return False

    async def save(self, context: Context) -> None:
        await self._local.save(context)

    async def insert(self, context: Context) -> None:
        await self._local.insert(context)
        from src.features.corpus.find_cache import invalidate_find_cache

        await invalidate_find_cache(context.keywords)
        schedule_mirror_insert(fed=self._fed, community=self._community, cfg=self._cfg, context=context)

    async def delete_expired(self, expiration: int, threshold: int) -> None:
        await self._local.delete_expired(expiration, threshold)

    async def find_for_cleanup(self, trigger_threshold: int, expiration: int) -> list[Context]:
        return await self._local.find_for_cleanup(trigger_threshold, expiration)

    async def upsert_answer(
        self,
        keywords: str,
        group_id: int,
        answer_keywords: str,
        answer_time: int,
        message: str,
        append_on_existing: bool,
    ) -> None:
        await self._local.upsert_answer(
            keywords=keywords,
            group_id=group_id,
            answer_keywords=answer_keywords,
            answer_time=answer_time,
            message=message,
            append_on_existing=append_on_existing,
        )
        from src.features.corpus.find_cache import invalidate_find_cache

        await invalidate_find_cache(keywords)
        schedule_mirror_upsert_answer(
            fed=self._fed,
            community=self._community,
            cfg=self._cfg,
            keywords=keywords,
            group_id=group_id,
            answer_keywords=answer_keywords,
            answer_time=answer_time,
            message=message,
            append_on_existing=append_on_existing,
        )

    async def replace_answers(self, keywords: str, answers: list[Answer], clear_time: int) -> None:
        await self._local.replace_answers(keywords, answers, clear_time)

    async def append_ban(self, keywords: str, ban: Ban) -> None:
        await self._local.append_ban(keywords, ban)

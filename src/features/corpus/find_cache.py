"""find_by_keywords 进程内 TTL 缓存（含负缓存），减轻复读热路径远程 HTTP。"""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING

from src.features.corpus.reply_perf_config import find_cache_max_entries, find_cache_ttl_sec

if TYPE_CHECKING:
    from src.foundation.db.modules import Context

_find_cache: dict[str, tuple[float, Context | None]] = {}
_find_lock = asyncio.Lock()


async def cached_find_by_keywords(
    keywords: str,
    loader,
) -> Context | None:
    key = (keywords or "").strip()
    if not key:
        return None
    now = time.monotonic()
    async with _find_lock:
        hit = _find_cache.get(key)
        if hit is not None:
            exp, val = hit
            if now < exp:
                return val
            _find_cache.pop(key, None)
        cache_max = find_cache_max_entries()
        if len(_find_cache) > cache_max:
            stale = [k for k, (e, _) in _find_cache.items() if now >= e]
            for k in stale:
                _find_cache.pop(k, None)
            if len(_find_cache) > cache_max:
                _find_cache.clear()

    ctx = await loader(key)

    expire_at = time.monotonic() + find_cache_ttl_sec()
    async with _find_lock:
        _find_cache[key] = (expire_at, ctx)
    return ctx


async def invalidate_find_cache(keywords: str | None = None) -> None:
    async with _find_lock:
        if keywords is None:
            _find_cache.clear()
            return
        key = keywords.strip()
        if key:
            _find_cache.pop(key, None)


async def reset_find_cache_for_tests() -> None:
    await invalidate_find_cache(None)

"""find_by_keywords 进程内 TTL 缓存（含负缓存），减轻复读热路径远程 HTTP。"""

from __future__ import annotations

import asyncio
import os
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.foundation.db.modules import Context

_FIND_CACHE_TTL_SEC = float(os.getenv("PALLAS_CORPUS_FIND_CACHE_SEC", "45"))
_FIND_CACHE_MAX = int(os.getenv("PALLAS_CORPUS_FIND_CACHE_MAX", "50000"))
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
        if len(_find_cache) > _FIND_CACHE_MAX:
            stale = [k for k, (e, _) in _find_cache.items() if now >= e]
            for k in stale:
                _find_cache.pop(k, None)
            if len(_find_cache) > _FIND_CACHE_MAX:
                _find_cache.clear()

    ctx = await loader(key)

    expire_at = time.monotonic() + _FIND_CACHE_TTL_SEC
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

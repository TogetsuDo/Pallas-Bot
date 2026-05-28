from __future__ import annotations

import pytest

from src.features.corpus.find_cache import cached_find_by_keywords, reset_find_cache_for_tests


@pytest.mark.asyncio
async def test_find_cache_hits_without_second_loader_call():
    await reset_find_cache_for_tests()
    calls = 0

    async def loader(keywords: str):
        nonlocal calls
        calls += 1
        return {"kw": keywords} if keywords == "hello" else None

    assert await cached_find_by_keywords("hello", loader) == {"kw": "hello"}
    assert await cached_find_by_keywords("hello", loader) == {"kw": "hello"}
    assert calls == 1

    assert await cached_find_by_keywords("missing", loader) is None
    assert await cached_find_by_keywords("missing", loader) is None
    assert calls == 2

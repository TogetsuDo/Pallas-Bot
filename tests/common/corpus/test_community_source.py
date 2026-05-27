from unittest.mock import MagicMock, patch

import httpx
import pytest

from src.features.community_stats.endpoints import FALLBACK_CORPUS_API_BASE, PRIMARY_CORPUS_API_BASE
from src.features.corpus.community_source import RemoteCorpusRepository


@pytest.mark.asyncio
async def test_find_by_keywords_failover_to_fallback():
    calls: list[str] = []

    async def fake_get(self, url, **kwargs):
        calls.append(url)
        if url.startswith(PRIMARY_CORPUS_API_BASE):
            raise httpx.ConnectError("name or service not known", request=MagicMock())
        mock = MagicMock()
        mock.status_code = 200
        mock.json.return_value = {
            "keywords": "test",
            "time": 1,
            "trigger_count": 1,
            "answers": [],
            "ban": [],
            "clear_time": 0,
        }
        return mock

    repo = RemoteCorpusRepository(
        api_bases=[PRIMARY_CORPUS_API_BASE, FALLBACK_CORPUS_API_BASE],
        token="pc_test",
    )
    with patch.object(httpx.AsyncClient, "get", fake_get):
        ctx = await repo.find_by_keywords("test")
    assert ctx is not None
    assert ctx.keywords == "test"
    assert calls[0] == f"{PRIMARY_CORPUS_API_BASE}/context"
    assert calls[1] == f"{FALLBACK_CORPUS_API_BASE}/context"


@pytest.mark.asyncio
async def test_find_by_keywords_all_bases_fail_raises():
    repo = RemoteCorpusRepository(
        api_bases=[PRIMARY_CORPUS_API_BASE, FALLBACK_CORPUS_API_BASE],
        token="pc_test",
    )

    async def fake_get(self, url, **kwargs):
        raise httpx.ConnectError("down", request=MagicMock())

    with patch.object(httpx.AsyncClient, "get", fake_get):
        with pytest.raises(httpx.ConnectError):
            await repo.find_by_keywords("test")

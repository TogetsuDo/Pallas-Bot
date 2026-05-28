from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from src.features.corpus.composite_repo import CompositeContextRepository
from src.features.corpus.config import CorpusConfig, remote_corpus_find_enabled


def test_remote_find_auto_defaults_off(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.features.corpus.config.setting_str",
        lambda name, default="": default,
    )
    from src.features.corpus.config import clear_corpus_config_cache

    clear_corpus_config_cache()
    assert remote_corpus_find_enabled() is False


def test_remote_find_disabled_by_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.features.corpus.config.setting_str",
        lambda name, default="": "false" if name == "PALLAS_CORPUS_REMOTE_FIND_ENABLED" else default,
    )
    from src.features.corpus.config import clear_corpus_config_cache

    clear_corpus_config_cache()
    assert remote_corpus_find_enabled() is False


@pytest.mark.asyncio
async def test_composite_skips_remote_find_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.features.corpus.find_cache import reset_find_cache_for_tests

    await reset_find_cache_for_tests()
    local = AsyncMock()
    local.find_by_keywords = AsyncMock(return_value=None)
    community = AsyncMock()
    community.find_by_keywords = AsyncMock(return_value=None)
    cfg = CorpusConfig(merge_order=["local", "community"], merge_strategy="local_first")
    repo = CompositeContextRepository(local, community=community, cfg=cfg)

    async def always_remote() -> bool:
        return False

    import src.features.corpus.composite_repo as mod

    monkeypatch.setattr(mod, "remote_corpus_find_enabled", lambda _cfg=None: False)
    try:
        assert await repo.find_by_keywords("kw") is None
        community.find_by_keywords.assert_not_called()
    finally:
        monkeypatch.undo()

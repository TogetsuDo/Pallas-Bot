import pytest

from src.features.corpus.remote_budget import (
    RemoteCorpusBudget,
    clear_remote_corpus_budget_state,
    should_skip_remote_corpus,
)


@pytest.mark.asyncio
async def test_remote_corpus_budget_skips_under_pressure(monkeypatch):
    clear_remote_corpus_budget_state()
    monkeypatch.setattr(
        "src.features.corpus.remote_budget.pg_pool_under_pressure",
        lambda threshold=0.75: True,
    )
    assert should_skip_remote_corpus(hot_path=True) is True
    async with RemoteCorpusBudget(hot_path=True) as budget:
        assert budget.skipped is True


@pytest.mark.asyncio
async def test_remote_corpus_budget_acquires_when_healthy(monkeypatch):
    clear_remote_corpus_budget_state()
    monkeypatch.setattr(
        "src.features.corpus.remote_budget.pg_pool_under_pressure",
        lambda threshold=0.75: False,
    )
    monkeypatch.setattr(
        "src.features.corpus.remote_budget.remote_corpus_concurrency_limit",
        lambda: 2,
    )
    async with RemoteCorpusBudget(hot_path=False, wait=True) as budget:
        assert budget.skipped is False

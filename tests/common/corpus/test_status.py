from __future__ import annotations

import pytest

from src.common.features.corpus.status import build_corpus_status_snapshot


async def _mock_no_usage():
    return None


@pytest.mark.asyncio
async def test_build_corpus_status_snapshot_shape(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "src.common.features.corpus.usage.fetch_corpus_community_usage",
        _mock_no_usage,
    )
    monkeypatch.setattr(
        "src.common.features.corpus.status.load_corpus_community_state",
        lambda: {
            "api_base": "https://stats.example/v1/corpus",
            "corpus_token": "pc_test",
            "contribute": False,
            "enrolled_at": 1_700_000_000,
        },
    )
    monkeypatch.setattr("src.common.features.corpus.status.corpus_community_enrollment_valid", lambda _state=None: True)
    monkeypatch.setattr("src.common.features.corpus.status.community_manual_configured", lambda: False)
    monkeypatch.setattr("src.common.features.corpus.status.fed_configured", lambda: False)
    monkeypatch.setattr(
        "src.common.features.corpus.config.repo_env_raw_value",
        lambda name: "auto" if name.startswith("PALLAS_CORPUS_") else None,
    )
    from src.common.features.corpus.config import clear_corpus_config_cache

    clear_corpus_config_cache()
    snap = await build_corpus_status_snapshot()
    assert snap["composite_active"] is True
    assert snap["sources"]["local"]["enabled"] is True
    assert snap["sources"]["community"]["enrolled"] is True
    assert snap["sources"]["community"]["contribute"] is False
    assert snap["sources"]["community"]["token_present"] is True
    assert snap["sources"]["community"]["usage"] is None
    assert "deployment_id" in snap["deployment"]

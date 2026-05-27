"""deploy_profile 与 apply_deploy_profile 工具。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.foundation.deploy_profile import (
    clear_deploy_profile_cache,
    is_deploy_profile_active,
    message_scrub_webui_available,
    read_profile_env_fragment,
    record_deploy_profile,
    uv_sync_hint_for_profile,
)


@pytest.fixture(autouse=True)
def reset_deploy_marker(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    marker = tmp_path / "deploy_profiles.json"
    monkeypatch.setattr(
        "src.foundation.deploy_profile.DEPLOY_MARKER_PATH",
        marker,
    )
    clear_deploy_profile_cache()
    yield
    clear_deploy_profile_cache()


def test_read_message_scrub_fragment_has_enabled() -> None:
    env = read_profile_env_fragment("message-scrub")
    assert env.get("PALLAS_MESSAGE_SCRUB_ENABLED") == "true"


def test_record_deploy_profile_merges(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    marker = tmp_path / "deploy_profiles.json"
    monkeypatch.setattr("src.foundation.deploy_profile.DEPLOY_MARKER_PATH", marker)
    clear_deploy_profile_cache()
    record_deploy_profile("message-scrub")
    record_deploy_profile("shard")
    clear_deploy_profile_cache()
    assert is_deploy_profile_active("message-scrub")
    assert is_deploy_profile_active("shard")
    data = json.loads(marker.read_text(encoding="utf-8"))
    assert "message-scrub" in data["extras"] or "deploy-shard" in data["extras"]


def test_uv_sync_hint_shard() -> None:
    assert "deploy-shard" in uv_sync_hint_for_profile("shard")


def test_message_scrub_webui_hidden_by_default(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    keys = [
        "PALLAS_MESSAGE_SCRUB_ENABLED",
        "PALLAS_INBOUND_FILTER_SUBSTRINGS",
        "PALLAS_SCRUB_LEXICON_PATH",
        "PALLAS_SCRUB_LEXICON_EXTRA",
        "PALLAS_SCRUB_API_URL",
        "PALLAS_SCRUB_BAIDU_API_KEY",
        "PALLAS_SCRUB_BAIDU_SECRET_KEY",
    ]
    for k in keys:
        monkeypatch.delenv(k, raising=False)
    phantom = tmp_path / "missing.toml"
    with monkeypatch.context() as mp:
        mp.setattr(
            "src.foundation.config.repo_settings.repo_env_path",
            lambda: phantom,
        )
        mp.setattr(
            "src.foundation.config.repo_settings.repo_config_path",
            lambda: phantom,
        )
        mp.setattr(
            "src.foundation.config.repo_settings.repo_webui_settings_path",
            lambda: tmp_path / "missing.json",
        )
        mp.setattr(
            "src.foundation.config.dotenv.merged_repo_dotenv_upper",
            lambda: {},
        )
        mp.setattr(
            "src.foundation.config.dotenv.repo_layered_dotenv_files_exist",
            lambda: True,
        )
        from src.features.message_scrub import reload_message_scrub_caches

        reload_message_scrub_caches()
        clear_deploy_profile_cache()
        assert message_scrub_webui_available() is False


def test_message_scrub_webui_with_profile(monkeypatch: pytest.MonkeyPatch) -> None:
    record_deploy_profile("message-scrub")
    assert message_scrub_webui_available() is True

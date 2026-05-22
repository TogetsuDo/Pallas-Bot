import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.common.community_stats import config as cfg_mod
from src.common.community_stats.reporter import (
    build_heartbeat_payload,
    send_community_stats_heartbeat,
    should_run_community_stats_reporter,
)
from src.common.community_stats.public_stats import _parse_stats_body
from src.common.community_stats.stats_url import stats_url_from_endpoint
from src.common.community_stats.store import community_stats_state_path, load_or_create_deployment_id


@pytest.fixture(autouse=True)
def clear_config_cache():
    cfg_mod.clear_community_stats_config_cache()
    yield
    cfg_mod.clear_community_stats_config_cache()


def test_stats_url_from_heartbeat_endpoint():
    assert (
        stats_url_from_endpoint("https://stats.pallasbot.top/v1/heartbeat")
        == "https://stats.pallasbot.top/v1/stats"
    )
    assert stats_url_from_endpoint("") == "https://stats.pallasbot.top/v1/stats"


def test_parse_stats_body():
    data = _parse_stats_body(
        {
            "deployments_total": 10,
            "deployments_online": 3,
            "bots_online_sum": 7,
            "online_ttl_sec": 900,
            "as_of": "2026-05-22T12:00:00Z",
        },
        "https://stats.example/v1/stats",
    )
    assert data["deployments_total"] == 10
    assert data["online_ttl_sec"] == 900


def test_config_enabled_default_true(monkeypatch):
    monkeypatch.delenv("PALLAS_COMMUNITY_STATS_ENABLED", raising=False)
    with patch("src.common.community_stats.config.repo_env_raw_value", return_value=None):
        cfg_mod.clear_community_stats_config_cache()
        assert cfg_mod.get_community_stats_config().enabled is True


def test_config_enabled_from_toml_without_section(tmp_path, monkeypatch):
    cfg = tmp_path / "pallas.toml"
    cfg.write_text('[bootstrap]\nhost = "127.0.0.1"\nport = 8080\n', encoding="utf-8")
    monkeypatch.delenv("PALLAS_COMMUNITY_STATS_ENABLED", raising=False)
    from src.common.config import repo_settings as rs

    monkeypatch.setattr(rs, "repo_config_path", lambda: cfg)
    monkeypatch.setattr(rs, "repo_webui_settings_path", lambda: tmp_path / "missing.json")
    monkeypatch.setattr(rs, "repo_env_path", lambda: tmp_path / "missing.env")
    monkeypatch.setattr(rs, "_REPO_ROOT", tmp_path)
    cfg_mod.clear_community_stats_config_cache()
    assert cfg_mod.get_community_stats_config().enabled is True


def test_config_disabled_from_toml(tmp_path, monkeypatch):
    cfg = tmp_path / "pallas.toml"
    cfg.write_text("[community_stats]\nenabled = false\n", encoding="utf-8")
    monkeypatch.delenv("PALLAS_COMMUNITY_STATS_ENABLED", raising=False)
    from src.common.config import repo_settings as rs

    monkeypatch.setattr(rs, "repo_config_path", lambda: cfg)
    monkeypatch.setattr(rs, "repo_webui_settings_path", lambda: tmp_path / "missing.json")
    monkeypatch.setattr(rs, "repo_env_path", lambda: tmp_path / "missing.env")
    monkeypatch.setattr(rs, "_REPO_ROOT", tmp_path)
    cfg_mod.clear_community_stats_config_cache()
    assert cfg_mod.get_community_stats_config().enabled is False


def test_config_can_disable(monkeypatch):
    monkeypatch.setenv("PALLAS_COMMUNITY_STATS_ENABLED", "false")
    cfg_mod.clear_community_stats_config_cache()
    assert cfg_mod.get_community_stats_config().enabled is False


def test_deployment_id_persisted(tmp_path, monkeypatch):
    path = tmp_path / "pallas_config" / "community_stats.json"
    monkeypatch.setattr(
        "src.common.community_stats.store.community_stats_state_path",
        lambda: path,
    )
    a = load_or_create_deployment_id()
    b = load_or_create_deployment_id()
    assert a == b
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["deployment_id"] == a


def test_should_not_run_on_worker(monkeypatch):
    monkeypatch.setenv("PALLAS_COMMUNITY_STATS_ENABLED", "true")
    cfg_mod.clear_community_stats_config_cache()
    with patch("src.common.community_stats.reporter.is_sharded_worker", return_value=True):
        assert should_run_community_stats_reporter() is False


@pytest.mark.asyncio
async def test_send_heartbeat_success(monkeypatch):
    monkeypatch.setenv("PALLAS_COMMUNITY_STATS_ENDPOINT", "https://stats.example/v1/heartbeat")
    monkeypatch.setenv("PALLAS_COMMUNITY_STATS_TOKEN", "secret")
    cfg_mod.clear_community_stats_config_cache()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = '{"ok":true}'

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_resp)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with (
        patch(
            "src.common.community_stats.store.community_stats_state_path",
            return_value=community_stats_state_path(),
        ),
        patch(
            "src.common.community_stats.reporter.load_or_create_deployment_id",
            return_value="550e8400-e29b-41d4-a716-446655440000",
        ),
        patch("src.common.community_stats.reporter.is_sharding_active", return_value=False),
        patch("src.common.community_stats.reporter.get_bots", return_value={"1": object()}),
        patch("src.common.community_stats.reporter.get_fleet_bot_ids", return_value=frozenset({1, 2})),
        patch("src.common.community_stats.reporter.httpx.AsyncClient", return_value=mock_client),
    ):
        assert await send_community_stats_heartbeat() is True
        mock_client.post.assert_awaited_once()
        _args, kwargs = mock_client.post.await_args
        assert kwargs["headers"]["Authorization"] == "Bearer secret"
        assert kwargs["json"]["online_bots"] == 1
        assert kwargs["json"]["catalog_bots"] == 2


def test_build_payload_sharded():
    shard = MagicMock()
    shard.id = 0
    with (
        patch("src.common.community_stats.reporter.is_sharding_active", return_value=True),
        patch(
            "src.common.shard.presence.get_cluster_online_bot_ids",
            return_value=frozenset({111, 222}),
        ),
        patch("src.common.community_stats.reporter.get_fleet_bot_ids", return_value=frozenset({111, 222, 333})),
        patch("src.common.community_stats.reporter.get_shard_registry") as mock_reg,
        patch("src.common.community_stats.reporter.is_test_shard_record", return_value=False),
        patch(
            "src.common.community_stats.reporter.load_or_create_deployment_id",
            return_value="550e8400-e29b-41d4-a716-446655440000",
        ),
    ):
        mock_reg.return_value.shards = [shard, shard]
        payload = build_heartbeat_payload()
        assert payload["sharded"] is True
        assert payload["online_bots"] == 2
        assert payload["catalog_bots"] == 3
        assert payload["shard_workers"] == 2

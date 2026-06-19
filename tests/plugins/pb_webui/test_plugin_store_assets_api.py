from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from packages.pb_webui import extended_api as mod
from packages.pb_webui.config import Config


def _build_client(monkeypatch) -> TestClient:
    monkeypatch.setattr(mod, "_check_pallas_write_token", lambda *a, **k: None)
    monkeypatch.setattr(mod, "_require_pallas_token_configured", lambda *a, **k: None)
    monkeypatch.setattr(mod, "ensure_console_metrics_hooks", lambda: None)
    app = FastAPI()
    mod.register_extended_api(app, api_base="/pallas/api", plugin_config=Config())
    return TestClient(app)


def test_plugin_store_readme_returns_cached_markdown(monkeypatch) -> None:
    monkeypatch.setattr(
        "pallas.console.webui.plugin_store_assets.get_cached_readme_markdown",
        lambda kind, target_id: "# Draw\n" if kind == "official" and target_id == "pallas-plugin-draw" else None,
    )

    client = _build_client(monkeypatch)
    response = client.get("/pallas/api/plugins/store/readme", params={"kind": "official", "id": "pallas-plugin-draw"})

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["ok"] is True
    assert payload["data"]["markdown"] == "# Draw\n"


def test_plugin_store_assets_refresh_returns_counts(monkeypatch) -> None:
    async def fake_refresh() -> dict:
        return {
            "checked_at": 123.0,
            "official": {"pallas-plugin-draw": {}},
            "community": {"draw": {}, "duel": {}},
        }

    monkeypatch.setattr("pallas.console.webui.plugin_store_assets.refresh_store_asset_snapshot", fake_refresh)
    monkeypatch.setattr(mod, "drop_read_cache", lambda *a, **k: None)

    client = _build_client(monkeypatch)
    response = client.post("/pallas/api/plugins/store-assets/refresh")

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["ok"] is True
    assert payload["data"]["checked_at"] == 123.0
    assert payload["data"]["official_count"] == 1
    assert payload["data"]["community_count"] == 2

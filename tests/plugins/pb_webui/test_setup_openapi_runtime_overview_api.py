from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from packages.pb_webui import api as api_mod
from packages.pb_webui import extended_api as mod
from packages.pb_webui.config import Config
from tools.export_pb_webui_openapi import export_console_openapi


def _build_client(monkeypatch) -> TestClient:
    monkeypatch.setattr(mod, "_check_pallas_write_token", lambda *a, **k: None)
    monkeypatch.setattr(mod, "_require_pallas_token_configured", lambda *a, **k: None)
    monkeypatch.setattr(mod, "ensure_console_metrics_hooks", lambda: None)
    app = FastAPI()
    mod.register_extended_api(app, api_base="/pallas/api", plugin_config=Config())
    return TestClient(app)


def test_auth_setup_status_public(monkeypatch) -> None:
    monkeypatch.setattr(
        mod,
        "console_setup_status",
        lambda: {
            "auth_configured": True,
            "setup_completed": False,
            "default_password_active": True,
            "requires_setup": True,
            "first_completed_at": None,
            "updated_at": None,
        },
    )
    client = _build_client(monkeypatch)
    response = client.get("/pallas/api/auth/setup-status")
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["ok"] is True
    assert payload["data"]["requires_setup"] is True
    assert payload["data"]["default_password_active"] is True


def test_console_openapi_json_filters_non_console_routes(monkeypatch) -> None:
    monkeypatch.setattr(mod, "ensure_console_metrics_hooks", lambda: None)
    app = FastAPI()

    @app.get("/hello")
    async def _hello() -> dict[str, str]:
        return {"ok": "yes"}

    api_mod.register_api(app, api_base="/pallas/api")
    mod.register_extended_api(app, api_base="/pallas/api", plugin_config=Config())
    client = TestClient(app)

    response = client.get("/pallas/api/openapi.json")
    assert response.status_code == 200, response.text
    payload = response.json()
    assert "/pallas/api/health" in payload["paths"]
    assert "/pallas/api/system" in payload["paths"]
    assert "/hello" not in payload["paths"]
    assert "/pallas/api/openapi.json" not in payload["paths"]
    assert payload["servers"] == [{"url": "/pallas/api"}]


def test_export_console_openapi_matches_console_prefix(monkeypatch) -> None:
    monkeypatch.setattr(mod, "ensure_console_metrics_hooks", lambda: None)
    payload = export_console_openapi(api_base="/pallas/api")
    assert "/pallas/api/health" in payload["paths"]
    assert "/pallas/api/system" in payload["paths"]
    assert all(path.startswith("/pallas/api/") for path in payload["paths"])
    assert payload["servers"] == [{"url": "/pallas/api"}]

    setup_schema = payload["paths"]["/pallas/api/auth/setup-status"]["get"]["responses"]["200"]["content"][
        "application/json"
    ]["schema"]
    gateways_schema = payload["paths"]["/pallas/api/common-config/service_gateways/connectivity-check"]["post"][
        "responses"
    ]["200"]["content"]["application/json"]["schema"]
    providers_schema = payload["paths"]["/pallas/api/common-config/llm/providers"]["get"]["responses"]["200"][
        "content"
    ]["application/json"]["schema"]
    provider_test_schema = payload["paths"]["/pallas/api/common-config/llm/providers/{provider_id}/test"]["post"][
        "responses"
    ]["200"]["content"]["application/json"]["schema"]
    runtime_schema = payload["paths"]["/pallas/api/common-config/llm/runtime-overview"]["get"]["responses"]["200"][
        "content"
    ]["application/json"]["schema"]
    wizard_schema = payload["paths"]["/pallas/api/common-config/llm/wizard/status"]["get"]["responses"]["200"][
        "content"
    ]["application/json"]["schema"]
    extension_test_schema = payload["paths"]["/pallas/api/ai-extension/test"]["post"]["responses"]["200"]["content"][
        "application/json"
    ]["schema"]
    password_schema = payload["paths"]["/pallas/api/security/console-login"]["post"]["responses"]["200"]["content"][
        "application/json"
    ]["schema"]

    assert setup_schema["$ref"].endswith("_ApiOkResponse__ConsoleSetupStatusData_")
    assert gateways_schema["$ref"].endswith("_ApiOkResponse__ServiceGatewaysConnectivityCheckData_")
    assert providers_schema["$ref"].endswith("_ApiOkResponse__LlmProvidersConfigData_")
    assert provider_test_schema["$ref"].endswith("_ApiOkResponse__LlmProviderTestData_")
    assert runtime_schema["$ref"].endswith("_ApiOkResponse__LlmRuntimeOverviewData_")
    assert wizard_schema["$ref"].endswith("_ApiOkResponse__LlmWizardStatusData_")
    assert extension_test_schema["$ref"].endswith("_ApiOkResponse__AiExtensionTestData_")
    assert password_schema["$ref"].endswith("_ApiOkResponse__ConsoleLoginChangeData_")


def test_llm_runtime_overview_returns_aggregated_fields(monkeypatch) -> None:
    async def fake_health(*, timeout_sec: float = 0.0):
        _ = timeout_sec
        return {
            "ok": True,
            "url": "http://127.0.0.1:9099/health",
            "status_code": 200,
            "error": "",
            "body": {
                "llm": {
                    "provider_mode": "hybrid",
                    "health_state": "healthy",
                    "degraded_state": "normal",
                    "provider_status": [
                        {
                            "id": "local",
                            "kind": "local",
                            "enabled": True,
                            "configured": True,
                            "reachable": True,
                            "health_state": "healthy",
                            "circuit_state": "closed",
                        }
                    ],
                },
                "image": {
                    "health_state": "healthy",
                    "degraded_state": "normal",
                    "backends": [{"circuit_state": "closed", "consecutive_failures": 0}],
                },
                "tts": {
                    "capability": "tts",
                    "health_state": "healthy",
                    "degraded_state": "normal",
                    "circuit_state": "closed",
                    "celery_enabled": False,
                },
                "media_tasks": {
                    "queue_depth": 1,
                    "active_tasks": 2,
                    "total_tasks": 3,
                    "health_state": "healthy",
                },
            },
        }

    async def fake_model_admin(*, timeout_sec: float = 0.0):
        _ = timeout_sec
        return {"model": "qwen", "ai_reachable": True, "provider_mode": "hybrid", "error": ""}

    async def fake_task_stats(*, timeout_sec: float = 0.0):
        _ = timeout_sec
        return {"bot": {"day_key": "2026-06-24"}, "ai": {}, "ai_reachable": True}

    monkeypatch.setattr("pallas.product.llm.startup_probe.probe_ai_service_health", fake_health)
    monkeypatch.setattr("pallas.product.llm.model_admin.fetch_model_admin_status", fake_model_admin)
    monkeypatch.setattr("pallas.product.llm.model_admin.fetch_llm_task_stats", fake_task_stats)
    monkeypatch.setattr(
        mod,
        "build_conversation_kernel_status",
        lambda: {"feature_level": "full_conversation_kernel"},
    )

    client = _build_client(monkeypatch)
    response = client.get("/pallas/api/common-config/llm/runtime-overview")

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["ok"] is True
    data = payload["data"]
    assert data["health"]["ok"] is True
    assert data["health"]["llm_health"]["health_state"] == "healthy"
    assert data["health"]["image_health"]["circuit_state"] == "closed"
    assert data["health"]["media_tasks"]["queue_depth"] == 1
    assert data["model_admin"]["model"] == "qwen"
    assert data["task_stats"]["ai_reachable"] is True
    assert data["conversation_kernel"]["feature_level"] == "full_conversation_kernel"


def test_llm_wizard_status_summarizes_next_step(monkeypatch) -> None:
    async def fake_model_admin(*, timeout_sec: float = 0.0):
        _ = timeout_sec
        return {
            "model": "",
            "ai_reachable": True,
            "provider_mode": "hybrid",
            "health_url": "http://127.0.0.1:9099/health",
            "error": "",
            "provider_status": [
                {"id": "local", "configured": True, "reachable": False},
                {"id": "remote", "configured": False, "reachable": False},
            ],
        }

    monkeypatch.setattr("pallas.product.llm.model_admin.fetch_model_admin_status", fake_model_admin)
    monkeypatch.setattr(
        "pallas.product.llm.webui_config.get_llm_webui_config",
        lambda: type("Cfg", (), {"llm_chat_enabled": False, "llm_tools_enabled": True})(),
    )

    client = _build_client(monkeypatch)
    response = client.get("/pallas/api/common-config/llm/wizard/status")

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["ok"] is True
    data = payload["data"]
    assert data["providers_configured"] == 1
    assert data["providers_reachable"] == 0
    assert data["checks"][0]["id"] == "ai_service"
    assert data["checks"][2]["ok"] is False
    assert data["next_step"] == "至少存在一个可达提供方"

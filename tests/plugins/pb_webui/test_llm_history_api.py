from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from packages.pb_webui import extended_api as mod
from packages.pb_webui.config import Config
from pallas.product.llm.session_store import LlmChatTurn


def _build_client(monkeypatch) -> TestClient:
    monkeypatch.setattr(mod, "_check_pallas_write_token", lambda *a, **k: None)
    monkeypatch.setattr(mod, "_require_pallas_token_configured", lambda *a, **k: None)
    monkeypatch.setattr(mod, "ensure_console_metrics_hooks", lambda: None)
    app = FastAPI()
    mod.register_extended_api(app, api_base="/pallas/api", plugin_config=Config())
    return TestClient(app)


def test_llm_history_sessions_get(monkeypatch) -> None:
    async def fake_list_sessions(*, bot_id=None, group_id=None, user_id=None, limit=50):
        assert bot_id == 10001
        assert group_id == 20002
        assert user_id is None
        assert limit == 20
        return [
            {
                "session_key": "10001:20002:30003",
                "bot_id": 10001,
                "group_id": 20002,
                "user_id": 30003,
                "turn_count": 6,
                "first_created_at": 1718700000,
                "last_created_at": 1718700123,
                "last_role": "assistant",
                "last_content": "你好，我在。",
            }
        ]

    monkeypatch.setattr(
        "pallas.product.llm.session_store.list_llm_history_sessions",
        fake_list_sessions,
    )

    client = _build_client(monkeypatch)
    response = client.get(
        "/pallas/api/common-config/llm/history/sessions",
        params={"bot_id": 10001, "group_id": 20002, "limit": 20},
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["ok"] is True
    assert payload["data"]["items"][0]["session_key"] == "10001:20002:30003"
    assert payload["data"]["items"][0]["turn_count"] == 6


def test_llm_history_session_detail_get(monkeypatch) -> None:
    async def fake_session_detail(*, bot_id, group_id, user_id, limit=100):
        assert bot_id == 10001
        assert group_id == 20002
        assert user_id == 30003
        assert limit == 12
        return {
            "session": {
                "session_key": "10001:20002:30003",
                "bot_id": 10001,
                "group_id": 20002,
                "user_id": 30003,
                "turn_count": 3,
                "first_created_at": 1718700000,
                "last_created_at": 1718700123,
                "last_role": "assistant",
                "last_content": "你好，我在。",
            },
            "turns": [
                LlmChatTurn(role="user", content="你好", user_id=30003, created_at=1718700000).model_dump(),
                LlmChatTurn(role="assistant", content="你好，我在。", user_id=30003, created_at=1718700002).model_dump(),
            ],
        }

    monkeypatch.setattr(
        "pallas.product.llm.session_store.get_llm_history_session_detail",
        fake_session_detail,
    )

    client = _build_client(monkeypatch)
    response = client.get(
        "/pallas/api/common-config/llm/history/session",
        params={"bot_id": 10001, "group_id": 20002, "user_id": 30003, "limit": 12},
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["ok"] is True
    assert payload["data"]["session"]["user_id"] == 30003
    assert payload["data"]["turns"][0]["content"] == "你好"

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from packages.pb_webui import extended_api as mod
from packages.pb_webui.config import Config
from pallas.product.llm.repeater_feedback import LlmRepeaterFeedbackEntry


def _build_client(monkeypatch) -> TestClient:
    monkeypatch.setattr(mod, "_check_pallas_write_token", lambda *a, **k: None)
    monkeypatch.setattr(mod, "_require_pallas_token_configured", lambda *a, **k: None)
    monkeypatch.setattr(mod, "ensure_console_metrics_hooks", lambda: None)
    app = FastAPI()
    mod.register_extended_api(app, api_base="/pallas/api", plugin_config=Config())
    return TestClient(app)


def test_llm_repeater_feedback_api_returns_recent_entries(monkeypatch) -> None:
    def fake_list_group_feedback_entries(*, group_id: int, limit: int = 20):
        assert group_id == 123
        assert limit == 20
        return [
            LlmRepeaterFeedbackEntry(
                entry_id="req-1",
                created_at=1718700001,
                bot_id=10001,
                group_id=123,
                user_id=30003,
                request_id="req-1",
                user_text="你又来这套",
                reply_text="少来。",
                behavior_scene="banter",
                behavior_actions=["follow_joke_once"],
                llm_route="plain_llm_chat",
                source_tags=[],
                eligible_for_bias=True,
                eligible_for_writeback=False,
            )
        ]

    monkeypatch.setattr(
        mod,
        "list_group_feedback_entries",
        fake_list_group_feedback_entries,
        raising=False,
    )

    client = _build_client(monkeypatch)
    response = client.get(
        "/pallas/api/llm/repeater-feedback",
        params={"group_id": 123, "limit": 20},
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["ok"] is True
    assert payload["data"]["items"][0]["request_id"] == "req-1"
    assert payload["data"]["items"][0]["reply_text"] == "少来。"
    assert payload["data"]["limit"] == 20


def test_llm_repeater_feedback_summary_api_returns_group_snapshot(monkeypatch) -> None:
    def fake_group_feedback_bias_snapshot(*, group_id: int, limit: int = 40):
        assert group_id == 123
        assert limit == 40
        return {
            "count": 3,
            "top_replies": ["少来。", "行啊。"],
            "scenes": ["banter", "group_threading"],
        }

    monkeypatch.setattr(
        mod,
        "group_feedback_bias_snapshot",
        fake_group_feedback_bias_snapshot,
        raising=False,
    )

    client = _build_client(monkeypatch)
    response = client.get(
        "/pallas/api/llm/repeater-feedback/summary",
        params={"group_id": 123, "limit": 40},
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["ok"] is True
    assert payload["data"]["count"] == 3
    assert payload["data"]["top_replies"] == ["少来。", "行啊。"]
    assert payload["data"]["scenes"] == ["banter", "group_threading"]

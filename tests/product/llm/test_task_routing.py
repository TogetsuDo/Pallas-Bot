from __future__ import annotations

import pytest

from pallas.product.llm.task_routing import (
    TaskRouteSpec,
    clear_task_route_cache,
    resolve_submit_task_name,
    resolve_task_route,
)


def test_resolve_submit_task_name_defaults() -> None:
    assert resolve_submit_task_name("repeater_select") == "repeater_select"
    assert resolve_submit_task_name(None, "drunk") == "drunk"
    assert resolve_submit_task_name("", None) == "llm_chat"


@pytest.mark.asyncio
async def test_resolve_task_route_explicit_model_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    clear_task_route_cache()

    async def fail_health(**_kwargs):
        raise AssertionError("explicit model should bypass remote route lookup")

    monkeypatch.setattr("pallas.product.llm.task_routing.probe_ai_service_health", fail_health)

    route = await resolve_task_route("llm_chat", explicit_model="qwen3:32b")

    assert route == TaskRouteSpec(
        task="llm_chat",
        resolved_model="qwen3:32b",
        provider_hint=None,
        source="explicit",
    )


@pytest.mark.asyncio
async def test_resolve_task_route_prefers_ai_health(monkeypatch: pytest.MonkeyPatch) -> None:
    clear_task_route_cache()

    async def fake_health(**_kwargs):
        return {
            "ok": True,
            "body": {
                "llm": {
                    "provider_mode": "local",
                    "task_routing": {"repeater_select": "qwen3:14b"},
                    "local_task_models": {"llm_chat": "qwen3:8b"},
                }
            },
        }

    async def fail_local(**_kwargs):
        raise AssertionError("health route should be preferred before local-routing fetch")

    monkeypatch.setattr("pallas.product.llm.task_routing.probe_ai_service_health", fake_health)
    monkeypatch.setattr("pallas.product.llm.task_routing.fetch_local_routing_config", fail_local)

    route = await resolve_task_route("repeater_select")

    assert route == TaskRouteSpec(
        task="repeater_select",
        resolved_model="qwen3:14b",
        provider_hint="local",
        source="ai_health",
    )


@pytest.mark.asyncio
async def test_resolve_task_route_falls_back_to_local_config(monkeypatch: pytest.MonkeyPatch) -> None:
    clear_task_route_cache()

    async def fake_health(**_kwargs):
        return {"ok": False, "body": None}

    async def fake_local(**_kwargs):
        return {
            "llm_model": "qwen3:8b",
            "task_models": {
                "repeater_select": "qwen3:14b",
            },
        }

    monkeypatch.setattr("pallas.product.llm.task_routing.probe_ai_service_health", fake_health)
    monkeypatch.setattr("pallas.product.llm.task_routing.fetch_local_routing_config", fake_local)

    repeater_route = await resolve_task_route("repeater_select")
    chat_route = await resolve_task_route("llm_chat")

    assert repeater_route == TaskRouteSpec(
        task="repeater_select",
        resolved_model="qwen3:14b",
        provider_hint=None,
        source="config",
    )
    assert chat_route == TaskRouteSpec(
        task="llm_chat",
        resolved_model="qwen3:8b",
        provider_hint=None,
        source="config",
    )

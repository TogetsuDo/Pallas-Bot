from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from pallas.product.llm.model_admin import fetch_llm_task_stats


@pytest.mark.asyncio
async def test_fetch_llm_task_stats_treats_token_only_ai_snapshot_as_collecting(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bot_snapshot = {
        "source": "bot",
        "day_key": "2026-06-18",
        "updated_at": 1.0,
        "by_task": {},
        "totals": {},
    }
    ai_snapshot = {
        "source": "ai",
        "day_key": "2026-06-18",
        "tokens": {
            "prompt_tokens": 123,
            "completion_tokens": 77,
            "total_tokens": 200,
        },
        "totals": {"task_ok": 4, "task_fail": 1},
    }
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = ai_snapshot

    monkeypatch.setattr(
        "pallas.product.llm.model_admin.llm_task_metrics_snapshot",
        lambda: bot_snapshot,
        raising=False,
    )
    monkeypatch.setattr(
        "pallas.product.llm.model_admin.cluster_llm_task_metrics_snapshot",
        lambda: bot_snapshot,
        raising=False,
    )
    monkeypatch.setattr(
        "pallas.product.llm.model_admin.today_key",
        lambda: "2026-06-18",
        raising=False,
    )
    monkeypatch.setattr(
        "pallas.product.llm.model_admin.HTTPXClient.get",
        AsyncMock(return_value=response),
    )
    written: list[tuple[str, str, dict[str, object]]] = []
    monkeypatch.setattr(
        "pallas.product.llm.llm_daily_stats_store.write_day_side",
        lambda day, side, snapshot: written.append((day, side, snapshot)),
    )
    monkeypatch.setattr(
        "pallas.product.llm.llm_daily_stats_store.load_range",
        lambda *, start_day, end_day: ([], start_day, end_day),
    )

    payload = await fetch_llm_task_stats(start="2026-06-18", end="2026-06-18")

    assert payload["ai_reachable"] is True
    assert payload["persistence"]["ai_collecting"] is True
    assert payload["ai"]["tokens"]["total_tokens"] == 200
    assert payload["history"]["rows"][0]["ai"]["tokens"]["prompt_tokens"] == 123
    assert written[0][0] == "2026-06-18"
    assert written[0][1] == "ai"
    assert written[0][2]["reachable"] is True

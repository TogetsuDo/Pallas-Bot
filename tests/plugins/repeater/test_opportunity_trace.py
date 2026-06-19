from __future__ import annotations

from packages.repeater.opportunity_trace import (
    append_repeater_opportunity_trace,
    read_recent_repeater_opportunity_trace,
)


def test_append_and_read_repeater_opportunity_trace(tmp_path, monkeypatch) -> None:
    from packages.repeater import opportunity_trace as mod

    monkeypatch.setattr(mod, "repeater_opportunity_trace_path", lambda: tmp_path / "repeater_opportunity_trace.jsonl")

    assert append_repeater_opportunity_trace({"kind": "llm_opportunity_gate", "accepted": True, "reply_mode": "god"})
    assert append_repeater_opportunity_trace({"kind": "repeater_reply_bundle", "pick_path": "god_recent_live"})

    rows = read_recent_repeater_opportunity_trace(limit=10)
    assert len(rows) == 2
    assert rows[0]["kind"] == "llm_opportunity_gate"
    assert rows[1]["pick_path"] == "god_recent_live"

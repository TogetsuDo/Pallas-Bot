from __future__ import annotations

from pallas.product.llm.runtime_debug import (
    append_request_snapshot,
    append_runtime_trace,
    build_replay_payload,
    load_runtime_debug_bundle,
)


def test_runtime_debug_snapshot_and_trace_roundtrip(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        "pallas.product.llm.runtime_debug.runtime_debug_dir",
        lambda: tmp_path,
    )
    snapshot_id = append_request_snapshot(
        request_id="req-1",
        task="llm_chat",
        system_prompt="你是牛牛",
        messages=[{"role": "user", "content": "你好"}],
        metadata={
            "agent_stage_plan": ["plan", "tool_loop", "generate"],
            "tool_catalog": {"version": "tool_catalog/v1"},
        },
    )
    append_runtime_trace(
        request_id="req-1",
        trace={"request_snapshot_id": snapshot_id, "version": "agent_trace/v1", "tool_call_count": 1},
    )
    bundle = load_runtime_debug_bundle(request_id="req-1")
    assert bundle["snapshot"]["request_snapshot_id"] == snapshot_id
    assert bundle["trace"]["tool_call_count"] == 1
    replay = build_replay_payload(request_id="req-1")
    assert replay["request_snapshot_id"] == snapshot_id
    assert replay["mode"] == "mock_tools"

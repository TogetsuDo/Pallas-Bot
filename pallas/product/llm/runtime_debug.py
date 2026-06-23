"""LLM runtime 调试：request snapshot 与 trace 落盘。"""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path  # noqa: TC003
from typing import Any

from pallas.core.foundation.paths import plugin_data_dir


def runtime_debug_dir() -> Path:
    path = plugin_data_dir("pb_webui", create=True) / "llm_runtime"
    path.mkdir(parents=True, exist_ok=True)
    return path


def request_snapshot_path() -> Path:
    return runtime_debug_dir() / "request_snapshots.jsonl"


def runtime_trace_path() -> Path:
    return runtime_debug_dir() / "runtime_traces.jsonl"


def append_request_snapshot(
    *,
    request_id: str,
    task: str,
    system_prompt: str,
    messages: list[dict[str, Any]],
    metadata: dict[str, Any],
) -> str:
    snapshot_id = f"reqsnap_{uuid.uuid4().hex[:16]}"
    row = {
        "request_snapshot_id": snapshot_id,
        "request_id": request_id,
        "created_at": int(time.time()),
        "task": task,
        "system_prompt": system_prompt,
        "messages": messages,
        "agent_stage_plan": list(metadata.get("agent_stage_plan") or []),
        "tool_catalog": metadata.get("tool_catalog") or {},
        "metadata_subset": {
            "task": metadata.get("task"),
            "mode": metadata.get("mode"),
            "bot_id": metadata.get("bot_id"),
            "group_id": metadata.get("group_id"),
            "user_id": metadata.get("user_id"),
        },
    }
    with request_snapshot_path().open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return snapshot_id


def append_runtime_trace(*, request_id: str, trace: dict[str, Any]) -> None:
    row = {
        "request_id": request_id,
        "request_snapshot_id": trace.get("request_snapshot_id"),
        "created_at": int(time.time()),
        "trace": trace,
    }
    with runtime_trace_path().open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_runtime_debug_bundle(*, request_id: str) -> dict[str, Any]:
    snapshot = find_request_snapshot(request_id=request_id)
    trace_row = find_runtime_trace(request_id=request_id)
    return {
        "request_id": request_id,
        "snapshot": snapshot,
        "trace": (trace_row or {}).get("trace"),
    }


def build_replay_payload(*, request_id: str, mode: str = "mock_tools") -> dict[str, Any]:
    bundle = load_runtime_debug_bundle(request_id=request_id)
    snapshot = bundle.get("snapshot")
    if not isinstance(snapshot, dict):
        return {"request_id": request_id, "mode": mode, "error": "snapshot_not_found"}
    return {
        "request_id": request_id,
        "request_snapshot_id": snapshot.get("request_snapshot_id"),
        "mode": mode,
        "task": snapshot.get("task"),
        "system_prompt": snapshot.get("system_prompt"),
        "messages": snapshot.get("messages"),
        "agent_stage_plan": snapshot.get("agent_stage_plan"),
        "tool_catalog": snapshot.get("tool_catalog"),
        "metadata_subset": snapshot.get("metadata_subset"),
        "trace": bundle.get("trace"),
    }


def find_request_snapshot(*, request_id: str) -> dict[str, Any] | None:
    path = request_snapshot_path()
    if not path.is_file():
        return None
    matched: dict[str, Any] | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if str(row.get("request_id") or "") == request_id:
            matched = row
    return matched


def find_runtime_trace(*, request_id: str) -> dict[str, Any] | None:
    path = runtime_trace_path()
    if not path.is_file():
        return None
    matched: dict[str, Any] | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if str(row.get("request_id") or "") == request_id:
            matched = row
    return matched

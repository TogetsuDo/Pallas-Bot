from __future__ import annotations

import json
import threading
import time
from typing import TYPE_CHECKING, Any

from pallas.core.foundation.paths import plugin_data_dir

if TYPE_CHECKING:
    from pathlib import Path

_TRACE_LOCK = threading.Lock()
_MAX_LINES = 5000


def repeater_opportunity_trace_path() -> Path:
    return plugin_data_dir("pb_webui", create=True) / "repeater_opportunity_trace.jsonl"


def append_repeater_opportunity_trace(row: dict[str, Any]) -> bool:
    payload = {
        "ts": int(time.time()),
        **dict(row or {}),
    }
    line = json.dumps(payload, ensure_ascii=False)
    path = repeater_opportunity_trace_path()
    with _TRACE_LOCK:
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            previous = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
        except OSError:
            previous = []
        previous.append(line)
        if len(previous) > _MAX_LINES:
            previous = previous[-_MAX_LINES:]
        tmp = path.with_suffix(".jsonl.tmp")
        tmp.write_text("\n".join(previous) + "\n", encoding="utf-8")
        tmp.replace(path)
        return True


def read_recent_repeater_opportunity_trace(*, limit: int = 200) -> list[dict[str, Any]]:
    path = repeater_opportunity_trace_path()
    if not path.is_file():
        return []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    rows: list[dict[str, Any]] = []
    for line in lines[-max(1, int(limit)) :]:
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows

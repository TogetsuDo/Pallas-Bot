from __future__ import annotations

import json
import threading
import time
from typing import TYPE_CHECKING, Any

from .data_dir import pb_webui_data_dir

if TYPE_CHECKING:
    from pathlib import Path

_HISTORY_LOCK = threading.Lock()
_MAX_LINES = 24 * 14


def repeater_metrics_history_path() -> Path:
    return pb_webui_data_dir() / "repeater_metrics_history.jsonl"


def append_repeater_metrics_history(
    *,
    cluster: dict[str, Any],
    process: dict[str, Any] | None,
    sharded: bool,
) -> bool:
    path = repeater_metrics_history_path()
    row = {
        "ts": int(time.time()),
        "day_key": str(cluster.get("day_key") or ""),
        "sharded": bool(sharded),
        "cluster": dict(cluster or {}),
        "process": dict(process or {}),
    }
    body = json.dumps(row, ensure_ascii=False) + "\n"
    with _HISTORY_LOCK:
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            previous = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
        except OSError:
            previous = []
        line = body.rstrip("\n")
        if previous and previous[-1] == line:
            return False
        previous.append(line)
        if len(previous) > _MAX_LINES:
            previous = previous[-_MAX_LINES:]
        tmp = path.with_suffix(".jsonl.tmp")
        tmp.write_text("\n".join(previous) + "\n", encoding="utf-8")
        tmp.replace(path)
        return True


def read_recent_repeater_metrics_history(*, limit: int = 168) -> list[dict[str, Any]]:
    path = repeater_metrics_history_path()
    if not path.is_file():
        return []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    rows: list[dict[str, Any]] = []
    for line in lines[-max(1, int(limit)) :]:
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows

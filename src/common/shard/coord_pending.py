"""coord 目录待处理 JSON 快照（运维 / WebUI 可观测）。"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from src.common.paths import plugin_data_dir

_PLUGIN = "pallas_shard"
_COORD_DIRS = (
    "bot_action",
    "duel_qte",
    "repeater_buffer",
    "cage_duel",
    "duel_group",
    "bot_count",
)


def _coord_root() -> Path:
    return Path(plugin_data_dir(_PLUGIN, create=False)) / "coord"


def _json_files_in(dir_path: Path) -> list[Path]:
    if not dir_path.is_dir():
        return []
    return [p for p in dir_path.glob("*.json") if ".lock" not in p.name]


def _bot_action_open_counts(files: list[Path]) -> tuple[int, int]:
    """返回 (进行中, 已过 deadline 仍未完成)。"""
    open_n = 0
    stale_open_n = 0
    now = time.time()
    for path in files:
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(raw, dict) or raw.get("done"):
            continue
        open_n += 1
        deadline = float(raw.get("deadline") or 0)
        if deadline > 0 and now > deadline:
            stale_open_n += 1
    return open_n, stale_open_n


def coord_pending_snapshot_sync() -> dict[str, Any]:
    root = _coord_root()
    by_dir: dict[str, int] = {}
    open_bot_action = 0
    stale_bot_action = 0
    total = 0
    for name in _COORD_DIRS:
        files = _json_files_in(root / name)
        count = len(files)
        by_dir[name] = count
        total += count
        if name == "bot_action":
            open_bot_action, stale_bot_action = _bot_action_open_counts(files)
    return {
        "total_json": total,
        "actionable_total": open_bot_action,
        "historical_retained": by_dir.get("bot_count", 0) + by_dir.get("duel_group", 0),
        "by_dir": by_dir,
        "bot_action_open": open_bot_action,
        "bot_action_stale_open": stale_bot_action,
    }

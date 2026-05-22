"""coord 目录待处理 JSON 快照（运维 / WebUI 可观测）。"""

from __future__ import annotations

import json
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


def _bot_action_open_count(files: list[Path]) -> int:
    n = 0
    for path in files:
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(raw, dict) and not raw.get("done"):
            n += 1
    return n


def coord_pending_snapshot_sync() -> dict[str, Any]:
    root = _coord_root()
    by_dir: dict[str, int] = {}
    open_bot_action = 0
    total = 0
    for name in _COORD_DIRS:
        files = _json_files_in(root / name)
        count = len(files)
        by_dir[name] = count
        total += count
        if name == "bot_action":
            open_bot_action = _bot_action_open_count(files)
    return {
        "total_json": total,
        "by_dir": by_dir,
        "bot_action_open": open_bot_action,
    }

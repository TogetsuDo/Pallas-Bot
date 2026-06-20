"""Persistence helpers for llm_chat behavior patterns and run records."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from packages.pb_webui.data_dir import pb_webui_data_dir

from .behavior import BehaviorOutcome, BehaviorPattern, BehaviorRun


def _base_dir() -> Path:
    env_dir = str(__import__("os").environ.get("PALLAS_DATA_DIR") or "").strip()
    if env_dir:
        root = Path(env_dir)
        root.mkdir(parents=True, exist_ok=True)
        path = root / "llm_behavior"
        path.mkdir(parents=True, exist_ok=True)
        return path
    path = pb_webui_data_dir() / "llm_behavior"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _patterns_path() -> Path:
    return _base_dir() / "patterns.json"


def _runs_path() -> Path:
    return _base_dir() / "runs.jsonl"


def save_behavior_patterns(patterns: list[BehaviorPattern]) -> None:
    _patterns_path().write_text(
        json.dumps([item.model_dump(mode="json") for item in patterns], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def list_behavior_patterns() -> list[BehaviorPattern]:
    path = _patterns_path()
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8") or "[]")
    return [BehaviorPattern.model_validate(item) for item in payload if isinstance(item, dict)]


def append_behavior_run(run: BehaviorRun) -> None:
    path = _runs_path()
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(run.model_dump(mode="json"), ensure_ascii=False) + "\n")


def list_behavior_runs(*, limit: int = 50) -> list[BehaviorRun]:
    path = _runs_path()
    if not path.exists():
        return []
    rows: list[BehaviorRun] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(BehaviorRun.model_validate(json.loads(line)))
    return rows[-max(1, int(limit)) :]


def list_behavior_runs_for_session(
    *,
    bot_id: int,
    group_id: int | None,
    user_id: int,
    limit: int = 50,
) -> list[BehaviorRun]:
    rows = [
        item
        for item in list_behavior_runs(limit=max(limit * 4, limit))
        if int(item.user_id or 0) == int(user_id)
        and int(item.group_id or 0) == int(group_id or 0)
        and int(item.bot_id or 0) == int(bot_id)
    ]
    return rows[-max(1, int(limit)) :]


def update_behavior_run_annotation(
    request_id: str,
    *,
    labels: list[str],
    final_outcome: BehaviorOutcome | str | None = None,
    disabled: bool | None = None,
) -> BehaviorRun | None:
    rows = list_behavior_runs(limit=10_000)
    updated: BehaviorRun | None = None
    for idx, item in enumerate(rows):
        if item.request_id != request_id:
            continue
        if labels:
            item.manual_labels = [str(label).strip() for label in labels if str(label).strip()]
        if final_outcome:
            item.final_outcome = (
                final_outcome if isinstance(final_outcome, BehaviorOutcome) else BehaviorOutcome(str(final_outcome))
            )
        if disabled is not None:
            item.disabled = bool(disabled)
        rows[idx] = item
        updated = item
        break
    if updated is None:
        return None
    path = _runs_path()
    with path.open("w", encoding="utf-8") as f:
        for item in rows:
            f.write(json.dumps(item.model_dump(mode="json"), ensure_ascii=False) + "\n")
    return updated


def behavior_run_public_dict(run: BehaviorRun) -> dict[str, Any]:
    return run.model_dump(mode="json")

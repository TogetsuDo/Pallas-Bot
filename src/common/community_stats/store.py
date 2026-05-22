"""deployment_id 持久化（一户部署一个 UUID）。"""

from __future__ import annotations

import json
import uuid
from typing import Any

from src.common.config.repo_settings import repo_webui_settings_path

_STATE_FILE = "community_stats.json"


def community_stats_state_path():
    return repo_webui_settings_path().parent / _STATE_FILE


def load_or_create_deployment_id() -> str:
    path = community_stats_state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file():
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            raw = None
        if isinstance(raw, dict):
            dep = str(raw.get("deployment_id") or "").strip().lower()
            if _is_uuid(dep):
                return dep
    dep = str(uuid.uuid4()).lower()
    data: dict[str, Any] = {"deployment_id": dep}
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)
    return dep


def _is_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
    except ValueError:
        return False
    return True

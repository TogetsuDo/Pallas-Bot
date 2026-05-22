"""deployment_id 与心跳入口持久化（一户部署一个 UUID）。"""

from __future__ import annotations

import json
import time
import uuid
from typing import Any

from src.common.config.repo_settings import repo_webui_settings_path

_STATE_FILE = "community_stats.json"


def community_stats_state_path():
    return repo_webui_settings_path().parent / _STATE_FILE


def _read_state_raw() -> dict[str, Any]:
    path = community_stats_state_path()
    if not path.is_file():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return raw if isinstance(raw, dict) else {}


def _write_state(data: dict[str, Any]) -> None:
    path = community_stats_state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def load_community_stats_state() -> dict[str, Any]:
    return dict(_read_state_raw())


def save_heartbeat_endpoint(endpoint: str) -> None:
    ep = (endpoint or "").strip()
    if not ep:
        return
    data = _read_state_raw()
    prev = (data.get("heartbeat_endpoint") or "").strip()
    data["heartbeat_endpoint"] = ep
    _write_state(data)
    if prev and prev != ep:
        from nonebot import logger

        logger.info("community_stats: 心跳入口已切换为 {}", ep)


def touch_primary_probe_unix() -> None:
    data = _read_state_raw()
    data["last_primary_probe_unix"] = int(time.time())
    _write_state(data)


def _is_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
    except ValueError:
        return False
    return True


def load_or_create_deployment_id() -> str:
    data = _read_state_raw()
    dep = str(data.get("deployment_id") or "").strip().lower()
    if _is_uuid(dep):
        return dep
    dep = str(uuid.uuid4()).lower()
    data["deployment_id"] = dep
    _write_state(data)
    return dep

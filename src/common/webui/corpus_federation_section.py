"""WebUI「通用配置 → 语料联邦」。"""

from __future__ import annotations

from typing import Any

from pydantic_core import PydanticUndefined

from src.common.config.dotenv import env_value_to_str
from src.common.config.repo_settings import upsert_repo_settings_items
from src.common.corpus.webui_config import CorpusFederationWebuiConfig, get_corpus_federation_webui_config

CORPUS_FEDERATION_SECTION_ID = "corpus_federation"
CORPUS_FEDERATION_TITLE = "语料联邦"

_FIELD_TO_ENV: dict[str, str] = {
    "merge_order": "PALLAS_CORPUS_MERGE_ORDER",
    "merge_strategy": "PALLAS_CORPUS_MERGE_STRATEGY",
    "community_enabled": "PALLAS_CORPUS_COMMUNITY_ENABLED",
    "auto_enroll": "PALLAS_CORPUS_AUTO_ENROLL",
    "community_contribute": "PALLAS_CORPUS_COMMUNITY_CONTRIBUTE",
    "fed_enabled": "PALLAS_CORPUS_FED_ENABLED",
    "fed_contribute": "PALLAS_CORPUS_FED_CONTRIBUTE",
    "on_remote_failure": "PALLAS_CORPUS_ON_REMOTE_FAILURE",
    "community_api_base": "PALLAS_CORPUS_COMMUNITY_API_BASE",
    "community_token": "PALLAS_CORPUS_TOKEN",
    "community_stats_enabled": "PALLAS_COMMUNITY_STATS_ENABLED",
    "community_stats_endpoint": "PALLAS_COMMUNITY_STATS_ENDPOINT",
    "community_stats_token": "PALLAS_COMMUNITY_STATS_TOKEN",
    "community_stats_interval_sec": "PALLAS_COMMUNITY_STATS_INTERVAL_SEC",
}


def _jsonable(v: Any) -> Any:
    if v is PydanticUndefined:
        return None
    return v


def _field_row(key: str, cur: Any) -> dict[str, Any]:
    f = CorpusFederationWebuiConfig.model_fields[key]
    default_value = None if f.default is PydanticUndefined else f.default
    from src.common.webui.field_meta import field_kind_from_annotation, literal_choices

    ann = f.annotation
    choices = literal_choices(ann)
    row: dict[str, Any] = {
        "name": key,
        "kind": field_kind_from_annotation(ann),
        "required": bool(f.is_required()),
        "description": str(f.description or ""),
        "env_key": _FIELD_TO_ENV.get(key, key.upper()),
        "default": _jsonable(default_value),
        "current": _jsonable(cur),
    }
    if choices is not None:
        row["choices"] = choices
    if key in ("community_enabled", "auto_enroll", "community_contribute", "fed_enabled"):
        row["kind"] = "enum"
        row["choices"] = ["auto", "true", "false"]
    return row


def corpus_federation_payload(*, current_values: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = get_corpus_federation_webui_config()
    data = cfg.model_dump(mode="python")
    if current_values is not None:
        data = {**data, **current_values}
    fields = [_field_row(k, data.get(k)) for k in CorpusFederationWebuiConfig.model_fields]
    return {
        "plugin": CORPUS_FEDERATION_SECTION_ID,
        "module": "src.common.corpus",
        "fields": fields,
        "field_groups": [
            {
                "id": "merge",
                "title": "多读源与合并",
                "field_names": ["merge_order", "merge_strategy", "on_remote_failure"],
            },
            {
                "id": "community",
                "title": "社区语料（stats 中心）",
                "field_names": [
                    "community_enabled",
                    "auto_enroll",
                    "community_contribute",
                    "community_api_base",
                    "community_token",
                ],
            },
            {
                "id": "fed",
                "title": "联邦语料 fed（托管 Phase 2）",
                "field_names": ["fed_enabled", "fed_contribute"],
            },
            {
                "id": "community_stats",
                "title": "社区统计心跳",
                "field_names": [
                    "community_stats_enabled",
                    "community_stats_endpoint",
                    "community_stats_token",
                    "community_stats_interval_sec",
                ],
            },
        ],
    }


def apply_corpus_federation_patch(patch: dict[str, Any]) -> dict[str, Any]:
    current = get_corpus_federation_webui_config().model_dump(mode="python")
    allowed = set(CorpusFederationWebuiConfig.model_fields.keys())
    for k in patch:
        if k not in allowed:
            raise ValueError(f"未知配置项: {k}")
    merged = {**current, **patch}
    validated = CorpusFederationWebuiConfig(**merged).model_dump(mode="python")
    items = {_FIELD_TO_ENV[k]: env_value_to_str(validated[k]) for k in patch if k in _FIELD_TO_ENV}
    upsert_repo_settings_items(items)
    try:
        from src.common.community_stats.config import clear_community_stats_config_cache

        clear_community_stats_config_cache()
    except Exception:
        pass
    try:
        from src.common.corpus.config import clear_corpus_config_cache

        clear_corpus_config_cache()
    except Exception:
        pass
    try:
        from src.common.db.context_repo_access import invalidate_shared_context_repository

        invalidate_shared_context_repository()
    except Exception:
        pass
    return corpus_federation_payload(current_values=validated)

"""WebUI「通用配置 → 语料联邦」（Phase 1：local + community）。"""

from __future__ import annotations

from typing import Any

from pydantic_core import PydanticUndefined

from src.common.config.dotenv import env_value_to_str
from src.common.config.repo_settings import upsert_repo_settings_items
from src.common.corpus.webui_config import CorpusFederationWebuiConfig, get_corpus_federation_webui_config
from src.common.webui.field_help import normalize_field_description

CORPUS_FEDERATION_SECTION_ID = "corpus_federation"
CORPUS_FEDERATION_TITLE = "语料联邦"

# Phase 1 仅暴露已接入项；fed / on_remote_failure 等 Phase 2 不在 WebUI 展示。
_PHASE1_FIELD_NAMES: tuple[str, ...] = (
    "merge_order",
    "merge_strategy",
    "community_enabled",
    "auto_enroll",
    "community_contribute",
    "community_api_base",
    "community_token",
    "community_stats_enabled",
    "community_stats_endpoint",
    "community_stats_token",
    "community_stats_interval_sec",
)

_FIELD_TO_ENV: dict[str, str] = {
    "merge_order": "PALLAS_CORPUS_MERGE_ORDER",
    "merge_strategy": "PALLAS_CORPUS_MERGE_STRATEGY",
    "community_enabled": "PALLAS_CORPUS_COMMUNITY_ENABLED",
    "auto_enroll": "PALLAS_CORPUS_AUTO_ENROLL",
    "community_contribute": "PALLAS_CORPUS_COMMUNITY_CONTRIBUTE",
    "community_api_base": "PALLAS_CORPUS_COMMUNITY_API_BASE",
    "community_token": "PALLAS_CORPUS_TOKEN",
    "community_stats_enabled": "PALLAS_COMMUNITY_STATS_ENABLED",
    "community_stats_endpoint": "PALLAS_COMMUNITY_STATS_ENDPOINT",
    "community_stats_token": "PALLAS_COMMUNITY_STATS_TOKEN",
    "community_stats_interval_sec": "PALLAS_COMMUNITY_STATS_INTERVAL_SEC",
}

_TRI_CHOICES = ["auto", "true", "false"]
_MERGE_ORDER_CHOICES = ["local,community", "local"]
_INTERVAL_CHOICES = ["60", "120", "300", "600", "900", "1800", "3600"]


def _jsonable(v: Any) -> Any:
    if v is PydanticUndefined:
        return None
    return v


def _community_enabled_bool(cur: Any) -> bool:
    if cur is True or cur == "true":
        return True
    if cur is False or cur == "false":
        return False
    return False


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
        "description": normalize_field_description(str(f.description or "")),
        "env_key": _FIELD_TO_ENV.get(key, key.upper()),
        "default": _jsonable(default_value),
        "current": _jsonable(cur),
    }
    if choices is not None:
        row["choices"] = choices
    if key == "community_enabled":
        row["kind"] = "bool"
        from src.common.webui.field_help import field_help

        row["description"] = field_help(
            "是否使用社区共享语料池",
            "开启后除本机语料外还会读取社区池；关闭则只使用本机语料",
            "与上方「读语料顺序」配合使用；首次使用请先填好社区地址与令牌",
        )
        row["current"] = _community_enabled_bool(cur)
    elif key == "merge_order":
        row["kind"] = "enum"
        row["choices"] = _MERGE_ORDER_CHOICES
        if row["current"] not in _MERGE_ORDER_CHOICES:
            row["current"] = _MERGE_ORDER_CHOICES[0]
    elif key in ("auto_enroll", "community_contribute"):
        row["kind"] = "enum"
        row["choices"] = _TRI_CHOICES
    elif key == "community_stats_interval_sec":
        row["kind"] = "enum"
        row["choices"] = _INTERVAL_CHOICES
        row["current"] = str(int(cur)) if cur is not None else row["choices"][2]
    return row


def corpus_federation_payload(*, current_values: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = get_corpus_federation_webui_config()
    data = cfg.model_dump(mode="python")
    if current_values is not None:
        data = {**data, **current_values}
    fields = [_field_row(k, data.get(k)) for k in _PHASE1_FIELD_NAMES]
    return {
        "plugin": CORPUS_FEDERATION_SECTION_ID,
        "module": "src.common.corpus",
        "hot_reload": True,
        "fields": fields,
        "field_groups": [
            {
                "id": "merge",
                "title": "语料来源与合并方式",
                "field_names": ["merge_order", "merge_strategy"],
            },
            {
                "id": "community",
                "title": "社区语料池",
                "field_names": [
                    "community_enabled",
                    "auto_enroll",
                    "community_contribute",
                    "community_api_base",
                    "community_token",
                ],
            },
            {
                "id": "community_stats",
                "title": "社区在线统计上报",
                "field_names": [
                    "community_stats_enabled",
                    "community_stats_endpoint",
                    "community_stats_token",
                    "community_stats_interval_sec",
                ],
            },
        ],
    }


def _normalize_patch(patch: dict[str, Any]) -> dict[str, Any]:
    out = dict(patch)
    if "community_enabled" in out:
        v = out["community_enabled"]
        if isinstance(v, bool):
            out["community_enabled"] = "true" if v else "false"
    if "community_stats_interval_sec" in out:
        try:
            out["community_stats_interval_sec"] = int(out["community_stats_interval_sec"])
        except (TypeError, ValueError) as e:
            raise ValueError("community_stats_interval_sec 须为整数秒") from e
    return out


def apply_corpus_federation_patch(patch: dict[str, Any]) -> dict[str, Any]:
    patch = _normalize_patch(patch)
    current = get_corpus_federation_webui_config().model_dump(mode="python")
    allowed = set(_PHASE1_FIELD_NAMES)
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
    try:
        from nonebot import logger

        from src.common.community_stats.scheduler import schedule_reload_community_stats_reporter

        schedule_reload_community_stats_reporter()
        logger.info("corpus_federation: WebUI 已写入配置，语料与社区统计心跳已热重载")
    except Exception as e:
        from nonebot import logger

        logger.warning("corpus_federation hot reload failed: {}", e)
    return corpus_federation_payload(current_values=validated)

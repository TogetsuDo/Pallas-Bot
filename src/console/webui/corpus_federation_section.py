"""WebUI「通用配置 → 语料联邦」（Phase 1：local + community）。"""

from __future__ import annotations

from typing import Any

from pydantic_core import PydanticUndefined

from src.console.webui.field_help import normalize_field_description
from src.features.corpus.reply_perf_config import CorpusReplyPerfConfig, get_corpus_reply_perf_config
from src.features.corpus.webui_config import CorpusFederationWebuiConfig, get_corpus_federation_webui_config
from src.foundation.config.dotenv import env_value_to_str
from src.foundation.config.repo_settings import upsert_repo_settings_items

CORPUS_FEDERATION_SECTION_ID = "corpus_federation"
CORPUS_FEDERATION_TITLE = "语料联邦"

# Phase 1 仅暴露已接入项；fed / on_remote_failure 等 Phase 2 不在 WebUI 展示。
_PHASE1_FIELD_NAMES: tuple[str, ...] = (
    "merge_order",
    "merge_strategy",
    "community_enabled",
    "auto_enroll",
    "community_contribute",
    "remote_find_enabled",
    "community_api_base",
    "community_token",
    "community_stats_enabled",
    "community_stats_endpoint",
    "community_stats_token",
    "community_stats_interval_sec",
)

_REPLY_PERF_FIELD_NAMES: tuple[str, ...] = (
    "reply_messages_cap",
    "reply_answers_cap",
    "find_cache_ttl_sec",
    "find_cache_max",
)

_WEBUI_FIELD_NAMES: tuple[str, ...] = _PHASE1_FIELD_NAMES + _REPLY_PERF_FIELD_NAMES

_FIELD_TO_ENV: dict[str, str] = {
    "merge_order": "PALLAS_CORPUS_MERGE_ORDER",
    "merge_strategy": "PALLAS_CORPUS_MERGE_STRATEGY",
    "community_enabled": "PALLAS_CORPUS_COMMUNITY_ENABLED",
    "auto_enroll": "PALLAS_CORPUS_AUTO_ENROLL",
    "community_contribute": "PALLAS_CORPUS_COMMUNITY_CONTRIBUTE",
    "remote_find_enabled": "PALLAS_CORPUS_REMOTE_FIND_ENABLED",
    "community_api_base": "PALLAS_CORPUS_COMMUNITY_API_BASE",
    "community_token": "PALLAS_CORPUS_TOKEN",
    "community_stats_enabled": "PALLAS_COMMUNITY_STATS_ENABLED",
    "community_stats_endpoint": "PALLAS_COMMUNITY_STATS_ENDPOINT",
    "community_stats_token": "PALLAS_COMMUNITY_STATS_TOKEN",
    "community_stats_interval_sec": "PALLAS_COMMUNITY_STATS_INTERVAL_SEC",
}

_PERF_FIELD_TO_ENV: dict[str, str] = {
    "reply_messages_cap": "PALLAS_CORPUS_REPLY_MESSAGES_CAP",
    "reply_answers_cap": "PALLAS_CORPUS_REPLY_ANSWERS_CAP",
    "find_cache_ttl_sec": "PALLAS_CORPUS_FIND_CACHE_SEC",
    "find_cache_max": "PALLAS_CORPUS_FIND_CACHE_MAX",
}

_FIELD_TO_ENV_ALL: dict[str, str] = {**_FIELD_TO_ENV, **_PERF_FIELD_TO_ENV}

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


def _field_row(key: str, cur: Any, *, model_fields: dict) -> dict[str, Any]:
    f = model_fields[key]
    default_value = None if f.default is PydanticUndefined else f.default
    from src.console.webui.field_meta import field_kind_from_annotation, literal_choices

    ann = f.annotation
    choices = literal_choices(ann)
    row: dict[str, Any] = {
        "name": key,
        "kind": field_kind_from_annotation(ann),
        "required": bool(f.is_required()),
        "description": normalize_field_description(str(f.description or "")),
        "env_key": _FIELD_TO_ENV_ALL.get(key, key.upper()),
        "default": _jsonable(default_value),
        "current": _jsonable(cur),
    }
    if choices is not None:
        row["choices"] = choices
    if key == "community_enabled":
        row["kind"] = "bool"
        from src.console.webui.field_help import field_help

        row["description"] = field_help(
            "是否使用共享语料池",
            "开启后除本机语料外还会读取共享池；关闭则只使用本机语料",
            "与上方「读语料顺序」配合使用；首次使用请先填好共享池地址与令牌",
        )
        row["current"] = _community_enabled_bool(cur)
    elif key == "merge_order":
        row["kind"] = "enum"
        row["choices"] = _MERGE_ORDER_CHOICES
        if row["current"] not in _MERGE_ORDER_CHOICES:
            row["current"] = _MERGE_ORDER_CHOICES[0]
    elif key in ("auto_enroll", "community_contribute", "remote_find_enabled"):
        row["kind"] = "enum"
        row["choices"] = _TRI_CHOICES
    elif key == "community_stats_interval_sec":
        row["kind"] = "enum"
        row["choices"] = _INTERVAL_CHOICES
        row["current"] = str(int(cur)) if cur is not None else row["choices"][2]
    return row


def corpus_federation_payload(*, current_values: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = get_corpus_federation_webui_config()
    perf = get_corpus_reply_perf_config()
    data = {**cfg.model_dump(mode="python"), **perf.model_dump(mode="python")}
    if current_values is not None:
        data = {**data, **current_values}
    fields = [
        _field_row(k, data.get(k), model_fields=CorpusFederationWebuiConfig.model_fields) for k in _PHASE1_FIELD_NAMES
    ]
    fields.extend(
        _field_row(k, data.get(k), model_fields=CorpusReplyPerfConfig.model_fields) for k in _REPLY_PERF_FIELD_NAMES
    )
    return {
        "plugin": CORPUS_FEDERATION_SECTION_ID,
        "module": "src.features.corpus",
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
                "title": "共享语料",
                "field_names": [
                    "community_enabled",
                    "auto_enroll",
                    "community_contribute",
                    "remote_find_enabled",
                    "community_api_base",
                    "community_token",
                ],
            },
            {
                "id": "community_stats",
                "title": "在线统计",
                "field_names": [
                    "community_stats_enabled",
                    "community_stats_endpoint",
                    "community_stats_token",
                    "community_stats_interval_sec",
                ],
            },
            {
                "id": "reply_perf",
                "title": "接话与查询性能",
                "field_names": list(_REPLY_PERF_FIELD_NAMES),
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
    for key in _REPLY_PERF_FIELD_NAMES:
        if key in out:
            try:
                out[key] = int(out[key])
            except (TypeError, ValueError) as e:
                raise ValueError(f"{key} 须为整数") from e
    return out


def apply_corpus_federation_patch(patch: dict[str, Any]) -> dict[str, Any]:
    patch = _normalize_patch(patch)
    current = get_corpus_federation_webui_config().model_dump(mode="python")
    current_perf = get_corpus_reply_perf_config().model_dump(mode="python")
    allowed = set(_WEBUI_FIELD_NAMES)
    for k in patch:
        if k not in allowed:
            raise ValueError(f"未知配置项: {k}")
    merged = {**current, **current_perf, **patch}
    validated = CorpusFederationWebuiConfig(**{k: merged[k] for k in _PHASE1_FIELD_NAMES}).model_dump(mode="python")
    validated_perf = CorpusReplyPerfConfig(**{k: merged[k] for k in _REPLY_PERF_FIELD_NAMES}).model_dump(mode="python")
    items = {_FIELD_TO_ENV[k]: env_value_to_str(validated[k]) for k in patch if k in _FIELD_TO_ENV}
    items.update({_PERF_FIELD_TO_ENV[k]: env_value_to_str(validated_perf[k]) for k in patch if k in _PERF_FIELD_TO_ENV})
    upsert_repo_settings_items(items)
    try:
        from src.features.community_stats.config import clear_community_stats_config_cache

        clear_community_stats_config_cache()
    except Exception:
        pass
    try:
        from src.features.corpus.config import clear_corpus_config_cache

        clear_corpus_config_cache()
    except Exception:
        pass
    if "remote_find_enabled" in patch or set(_REPLY_PERF_FIELD_NAMES) & set(patch):
        try:
            import asyncio

            from src.features.corpus.find_cache import invalidate_find_cache

            coro = invalidate_find_cache(None)
            try:
                asyncio.get_running_loop().create_task(coro)
            except RuntimeError:
                asyncio.run(coro)
        except Exception:
            pass
    if set(_REPLY_PERF_FIELD_NAMES) & set(patch):
        try:
            from src.features.corpus.reply_perf_config import clear_corpus_reply_perf_config_cache

            clear_corpus_reply_perf_config_cache()
        except Exception:
            pass
    try:
        from src.foundation.db.context_repo_access import invalidate_shared_context_repository

        invalidate_shared_context_repository()
    except Exception:
        pass
    try:
        from nonebot import logger

        from src.features.community_stats.scheduler import schedule_reload_community_stats_reporter

        schedule_reload_community_stats_reporter()
        logger.info("corpus_federation: WebUI 已写入配置，语料与在线统计上报已热重载")
    except Exception as e:
        from nonebot import logger

        logger.warning("corpus_federation hot reload failed: {}", e)
    return corpus_federation_payload(current_values={**validated, **validated_perf})

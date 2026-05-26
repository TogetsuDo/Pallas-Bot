"""WebUI「通用配置 → 联邦控制面」：分组、三态选项与通俗说明。"""

from __future__ import annotations

from typing import Any

from pydantic_core import PydanticUndefined

from src.common.config.dotenv import env_value_to_str
from src.common.config.repo_settings import remove_repo_settings_keys, repo_env_raw_value, upsert_repo_settings_items
from src.common.control_plane.webui_config import (
    ControlPlaneWebuiConfig,
    get_control_plane_webui_config,
    repair_misplaced_federate_redis_env,
    setting_str,
)
from src.common.corpus.config import parse_tristate
from src.common.webui.field_help import field_help, normalize_field_description

CONTROL_PLANE_SECTION_ID = "control_plane"
CONTROL_PLANE_TITLE = "联邦控制面"

_TRI_CHOICES = ["auto", "true", "false"]

_FIELD_LABELS: dict[str, str] = {
    "enabled": "控制面总开关",
    "instance_secret": "入池密钥",
    "bootstrap_url": "中心配置地址",
    "federate_id": "联邦池编号",
    "federate_ingress_enabled": "重复消息去重",
    "coord_redis_url": "去重服务器地址",
    "federate_redis_prefix": "去重键前缀",
}

_FIELD_TO_ENV: dict[str, str] = {
    "enabled": "PALLAS_CONTROL_PLANE_ENABLED",
    "bootstrap_url": "PALLAS_CONTROL_PLANE_BOOTSTRAP_URL",
    "instance_secret": "PALLAS_INSTANCE_SECRET",
    "federate_id": "PALLAS_FEDERATE_ID",
    "federate_ingress_enabled": "PALLAS_FEDERATE_INGRESS_ENABLED",
    "federate_redis_prefix": "PALLAS_FEDERATE_REDIS_PREFIX",
    "coord_redis_url": "PALLAS_FEDERATE_COORD_REDIS_URL",
}

_FIELD_ORDER: tuple[str, ...] = (
    "enabled",
    "instance_secret",
    "bootstrap_url",
    "federate_id",
    "federate_ingress_enabled",
    "coord_redis_url",
    "federate_redis_prefix",
)


def _shard_redis_hint() -> str:
    try:
        shard = str(repo_env_raw_value("REDIS_URL") or "").strip()
    except Exception:
        shard = ""
    if shard:
        return f"当前分片用的 Redis 是 {shard}，不要填到本项。"
    return "分片模式下的 REDIS_URL 与本项无关，勿混填。"


def _enabled_raw() -> str:
    raw = setting_str("PALLAS_CONTROL_PLANE_ENABLED", "true").strip().lower()
    return raw if raw in _TRI_CHOICES else "true"


def _field_row(key: str, cur: Any) -> dict[str, Any]:
    f = ControlPlaneWebuiConfig.model_fields[key]
    default_value = None if f.default is PydanticUndefined else f.default
    row: dict[str, Any] = {
        "name": key,
        "label": _FIELD_LABELS.get(key, key),
        "kind": "string",
        "required": bool(f.is_required()),
        "description": normalize_field_description(str(f.description or "")),
        "env_key": _FIELD_TO_ENV[key],
        "default": default_value,
        "current": cur,
    }
    if key == "enabled":
        row["kind"] = "enum"
        row["choices"] = _TRI_CHOICES
        row["current"] = _enabled_raw()
        row["description"] = field_help(
            "是否向中心自动领取联邦池与去重服务器配置",
            "一般选「自动」或「开启」；关闭后不再拉取中心配置",
            "默认已开启；入池密钥仍需填写",
        )
    elif key == "instance_secret":
        row["description"] = field_help(
            "加入社区联邦池的口令",
            "从控制台「统计与语料」页复制，粘贴到此处",
            "与共享语料口令、统计心跳无关；勿泄露",
        )
    elif key == "bootstrap_url":
        row["description"] = field_help(
            "向中心拉取配置的网址",
            "留空即可，程序会按统计主站/备站自动选择",
            "仅自建中心或特殊网络时填写完整地址",
        )
    elif key == "federate_id":
        row["description"] = field_help(
            "所属联邦池编号",
            "可留空，保存密钥后会由中心自动写入",
            "多套自托管共用同一编号时，跨机去重才生效",
        )
    elif key == "federate_ingress_enabled":
        row["kind"] = "enum"
        row["choices"] = _TRI_CHOICES
        raw = str(cur or "auto").strip().lower()
        row["current"] = raw if raw in _TRI_CHOICES else "auto"
        row["description"] = field_help(
            "避免多套牛牛对同一条群消息各回复一遍",
            "选「自动」：有池编号且去重服务器可用时开启",
            "分片与单进程均会经过此去重",
        )
    elif key == "coord_redis_url":
        row["description"] = field_help(
            "各套牛牛共用的去重服务器（TCP，不是网页）",
            "一般留空，由中心自动下发；仅调试时可手填",
            _shard_redis_hint(),
        )
    elif key == "federate_redis_prefix":
        row["description"] = field_help(
            "去重记录在服务器里的分类前缀",
            "一般留空，由中心或池编号自动生成",
            "与分片协调用的键前缀不是一回事",
        )
    return row


def control_plane_payload(*, current_values: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = get_control_plane_webui_config()
    data = cfg.model_dump(mode="python")
    data["enabled"] = _enabled_raw()
    if current_values is not None:
        data = {**data, **current_values}
    fields = [_field_row(k, data.get(k)) for k in _FIELD_ORDER]
    return {
        "plugin": CONTROL_PLANE_SECTION_ID,
        "module": "src.common.control_plane",
        "hot_reload": True,
        "fields": fields,
        "field_groups": [
            {
                "id": "join",
                "title": "入池与自动配置",
                "field_names": ["enabled", "instance_secret", "bootstrap_url"],
            },
            {
                "id": "pool",
                "title": "联邦池与去重",
                "field_names": ["federate_id", "federate_ingress_enabled"],
            },
            {
                "id": "redis",
                "title": "去重服务器（高级）",
                "field_names": ["coord_redis_url", "federate_redis_prefix"],
            },
        ],
    }


def apply_control_plane_patch(patch: dict[str, Any]) -> dict[str, Any]:
    allowed = set(_FIELD_ORDER)
    for k in patch:
        if k not in allowed:
            raise ValueError(f"未知配置项: {k}")
    cfg = get_control_plane_webui_config()
    merged = cfg.model_dump(mode="python")
    merged["enabled"] = _enabled_raw()
    merged.update(patch)
    if "enabled" in patch:
        en = str(patch["enabled"]).strip().lower()
        if en not in _TRI_CHOICES:
            raise ValueError("enabled 须为 auto、true 或 false")
        merged["enabled"] = en
    if "federate_ingress_enabled" in patch:
        ing = str(patch["federate_ingress_enabled"]).strip().lower()
        if ing not in _TRI_CHOICES:
            raise ValueError("federate_ingress_enabled 须为 auto、true 或 false")
        merged["federate_ingress_enabled"] = ing

    enabled_bool = parse_tristate(str(merged["enabled"]), default=True) is not False
    validated = ControlPlaneWebuiConfig(
        enabled=enabled_bool,
        bootstrap_url=str(merged.get("bootstrap_url") or ""),
        instance_secret=str(merged.get("instance_secret") or ""),
        federate_id=str(merged.get("federate_id") or ""),
        federate_ingress_enabled=str(merged.get("federate_ingress_enabled") or "auto"),
        federate_redis_prefix=str(merged.get("federate_redis_prefix") or ""),
        coord_redis_url=str(merged.get("coord_redis_url") or ""),
    ).model_dump(mode="python")

    items: dict[str, str] = {}
    if "enabled" in patch:
        items["PALLAS_CONTROL_PLANE_ENABLED"] = str(merged["enabled"])
    for k in patch:
        if k == "enabled":
            continue
        env_key = _FIELD_TO_ENV[k]
        items[env_key] = env_value_to_str(validated[k])
    if "coord_redis_url" in patch and not str(validated.get("coord_redis_url") or "").strip():
        items["PALLAS_FEDERATE_COORD_REDIS_URL"] = ""

    upsert_repo_settings_items(items)
    if "coord_redis_url" in patch and not str(validated.get("coord_redis_url") or "").strip():
        remove_repo_settings_keys(["PALLAS_FEDERATE_COORD_REDIS_URL"])
    repair_misplaced_federate_redis_env()

    try:
        from nonebot import logger

        from src.common.control_plane.bootstrap_client import (
            clear_bootstrap_runtime_caches,
            refresh_control_plane_bootstrap,
        )
        from src.common.control_plane.config import clear_control_plane_config_cache
        from src.common.control_plane.webui_config import clear_control_plane_webui_config_cache
        from src.common.federate.config import clear_federate_config_cache

        clear_control_plane_webui_config_cache()
        clear_control_plane_config_cache()
        clear_federate_config_cache()
        clear_bootstrap_runtime_caches()
        import asyncio

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(refresh_control_plane_bootstrap(force=True))
        except RuntimeError:
            asyncio.run(refresh_control_plane_bootstrap(force=True))
        logger.info("control_plane: WebUI 已热重载并刷新 bootstrap")
    except Exception as e:
        from nonebot import logger

        logger.warning("control_plane hot reload failed: {}", e)

    out = validated.copy()
    out["enabled"] = str(merged.get("enabled") or _enabled_raw())
    return control_plane_payload(current_values=out)

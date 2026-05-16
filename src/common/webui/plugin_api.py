"""WebUI「按插件名」配置读写（供 ``pallas_webui.extended_api`` 调用）。"""

from __future__ import annotations

import importlib
from typing import Any

from nonebot import get_loaded_plugins, get_plugin_config
from pydantic import BaseModel
from pydantic_core import PydanticUndefined

from src.common.env_dotenv import env_value_to_str, upsert_env_dotenv_items

from .registry import read_plugin_config, reload_plugin_config


def find_loaded_plugin(plugin_name: str):
    target = (plugin_name or "").strip()
    for p in get_loaded_plugins():
        if str(getattr(p, "name", "") or "").strip() == target:
            return p
    return None


def plugin_module_name(p: Any) -> str:
    mod = getattr(p, "module", None)
    module_name = getattr(mod, "__name__", "") if mod is not None else ""
    if not module_name:
        module_name = str(getattr(p, "module_name", "") or "")
    return module_name.strip()


def plugin_config_model_by_name(plugin_name: str):
    p = find_loaded_plugin(plugin_name)
    if p is None:
        raise ValueError(f"未找到插件: {plugin_name}")
    module_name = plugin_module_name(p)
    if not module_name:
        raise ValueError(f"插件模块名为空: {plugin_name}")
    cfg_mod_name = module_name if module_name.endswith(".config") else f"{module_name}.config"
    try:
        cfg_mod = importlib.import_module(cfg_mod_name)
    except Exception as e:  # noqa: BLE001
        raise ValueError(f"插件缺少 config.py: {plugin_name}") from e
    cfg_cls = getattr(cfg_mod, "Config", None)
    if cfg_cls is None or not isinstance(cfg_cls, type) or not issubclass(cfg_cls, BaseModel):
        raise ValueError(f"插件 config.py 未定义 Config(BaseModel): {plugin_name}")
    return p, module_name, cfg_cls


def field_kind_from_annotation(ann: Any) -> str:
    text = str(ann).lower()
    if "list" in text or "dict" in text or "set" in text or "tuple" in text:
        return "json"
    if "bool" in text:
        return "bool"
    if "int" in text:
        return "int"
    if "float" in text:
        return "float"
    return "string"


def jsonable_value(v: Any) -> Any:
    if v is PydanticUndefined:
        return None
    if isinstance(v, BaseModel):
        return v.model_dump(mode="python")
    if isinstance(v, dict):
        return {str(k): jsonable_value(val) for k, val in v.items()}
    if isinstance(v, list):
        return [jsonable_value(x) for x in v]
    if isinstance(v, (set, tuple)):
        return [jsonable_value(x) for x in v]
    return v


def read_current_plugin_config(module_name: str, cfg_cls: type[BaseModel]) -> BaseModel:
    return read_plugin_config(
        module_name,
        cfg_cls,
        fallback_getter=lambda: get_plugin_config(cfg_cls),
    )


def plugin_config_payload(
    plugin_name: str,
    *,
    current_values: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """GET 用默认 ``current``；PUT 落盘后应传 ``validated``，避免 ``get_plugin_config`` 仍为旧内存。"""
    p, module_name, cfg_cls = plugin_config_model_by_name(plugin_name)
    cfg_obj = read_current_plugin_config(module_name, cfg_cls)
    fields: list[dict[str, Any]] = []
    for key, f in cfg_cls.model_fields.items():
        if current_values is not None:
            cur = current_values.get(key, getattr(cfg_obj, key, f.default))
        else:
            cur = getattr(cfg_obj, key, f.default)
        default_value = None if f.default is PydanticUndefined else f.default
        fields.append({
            "name": key,
            "kind": field_kind_from_annotation(f.annotation),
            "required": bool(f.is_required()),
            "description": str(f.description or ""),
            "env_key": key.upper(),
            "default": jsonable_value(default_value),
            "current": jsonable_value(cur),
        })
    return {
        "plugin": str(getattr(p, "name", "") or plugin_name),
        "module": module_name,
        "fields": fields,
    }


def apply_plugin_config_patch(
    plugin_name: str,
    patch: dict[str, Any],
) -> dict[str, Any]:
    _, module_name, cfg_cls = plugin_config_model_by_name(plugin_name)
    current = read_current_plugin_config(module_name, cfg_cls).model_dump(mode="python")
    allowed = set(cfg_cls.model_fields.keys())
    for k in patch:
        if k not in allowed:
            raise ValueError(f"未知配置项: {k}")
    merged = {**current, **patch}
    validated = cfg_cls(**merged).model_dump(mode="python")
    env_items = {str(k).upper(): env_value_to_str(validated[k]) for k in patch}
    upsert_env_dotenv_items(env_items)
    try:
        reload_plugin_config(module_name)
    except Exception:
        pass
    return plugin_config_payload(plugin_name, current_values=validated)

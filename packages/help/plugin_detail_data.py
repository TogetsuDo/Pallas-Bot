"""二级/三级帮助页结构化数据。"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from pallas.core.limits import effective_command_cooldown_text
from pallas.core.perm import (
    effective_permission_avail_text,
    help_say_phrase,
    help_scene_text,
    iter_user_help_menu,
)

from .markdown_generator import HelpMarkdownIssue
from .plugin_manager import find_plugin, plugin_display_name
from .plugin_match import normalize_help_key

_NUMBERED_USAGE_RE = re.compile(r"^\d+\.\s*")


def normalize_plugin_usage_text(usage: str) -> str:
    """插件 usage 统一为 join_usage 序号列表（≥2 条时 1. 2. 3.）。"""
    from pallas.core.perm.metadata_text import join_usage

    raw = (usage or "").strip()
    if not raw:
        return "暂无说明"
    if " · " in raw and "\n" not in raw:
        parts = [part.strip() for part in raw.split(" · ") if part.strip()]
    else:
        parts = [line.strip() for line in raw.splitlines() if line.strip()]
    items = [_NUMBERED_USAGE_RE.sub("", part) for part in parts if part]
    if len(items) >= 2:
        return join_usage(*items)
    return items[0] if items else "暂无说明"


@dataclass(frozen=True, slots=True)
class HelpFunctionRow:
    index: int
    func: str
    say: str
    scene: str
    perm: str
    cooldown: str
    brief: str
    detail: str


@dataclass(slots=True)
class PluginDetailData:
    plugin: Any
    display_name: str
    description: str
    usage: str
    enabled: bool | None
    functions: list[HelpFunctionRow] = field(default_factory=list)
    extra_sections: list[tuple[str, str]] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class FunctionDetailData:
    plugin: Any
    display_name: str
    func_name: str
    index: int
    total: int
    say: str
    scene: str
    perm: str
    cooldown: str
    brief: str
    detail: str
    extra_sections: list[tuple[str, str]] = field(default_factory=list)


def build_plugin_detail_data(
    plugin_name: str,
    *,
    plugin_enabled: bool | None,
) -> tuple[PluginDetailData | None, HelpMarkdownIssue]:
    target_plugin = find_plugin(plugin_name)
    if not target_plugin:
        return None, HelpMarkdownIssue.PLUGIN_NOT_FOUND

    display_name = plugin_display_name(target_plugin)
    data = PluginDetailData(
        plugin=target_plugin,
        display_name=display_name,
        description="暂无描述",
        usage="暂无说明",
        enabled=plugin_enabled,
    )

    meta = getattr(target_plugin, "metadata", None)
    if meta is not None:
        data.description = str(getattr(meta, "description", None) or "暂无描述").strip()
        data.usage = normalize_plugin_usage_text(str(getattr(meta, "usage", None) or "暂无说明"))
        menu_data = []
        if getattr(meta, "extra", None):
            menu_data = list(iter_user_help_menu(meta.extra.get("menu_data", [])))
        for i, item in enumerate(menu_data, 1):
            perm_raw = effective_permission_avail_text(item)
            cd_raw = effective_command_cooldown_text(item)
            data.functions.append(
                HelpFunctionRow(
                    index=i,
                    func=str(item.get("func", f"未命名功能 {i}") or f"未命名功能 {i}"),
                    say=help_say_phrase(item),
                    scene=help_scene_text(item),
                    perm=perm_raw or "—",
                    cooldown=cd_raw or "—",
                    brief=str(item.get("brief_des", "") or "").strip(),
                    detail=str(item.get("detail_des", "") or "").strip(),
                )
            )

    if target_plugin.name == "maa":
        from pallas.core.plugin_coord import maa as maa_coord

        data.extra_sections.append(("MAA 对接地址", maa_coord.format_maa_http_setup_help()))

    return data, HelpMarkdownIssue.OK


def build_function_detail_data(
    plugin_name: str,
    function_name: str,
) -> tuple[FunctionDetailData | None, HelpMarkdownIssue]:
    target_plugin = find_plugin(plugin_name)
    if not target_plugin:
        return None, HelpMarkdownIssue.PLUGIN_NOT_FOUND

    meta = getattr(target_plugin, "metadata", None)
    if meta is None or not getattr(meta, "extra", None):
        return None, HelpMarkdownIssue.METADATA_MISSING

    user_menu = list(iter_user_help_menu(meta.extra.get("menu_data", [])))
    target_function = None
    target_index = -1

    if function_name.isdigit():
        index = int(function_name) - 1
        if 0 <= index < len(user_menu):
            target_function = user_menu[index]
            target_index = index + 1
    else:
        for index, item in enumerate(user_menu):
            func = item.get("func", "")
            if normalize_help_key(func) == normalize_help_key(function_name):
                target_function = item
                target_index = index + 1
                break
        if not target_function:
            arg_key = normalize_help_key(function_name)
            for index, item in enumerate(user_menu):
                func = item.get("func", "")
                if arg_key and arg_key in normalize_help_key(func):
                    target_function = item
                    target_index = index + 1
                    break

    if not target_function:
        return None, HelpMarkdownIssue.FUNCTION_NOT_FOUND

    display_name = plugin_display_name(target_plugin)
    func_name = str(target_function.get("func", "未命名功能") or "未命名功能")
    perm_raw = effective_permission_avail_text(target_function)
    cd_raw = effective_command_cooldown_text(target_function)
    extra_sections: list[tuple[str, str]] = []
    if target_plugin.name == "maa" and func_name in {"绑定设备", "绑定 MAA 设备", "MAA HTTP"}:
        from pallas.core.plugin_coord import maa as maa_coord

        extra_sections.append(("MAA 对接地址", maa_coord.format_maa_http_setup_help()))

    return (
        FunctionDetailData(
            plugin=target_plugin,
            display_name=display_name,
            func_name=func_name,
            index=target_index,
            total=len(user_menu),
            say=help_say_phrase(target_function),
            scene=help_scene_text(target_function),
            perm=perm_raw or "—",
            cooldown=cd_raw or "—",
            brief=str(target_function.get("brief_des", "") or "暂无简介").strip(),
            detail=str(target_function.get("detail_des", "") or "").strip(),
            extra_sections=extra_sections,
        ),
        HelpMarkdownIssue.OK,
    )

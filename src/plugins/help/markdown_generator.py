import re
import textwrap
from enum import StrEnum

from nonebot import get_loaded_plugins

from src.common.cmd_perm import (
    effective_permission_avail_text,
    help_say_phrase,
    help_scene_text,
    iter_user_help_menu,
)

from .config import Config
from .plugin_manager import find_plugin, plugin_display_name
from .visibility import load_help_hidden_plugins

# 成图宽度与 pillowmd 默认版心大致对齐；总表「简介」列更窄
_HELP_DETAIL_WRAP = 44
_HELP_LIST_INTRO_WRAP = 22


def _sanitize_pipe(cell: str) -> str:
    return (cell or "").replace("|", "｜")


def _markdown_table_cell_linebreaks(text: str, width: int) -> str:
    """一级菜单：折叠空白为单行"""
    t = (text or "").strip()
    if not t:
        return "暂无"
    single = re.sub(r"\s+", " ", t.replace("\n", " "))
    return _sanitize_pipe(single)


def _markdown_table_cell_truncate(text: str, width: int) -> str:
    """二/三级菜单：折叠空白为单行，超过 width 时截断并加省略号。"""
    t = (text or "").strip()
    if not t:
        return "暂无"
    single = re.sub(r"\s+", " ", t.replace("\n", " "))
    single = _sanitize_pipe(single)
    if len(single) > width:
        return single[: width - 1] + "…"
    return single


def _is_markdown_table_block(block: str) -> bool:
    lines = [ln.strip() for ln in block.strip().splitlines() if ln.strip()]
    if len(lines) < 2:
        return False
    return all("|" in ln for ln in lines)


def _is_bullet_block(block: str) -> bool:
    lines = [ln.strip() for ln in block.strip().splitlines() if ln.strip()]
    if not lines:
        return False
    return all(ln.startswith(("·", "•", "- ", "* ")) for ln in lines)


def _wrap_paragraphs_for_help_page(text: str, width: int = _HELP_DETAIL_WRAP) -> str:
    """详情页「说明」「用法」等：按空行分段后对每段 soft-wrap；表格与条目列表保持原样。"""
    if not (text or "").strip():
        return text or ""
    chunks: list[str] = []
    for block in (text or "").split("\n\n"):
        b = block.strip()
        if not b:
            continue
        if _is_markdown_table_block(b) or _is_bullet_block(b):
            chunks.append(b)
            continue
        line = re.sub(r"[ \t\r\f\v]+", " ", b.replace("\n", " ")).strip()
        if not line:
            continue
        chunks.append(
            textwrap.fill(
                line,
                width=max(12, width),
                break_long_words=True,
                break_on_hyphens=True,
            )
        )
    return "\n\n".join(chunks)


class HelpMarkdownIssue(StrEnum):
    """帮助 Markdown 生成结果（供 handler 分支，避免解析正文）。"""

    OK = "ok"
    PLUGIN_NOT_FOUND = "plugin_not_found"
    METADATA_MISSING = "metadata_missing"
    FUNCTION_NOT_FOUND = "function_not_found"


def generate_plugins_markdown(
    plugin_config: Config, show_ignored: bool = False, ignored_plugins: list | None = None
) -> str:
    """生成一级菜单。"""
    plugins = get_loaded_plugins()

    if show_ignored:
        filtered_plugins = [plugin for plugin in plugins if plugin.name]
    else:
        ignored_plugins = ignored_plugins or (plugin_config.ignored_plugins if plugin_config else [])
        hidden_plugins = set(load_help_hidden_plugins())
        filtered_plugins = [
            plugin
            for plugin in plugins
            if plugin.name and plugin.name not in ignored_plugins and plugin.name not in hidden_plugins
        ]

    n = len(filtered_plugins)
    title = "# 牛牛帮助" if not show_ignored else "# 牛牛帮助（超级用户）"
    markdown_content = f"{title}\n\n"

    intro = f"共 **{n}** 个插件；下表「状态」为本群/私聊是否启用（✅/⛔），「简介」仅作概括。"
    markdown_content += f"{_wrap_paragraphs_for_help_page(intro)}\n\n"
    markdown_content += (
        "> **① 本页** 总览 → **②**「牛牛帮助 序号或插件名」功能表 → "
        "**③** 再加功能序号/名称看**详情**（完整口令与用法）\n\n"
    )
    markdown_content += "| 命令 | 说明 |\n|------|------|\n"
    markdown_content += "| 「牛牛帮助 1」 | 第 1 个插件的功能表 |\n"
    markdown_content += "| 「牛牛帮助 MAA远控」 | 按中文名打开插件 |\n"
    markdown_content += "| 「牛牛帮助 1 2」 | 第 1 个插件第 2 条详情 |\n\n"
    markdown_content += "> 开关：「牛牛开启/关闭 插件名」；全开/全关见「牛牛帮助 帮助系统」。\n\n"

    markdown_content += "## 插件列表\n\n"
    markdown_content += "| 序号 | 插件名称 | 状态 | 简介 |\n"
    markdown_content += "|------|----------|------|------|\n"

    sorted_plugins = sorted(filtered_plugins, key=lambda p: plugin_display_name(p))

    for index, plugin in enumerate(sorted_plugins, 1):
        plugin_name = plugin_display_name(plugin)

        if plugin.metadata:
            metadata = plugin.metadata
            description = metadata.description or "暂无描述"
        else:
            description = "暂无描述"
        description = _markdown_table_cell_linebreaks(description, _HELP_LIST_INTRO_WRAP)

        status_placeholder = "{status}"

        markdown_content += f"| {index} | {plugin_name} | {status_placeholder} | {description} |\n"

    if show_ignored:
        markdown_content += "\n> 本视图包含通常不在普通帮助里显示的插件，仅超级用户在私聊下可见。\n"

    markdown_content += "\n> 发「牛牛帮助」可回到本页。\n"
    return markdown_content


def generate_plugin_functions_markdown(
    plugin_name: str, plugin_status: str | None = None
) -> tuple[str, HelpMarkdownIssue]:
    """生成二级菜单。"""
    target_plugin = find_plugin(plugin_name)
    if not target_plugin:
        text = (
            f"# 未找到插件\n\n"
            f"没有找到与「{plugin_name}」对应的插件。\n\n"
            f"请发「牛牛帮助」回到总列表，核对序号或名称后再试。"
        )
        return text, HelpMarkdownIssue.PLUGIN_NOT_FOUND

    plugin_name_display = plugin_display_name(target_plugin)
    markdown_content = f"# {plugin_name_display}"

    if plugin_status:
        status_display = "✅ 已启用" if plugin_status == "✅ 启用" else "⛔ 已禁用"
        markdown_content += f"（{status_display}）\n\n"

        action_hint = "关闭" if plugin_status == "✅ 启用" else "开启"
        verb = "停用" if plugin_status == "✅ 启用" else "启用"
        markdown_content += f"要{verb}本插件，可发：「牛牛{action_hint} {plugin_name_display}」\n\n"
    else:
        markdown_content += "\n\n"

    if target_plugin.metadata:
        metadata = target_plugin.metadata
        description = _wrap_paragraphs_for_help_page(metadata.description or "暂无描述")
        usage = _wrap_paragraphs_for_help_page(metadata.usage or "暂无说明")

        user_menu: list[dict] = []
        if hasattr(metadata, "extra") and metadata.extra:
            menu_data = metadata.extra.get("menu_data", [])
            user_menu = list(iter_user_help_menu(menu_data))

        if user_menu:
            first_func = _sanitize_pipe(str(user_menu[0].get("func", "1") or "1"))
            markdown_content += "## 功能一览\n\n"
            detail_hint = (
                f"需要某一条的完整口令与步骤时，发「牛牛帮助 {plugin_name_display}」+ **序号**"
                f"（如「牛牛帮助 {plugin_name_display} 2」），"
                f"或 + **功能名**（如「牛牛帮助 {plugin_name_display} {first_func}」）。"
            )
            markdown_content += f"{_wrap_paragraphs_for_help_page(detail_hint)}\n\n"
            markdown_content += "| # | 功能 | 怎么说 | 场景 | 何人可用 |\n"
            markdown_content += "|---|------|--------|------|----------|\n"
            say_wrap = 28 if target_plugin.name == "maa" else 24
            for i, item in enumerate(user_menu, 1):
                func_name = _sanitize_pipe(str(item.get("func", f"未命名功能 {i}") or ""))
                say_cell = _markdown_table_cell_truncate(help_say_phrase(item), say_wrap)
                scene_cell = _markdown_table_cell_truncate(help_scene_text(item), 6)
                perm_raw = effective_permission_avail_text(item)
                perm_cell = _markdown_table_cell_truncate(perm_raw, 12) if perm_raw else "—"
                markdown_content += f"| {i} | {func_name} | {say_cell} | {scene_cell} | {perm_cell} |\n"
            markdown_content += "\n"

        markdown_content += "## 说明\n\n"
        markdown_content += f"{description}\n\n"

        if target_plugin.name == "maa":
            from src.plugins.maa.endpoints import format_maa_http_setup_help

            maa_http = _wrap_paragraphs_for_help_page(format_maa_http_setup_help())
            markdown_content += "## MAA 对接地址\n\n"
            markdown_content += f"{maa_http}\n\n"

        markdown_content += "## 插件内用法\n\n"
        markdown_content += f"{usage}\n\n"

        if not user_menu and hasattr(metadata, "extra"):
            markdown_content += "本插件未登记功能列表，仅见上文说明。\n\n"
    else:
        markdown_content += "本插件没有可用的元数据说明。\n\n"

    markdown_content += "---\n\n> 返回总列表：「牛牛帮助」\n"
    return markdown_content, HelpMarkdownIssue.OK


def generate_function_detail_markdown(plugin_name: str, function_name: str) -> tuple[str, HelpMarkdownIssue]:
    """生成三级菜单。"""
    target_plugin = find_plugin(plugin_name)
    if not target_plugin:
        text = f"# 未找到插件\n\n没有找到与「{plugin_name}」对应的插件。\n\n请发「牛牛帮助」回到总列表后再试。"
        return text, HelpMarkdownIssue.PLUGIN_NOT_FOUND

    if not target_plugin.metadata or not hasattr(target_plugin.metadata, "extra"):
        pd = plugin_display_name(target_plugin)
        text = f"# 暂无详情\n\n插件「{pd}」没有可供展示的元数据，因此无法打开本条功能的详细页。"
        return text, HelpMarkdownIssue.METADATA_MISSING

    metadata = target_plugin.metadata
    menu_data = metadata.extra.get("menu_data", []) if metadata.extra else []
    user_menu = list(iter_user_help_menu(menu_data))

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
            if func.lower() == function_name.lower():
                target_function = item
                target_index = index + 1
                break

        if not target_function:
            for index, item in enumerate(user_menu):
                func = item.get("func", "")
                if function_name.lower() in func.lower():
                    target_function = item
                    target_index = index + 1
                    break

    if not target_function:
        pd = plugin_display_name(target_plugin)
        text = (
            f"# 未找到该功能\n\n"
            f"在插件「{pd}」下没有找到与「{function_name}」对应的功能项。\n\n"
            f"请发「牛牛帮助 {pd}」先打开功能列表，确认序号或名称。"
        )
        return text, HelpMarkdownIssue.FUNCTION_NOT_FOUND

    func_name = target_function.get("func", "未命名功能")
    plugin_name_display = plugin_display_name(target_plugin)
    markdown_content = f"# {plugin_name_display} · {func_name}\n\n"
    nav_bits = [f"「牛牛帮助 {plugin_name_display}」列表"]
    if target_index > 1:
        nav_bits.append(f"「牛牛帮助 {plugin_name_display} {target_index - 1}」上一条")
    if target_index < len(user_menu):
        nav_bits.append(f"「牛牛帮助 {plugin_name_display} {target_index + 1}」下一条")
    nav_bits.append("「牛牛帮助」总览")
    markdown_content += f"> 功能详情 · 第 **{target_index}/{len(user_menu)}** 条 · {' · '.join(nav_bits)}\n\n"

    say_plain = help_say_phrase(target_function)
    scene_plain = help_scene_text(target_function)
    perm_avail = effective_permission_avail_text(target_function)
    brief_cell = target_function.get("brief_des", "暂无简介") or "暂无简介"

    markdown_content += "| 项 | 内容 |\n|----|------|\n"
    markdown_content += f"| 怎么说 | {_sanitize_pipe(say_plain)} |\n"
    markdown_content += f"| 场景 | {_sanitize_pipe(scene_plain)} |\n"
    markdown_content += f"| 何人可用 | {_sanitize_pipe(perm_avail or '—')} |\n"
    markdown_content += f"| 简介 | {_sanitize_pipe(str(brief_cell).strip())} |\n\n"

    detail_des = target_function.get("detail_des", "")
    if detail_des:
        markdown_content += f"## 怎么用\n\n{_wrap_paragraphs_for_help_page(str(detail_des))}\n\n"

    if target_plugin.name == "maa" and func_name in {"绑定设备", "绑定 MAA 设备", "MAA HTTP"}:
        from src.plugins.maa.endpoints import format_maa_http_setup_help

        maa_http = _wrap_paragraphs_for_help_page(format_maa_http_setup_help())
        markdown_content += f"## MAA 对接地址\n\n{maa_http}\n\n"

    return markdown_content, HelpMarkdownIssue.OK

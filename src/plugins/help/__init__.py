import asyncio
import io

import pillowmd
from nonebot import get_loaded_plugins, on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageSegment
from nonebot.adapters.onebot.v11.permission import GROUP
from nonebot.params import ArgStr
from nonebot.permission import Permission
from nonebot.plugin import PluginMetadata
from nonebot.typing import T_State

# 导入配置相关模块
from .config import HelpConfig
from .styles import get_default_style, load_config, load_custom_styles

__plugin_meta__ = PluginMetadata(
    name="帮助系统",
    description="显示所有插件的帮助信息",
    usage="""
牛牛帮助 - 显示所有插件的简要帮助信息
牛牛帮助 <插件名/序号> - 显示指定插件的功能列表
牛牛帮助 <插件名/序号> <功能名/序号> - 显示指定功能的详细信息
    """.strip(),
    type="application",
    homepage="https://github.com/Pallas-Bot/Pallas-Bot",
    supported_adapters=["~onebot.v11"],
    extra={
        "version": "1.0.0",
        "menu_data": [
            {
                "func": "显示帮助信息",
                "trigger_method": "on_cmd",
                "trigger_condition": "牛牛帮助",
                "brief_des": "显示所有插件的帮助信息",
                "detail_des": "显示所有已加载插件的元数据信息，包括插件名称、描述、使用方法等，将以图片形式展示",
            },
            {
                "func": "详细帮助信息",
                "trigger_method": "on_cmd",
                "trigger_condition": "牛牛帮助 detail",
                "brief_des": "显示插件的详细帮助信息",
                "detail_des": "显示包括功能列表在内的详细插件信息",
            },
        ],
        "menu_template": "default",
    },
)
# 创建命令处理器
help_cmd = on_command("牛牛帮助", aliases={"牛牛菜单"}, priority=5, block=True)

# 初始化配置和样式
plugin_config = load_config()
AVAILABLE_STYLES = load_custom_styles(plugin_config)
DEFAULT_STYLE_NAME = get_default_style(plugin_config)


def generate_plugins_markdown(detail: bool = False) -> str:
    """生成所有插件信息的Markdown文档（一级菜单"""
    plugins = get_loaded_plugins()

    # 过滤掉被忽略的插件
    ignored_plugins = plugin_config.ignored_plugins if plugin_config else []
    filtered_plugins = [plugin for plugin in plugins if plugin.name and plugin.name not in ignored_plugins]

    # 构建Markdown内容
    markdown_content = "# 牛牛帮助\n\n"
    markdown_content += f"总计加载插件数量: {len(filtered_plugins)}\n\n"

    # 添加表格标题
    markdown_content += "| 序号 | 插件名称 | 插件简介 |\n"
    markdown_content += "|------|----------|----------|\n"

    # 按名称排序插件
    sorted_plugins = sorted(filtered_plugins, key=lambda p: p.name or "")

    for index, plugin in enumerate(sorted_plugins, 1):
        # 添加插件标题
        plugin_name = plugin.name or "未命名插件"

        # 添加插件简介
        if plugin.metadata:
            metadata = plugin.metadata
            description = metadata.description or "暂无描述"
        else:
            description = "暂无描述"

        markdown_content += f"| {index} | {plugin_name} | {description} |\n"

    markdown_content += "\n使用方法: 使用 `牛牛帮助 <序号或插件名>` 查看插件详细功能\n"
    markdown_content += "\n示例: 牛牛帮助 1 或 牛牛帮助 帮助系统\n"
    return markdown_content


def generate_plugin_functions_markdown(plugin_name: str) -> str:
    """生成插件功能列表的Markdown文档（二级菜单）"""
    plugins = get_loaded_plugins()

    # 查找指定的插件
    target_plugin = None
    for plugin in plugins:
        if plugin.name and plugin.name.lower() == plugin_name.lower():
            target_plugin = plugin
            break

    if not target_plugin:
        # 模糊匹配
        for plugin in plugins:
            if plugin.name and plugin_name.lower() in plugin.name.lower():
                target_plugin = plugin
                break

    if not target_plugin:
        return f"# 未找到插件\n\n未找到名为 '{plugin_name}' 的插件。\n\n使用 `牛牛帮助` 查看所有插件。"

    # 构建Markdown内容
    plugin_name_display = target_plugin.name or "未命名插件"
    markdown_content = f"# {plugin_name_display} \n\n"

    if target_plugin.metadata:
        metadata = target_plugin.metadata
        description = metadata.description or "暂无描述"
        usage = metadata.usage or "暂无说明"
        markdown_content += f"**描述**: {description}\n\n"
        markdown_content += f"**使用方法**: {usage}\n\n"

        # 添加功能列表
        if hasattr(metadata, "extra") and metadata.extra:
            menu_data = metadata.extra.get("menu_data", [])
            if menu_data:
                markdown_content += "## 功能列表\n\n"
                markdown_content += "| 序号 | 功能名称 | 简要描述 |\n"
                markdown_content += "|------|----------|----------|\n"
                for i, item in enumerate(menu_data, 1):
                    func_name = item.get("func", f"未命名功能 {i}")
                    brief_des = item.get("brief_des", "暂无简介")
                    markdown_content += f"| {i} | {func_name} | {brief_des} |\n"
                markdown_content += "\n使用方法: 使用 `牛牛帮助 <插件名> <功能序号或名称>` 查看功能详情\n\n"
            else:
                markdown_content += "该插件未定义功能列表。\n\n"
        else:
            markdown_content += "该插件未定义功能列表。\n\n"
    else:
        markdown_content += "该插件未定义元数据。\n\n"

    markdown_content += "---\n\n返回上级: 使用 `牛牛帮助` 命令回到插件列表\n"
    return markdown_content


def generate_function_detail_markdown(plugin_name: str, function_name: str) -> str:
    """生成功能详情的Markdown文档（三级菜单）"""
    plugins = get_loaded_plugins()

    # 查找指定的插件
    target_plugin = None
    for plugin in plugins:
        if plugin.name and plugin.name.lower() == plugin_name.lower():
            target_plugin = plugin
            break

    if not target_plugin:
        # 模糊匹配
        for plugin in plugins:
            if plugin.name and plugin_name.lower() in plugin.name.lower():
                target_plugin = plugin
                break

    if not target_plugin:
        return f"# 未找到插件\n\n未找到名为 '{plugin_name}' 的插件。\n\n使用 `牛牛帮助` 查看所有插件。"

    # 查找功能
    if not target_plugin.metadata or not hasattr(target_plugin.metadata, "extra"):
        return f"# 错误\n\n插件 '{target_plugin.name}' 未定义元数据。"

    metadata = target_plugin.metadata
    menu_data = metadata.extra.get("menu_data", []) if metadata.extra else []

    target_function = None
    target_index = -1
    for index, item in enumerate(menu_data):
        func = item.get("func", "")
        if func.lower() == function_name.lower():
            target_function = item
            target_index = index + 1
            break

    if not target_function:
        # 模糊匹配功能名
        for index, item in enumerate(menu_data):
            func = item.get("func", "")
            if function_name.lower() in func.lower():
                target_function = item
                target_index = index + 1
                break

    if not target_function:
        return f"# 未找到功能\n\n在插件 '{target_plugin.name}' 中未找到功能 '{function_name}'。\n\n使用 `牛牛帮助 {target_plugin.name}` 查看功能列表。"

    # 构建Markdown内容
    func_name = target_function.get("func", "未命名功能")
    plugin_name_display = target_plugin.name or "未命名插件"
    markdown_content = f"# {plugin_name_display} - {func_name} 功能详情\n\n"

    # 使用表格展示功能详情
    markdown_content += "| 属性 | 详情 |\n"
    markdown_content += "|------|------|\n"

    markdown_content += f"| 功能序号 | {target_index} |\n"
    markdown_content += f"| 功能名称 | {func_name} |\n"
    markdown_content += f"| 简要描述 | {target_function.get('brief_des', '暂无简介') or '暂无简介'} |\n"

    trigger_method = target_function.get("trigger_method", "未知")
    trigger_condition = target_function.get("trigger_condition", "未知")
    markdown_content += f"| 触发方式 | {trigger_method} |\n"
    markdown_content += f"| 触发条件 | {trigger_condition} |\n"

    markdown_content += "\n"

    detail_des = target_function.get("detail_des", "")
    if detail_des:
        markdown_content += f"## 详细描述\n\n{detail_des}\n\n"

    markdown_content += "---\n\n"
    markdown_content += f"返回功能列表: `牛牛帮助 {plugin_name_display}`\n\n"
    markdown_content += "返回插件列表: `牛牛帮助`\n"

    return markdown_content


@help_cmd.handle()
async def handle_help_cmd(bot: Bot, event: GroupMessageEvent, state: T_State):
    """处理帮助命令"""
    # 获取命令参数
    args = event.get_plaintext().strip().split()[1:] if event.get_plaintext() else []

    # 使用默认样式
    style_name = DEFAULT_STYLE_NAME

    # 根据参数数量确定显示级别
    if len(args) == 0:
        # 一级菜单：显示所有插件列表
        markdown_content = generate_plugins_markdown()
        await send_image_response(markdown_content, style_name)
    elif len(args) == 1:
        # 二级菜单：显示插件功能列表
        plugin_identifier = args[0]
        plugin_name = plugin_identifier

        # 如果是数字，则尝试按序号查找插件
        if plugin_identifier.isdigit():
            plugins = get_loaded_plugins()
            # 过滤掉被忽略的插件
            ignored_plugins = plugin_config.ignored_plugins if plugin_config else []
            filtered_plugins = [plugin for plugin in plugins if plugin.name and plugin.name not in ignored_plugins]
            sorted_plugins = sorted(filtered_plugins, key=lambda p: p.name or "")
            index = int(plugin_identifier) - 1
            # 边界检查
            if 0 <= index < len(sorted_plugins) and len(sorted_plugins) > 0:
                plugin = sorted_plugins[index]
                plugin_name = plugin.name or "未命名插件"
            else:
                await help_cmd.finish(
                    f"序号错误：插件序号 '{plugin_identifier}' 超出范围，请使用 1 到 {len(sorted_plugins)} 之间的序号。"
                )
                return

        # 检查插件是否存在
        markdown_content = generate_plugin_functions_markdown(plugin_name)
        if "未找到插件" in markdown_content:
            # 插件不存在，直接发送文本响应
            await help_cmd.finish(f"未找到名为 '{plugin_name}' 的插件，请使用 `牛牛帮助` 查看所有插件。")
            return

        await send_image_response(markdown_content, style_name)
    elif len(args) == 2:
        # 三级菜单：显示功能详情
        plugin_identifier = args[0]
        function_identifier = args[1]

        # 处理插件序号
        plugin_name = plugin_identifier
        if plugin_identifier.isdigit():
            plugins = get_loaded_plugins()
            # 过滤掉被忽略的插件
            ignored_plugins = plugin_config.ignored_plugins if plugin_config else []
            filtered_plugins = [plugin for plugin in plugins if plugin.name and plugin.name not in ignored_plugins]
            sorted_plugins = sorted(filtered_plugins, key=lambda p: p.name or "")
            index = int(plugin_identifier) - 1
            # 边界检查
            if 0 <= index < len(sorted_plugins) and len(sorted_plugins) > 0:
                plugin = sorted_plugins[index]
                plugin_name = plugin.name or "未命名插件"
            else:
                await help_cmd.finish(
                    f"序号 '{plugin_identifier}' 超出范围，请使用 1 到 {len(sorted_plugins)} 之间的序号。"
                )
                return

        # 检查插件是否存在
        plugin_check_content = generate_plugin_functions_markdown(plugin_name)
        if "未找到插件" in plugin_check_content:
            # 插件不存在，直接发送文本响应
            await help_cmd.finish(f"未找到插件：未找到名为 '{plugin_name}' 的插件，请使用 `牛牛帮助` 查看所有插件。")
            return

        # 处理功能序号
        function_name = function_identifier
        if function_identifier.isdigit():
            # 如果是数字，尝试按序号查找功能
            plugins = get_loaded_plugins()
            target_plugin = None
            for plugin in plugins:
                if plugin.name and plugin.name.lower() == plugin_name.lower():
                    target_plugin = plugin
                    break

            if not target_plugin:
                # 模糊匹配
                for plugin in plugins:
                    if plugin.name and plugin_name.lower() in plugin.name.lower():
                        target_plugin = plugin
                        break

            if target_plugin and target_plugin.metadata and hasattr(target_plugin.metadata, "extra"):
                metadata = target_plugin.metadata
                menu_data = metadata.extra.get("menu_data", []) if metadata.extra else []
                index = int(function_identifier) - 1
                # 边界检查
                if 0 <= index < len(menu_data) and len(menu_data) > 0:
                    function_name = menu_data[index].get("func", function_identifier)
                else:
                    await help_cmd.finish(
                        f"序号 '{function_identifier}' 超出范围，请使用 1 到 {len(menu_data)} 之间的序号。"
                    )
                    return
            else:
                await help_cmd.finish(f"插件 '{plugin_name}' 未定义功能列表。")
                return

        markdown_content = generate_function_detail_markdown(plugin_name, function_name)
        if "未找到功能" in markdown_content:
            # 功能不存在，直接发送文本响应
            await help_cmd.finish(
                f"在插件 '{plugin_name}' 中未找到功能 '{function_name}'，请使用 `牛牛帮助 {plugin_name}` 查看功能列表。"
            )
            return
        elif "未找到插件" in markdown_content:
            # 插件不存在，直接发送文本响应
            await help_cmd.finish(f"未找到名为 '{plugin_name}' 的插件，请使用 `牛牛帮助` 查看所有插件。")
            return
        elif "错误" in markdown_content:
            # 其他错误，直接发送文本响应
            await help_cmd.finish(f"插件 '{plugin_name}' 未定义元数据。")
            return

        await send_image_response(markdown_content, style_name)
    else:
        await help_cmd.finish("参数错误。使用 `牛牛帮助` 查看帮助。")


async def send_image_response(markdown_content: str, style_name: str):
    """发送图片格式的响应"""
    # 使用pillowmd渲染为图片
    # 获取指定的样式
    style = AVAILABLE_STYLES.get(style_name, AVAILABLE_STYLES.get(DEFAULT_STYLE_NAME, pillowmd.MdStyle()))

    # 获取渲染结果
    render_result = await pillowmd.MdToImage(markdown_content, style=style)
    # 从MdRenderResult对象中提取图片
    image = render_result.image

    # 将Image对象转换为bytes
    img_bytes = io.BytesIO()
    image.save(img_bytes, format="PNG")
    img_bytes.seek(0)

    # 发送图片
    await help_cmd.finish(MessageSegment.image(img_bytes))

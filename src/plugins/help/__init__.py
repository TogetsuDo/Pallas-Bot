from nonebot import get_plugin_config, on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, PrivateMessageEvent
from nonebot.plugin import PluginMetadata
from nonebot.typing import T_State

from src.common.cmd_perm import permission_for_command
from src.common.config import BotConfig, GroupConfig

from .config import Config
from .event_preprocessor import IGNORED_PLUGINS

# 导入处理函数
from .handlers import (
    handle_help_command,
    handle_plugin_operation,
)
from .styles import get_default_style, load_config, load_custom_styles

__plugin_meta__ = PluginMetadata(
    name="帮助系统",
    description="显示所有功能的帮助信息，管理功能启用/禁用",
    usage="""
牛牛帮助 — 第 1 级：全部插件一览
牛牛帮助 〈插件名或序号〉 — 第 2 级：功能表（口令摘要）
牛牛帮助 〈插件〉 〈功能序号或名称〉 — 第 3 级：功能详情（完整口令与「怎么用」，推荐）

牛牛开启 / 牛牛关闭 〈插件名或序号〉 — 本群开关某插件
牛牛开启全部功能 / 牛牛关闭全部功能 — 本群一键全开或全关
所需权限以各功能详情「何人可用」为准（可由 WebUI「命令权限」覆盖）。
    """.strip(),
    type="application",
    homepage="https://github.com/PallasBot/Pallas-Bot",
    supported_adapters={"~onebot.v11"},
    extra={
        "version": "3.0.0",
        "command_permissions": [
            {"id": "help.help", "label": "牛牛帮助", "default": "everyone"},
            {"id": "help.plugin_enable", "label": "牛牛开启（单插件）", "default": "staff"},
            {"id": "help.plugin_disable", "label": "牛牛关闭（单插件）", "default": "staff"},
            {"id": "help.plugin_enable_all", "label": "牛牛开启全部功能", "default": "staff"},
            {"id": "help.plugin_disable_all", "label": "牛牛关闭全部功能", "default": "staff"},
        ],
        "menu_data": [
            {
                "func": "总列表",
                "trigger_method": "on_cmd",
                "trigger_scene": "群内或私聊",
                "trigger_condition": "牛牛帮助",
                "command_permission": "help.help",
                "brief_des": "全部插件、状态与简介",
                "detail_des": "看图可知本群各插件是否启用；用序号或中文名继续打开下级。",
            },
            {
                "func": "插件详情",
                "trigger_method": "on_cmd",
                "trigger_scene": "群内或私聊",
                "trigger_condition": "牛牛帮助 〈插件名或序号〉",
                "command_permission": "help.help",
                "brief_des": "单插件说明与功能表",
                "detail_des": "含用法与「怎么说 / 场景 / 何人可用」；可再跟功能序号或名称看详情。",
            },
            {
                "func": "功能详情",
                "trigger_method": "on_cmd",
                "trigger_scene": "群内或私聊",
                "trigger_condition": "牛牛帮助 〈插件〉 〈功能序号或名称〉",
                "command_permission": "help.help",
                "brief_des": "单条功能的口令与说明",
                "detail_des": "展示完整怎么说、场景、权限与 detail_des。",
            },
            {
                "func": "插件开关",
                "trigger_method": "on_cmd",
                "trigger_scene": "群内",
                "trigger_condition": "牛牛开启 / 牛牛关闭 〈插件名或序号〉",
                "command_permissions": ["help.plugin_enable", "help.plugin_disable"],
                "brief_des": "本群启用或停用某插件",
                "detail_des": "例：牛牛开启 牛牛复读、牛牛关闭 1；命名规则同打开插件详情。",
            },
            {
                "func": "批量开关",
                "trigger_method": "on_cmd",
                "trigger_scene": "群内",
                "trigger_condition": "牛牛开启全部功能 / 牛牛关闭全部功能",
                "command_permissions": ["help.plugin_enable_all", "help.plugin_disable_all"],
                "brief_des": "本群一键全开或全关",
                "detail_des": "切换当前群内所有已加载插件的开关状态。",
            },
        ],
        "menu_template": "default",
    },
)

plugin_config = get_plugin_config(Config)

# 初始化配置和样式
AVAILABLE_STYLES = load_custom_styles(plugin_config)
DEFAULT_STYLE_NAME = get_default_style(plugin_config)


help_cmd = on_command("牛牛帮助", priority=5, block=True, permission=permission_for_command("help.help"))

HELP_COOLDOWN_KEY = "help"

plugin_enable_cmd = on_command(
    "牛牛开启", priority=5, block=True, permission=permission_for_command("help.plugin_enable")
)

plugin_disable_cmd = on_command(
    "牛牛关闭", priority=5, block=True, permission=permission_for_command("help.plugin_disable")
)

plugin_enable_all_cmd = on_command(
    "牛牛开启全部功能", priority=5, block=True, permission=permission_for_command("help.plugin_enable_all")
)

plugin_disable_all_cmd = on_command(
    "牛牛关闭全部功能", priority=5, block=True, permission=permission_for_command("help.plugin_disable_all")
)


@help_cmd.handle()
async def handle_help_cmd(bot: Bot, event: GroupMessageEvent | PrivateMessageEvent, state: T_State):
    """处理帮助命令（群聊和私聊）"""
    if isinstance(event, GroupMessageEvent):
        config = GroupConfig(event.group_id, cooldown=3)
        if not await config.is_cooldown(HELP_COOLDOWN_KEY):
            await help_cmd.finish()
            return
        await config.refresh_cooldown(HELP_COOLDOWN_KEY)

    await handle_help_command(bot, event, state, plugin_config, AVAILABLE_STYLES, DEFAULT_STYLE_NAME, help_cmd)


def extract_plugin_name_from_command(event: GroupMessageEvent | PrivateMessageEvent, prefix: str) -> str:
    """从命令文本中提取插件名称"""
    message_text = event.get_plaintext().strip()
    if message_text.startswith(prefix):
        args = message_text[len(prefix) :].strip().split()
        return args[0] if args else ""
    return ""


@plugin_enable_cmd.handle()
async def handle_enable_command(bot: Bot, event: GroupMessageEvent | PrivateMessageEvent, state: T_State):
    """处理功能启用命令"""
    plugin_name = extract_plugin_name_from_command(event, "牛牛开启")
    if not plugin_name:
        await plugin_enable_cmd.finish("博士，即使身为大祭司，你不说想要开启什么，我也帮不了你呀")
        return

    state["plugin_name"] = plugin_name
    await handle_plugin_operation(bot, event, state, "enable", plugin_enable_cmd)


@plugin_disable_cmd.handle()
async def handle_disable_command(bot: Bot, event: GroupMessageEvent | PrivateMessageEvent, state: T_State):
    """处理功能禁用命令"""
    plugin_name = extract_plugin_name_from_command(event, "牛牛关闭")
    if not plugin_name:
        await plugin_disable_cmd.finish("博士，即使身为大祭司，你不说想要关闭什么，我也帮不了你呀")
        return

    state["plugin_name"] = plugin_name
    await handle_plugin_operation(bot, event, state, "disable", plugin_disable_cmd)


async def toggle_all_plugins(bot: Bot, event: GroupMessageEvent | PrivateMessageEvent, action: str, matcher):
    """处理启用/禁用所有功能的命令"""
    from nonebot import get_loaded_plugins

    from .handlers import get_context_info
    from .plugin_manager import toggle_plugin

    bot_id, group_id = get_context_info(bot, event)

    # 获取所有已加载的功能并过滤
    plugins = [p for p in get_loaded_plugins() if p.name and p.name.lower() not in IGNORED_PLUGINS]

    count = 0
    for plugin in plugins:
        success, _ = await toggle_plugin(plugin.name, group_id, bot_id, action=action)
        if success:
            count += 1

    action_name = "启用" if action == "enable" else "停止"
    await matcher.finish(f"在米诺斯女神的允许下，我将{action_name} {count} 个能力")


@plugin_enable_all_cmd.handle()
async def handle_enable_all_command(bot: Bot, event: GroupMessageEvent | PrivateMessageEvent, state: T_State):
    """处理启用所有功能的命令"""
    await toggle_all_plugins(bot, event, "enable", plugin_enable_all_cmd)


@plugin_disable_all_cmd.handle()
async def handle_disable_all_command(bot: Bot, event: GroupMessageEvent | PrivateMessageEvent, state: T_State):
    """处理禁用所有功能的命令"""
    await toggle_all_plugins(bot, event, "disable", plugin_disable_all_cmd)

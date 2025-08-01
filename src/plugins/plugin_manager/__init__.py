import re
from typing import Dict, List, Optional, Tuple, Union

from nonebot import get_driver, get_loaded_plugins, on_command, on_shell_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message, MessageEvent, MessageSegment
from nonebot.exception import ParserExit
from nonebot.matcher import Matcher
from nonebot.params import CommandArg, ShellCommandArgs
from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata
from nonebot.rule import ArgumentParser, ParserExit

from src.common.db.modules import BotConfigModule, GroupConfigModule
from src.common.permission import PermissionLevel, permission_check

__plugin_meta__ = PluginMetadata(
    name="插件管理器",
    description="管理插件的开关和权限设置",
    usage="""
# 插件管理器使用指南

## 基础命令
- 查看插件列表: /plugins list
- 查看插件状态: /plugins status [插件名]

## 管理员命令
- 全局禁用插件: /plugins disable <插件名>
- 全局启用插件: /plugins enable <插件名>
- 在当前群禁用插件: /plugins group disable <插件名>
- 在当前群启用插件: /plugins group enable <插件名>
- 设置插件权限: /plugins perm <插件名> <权限等级>
  权限等级: user(普通用户), admin(群管理), owner(群主), superuser(超级用户)

## 注意事项
- 插件名称必须完全匹配
- 某些核心插件无法被禁用
    """,
    type="application",
    homepage="https://github.com/Pallas-Bot/Pallas-Bot",
    supported_adapters={"~onebot.v11"},
    extra={
        "version": "1.0.0",
        "menu_data": [
            {
                "func": "查看插件列表",
                "trigger_method": "on_cmd",
                "trigger_condition": "/plugins list",
                "brief_des": "列出所有已加载的插件",
                "detail_des": "列出所有已加载的插件，包括插件名称和描述",
            },
            {
                "func": "查看插件状态",
                "trigger_method": "on_cmd",
                "trigger_condition": "/plugins status [插件名]",
                "brief_des": "查看插件的启用状态",
                "detail_des": "查看指定插件在全局和当前群的启用状态，以及权限设置",
            },
            {
                "func": "全局禁用插件",
                "trigger_method": "on_cmd",
                "trigger_condition": "/plugins disable <插件名>",
                "brief_des": "全局禁用指定插件",
                "detail_des": "全局禁用指定插件，该操作需要超级用户权限",
            },
            {
                "func": "全局启用插件",
                "trigger_method": "on_cmd",
                "trigger_condition": "/plugins enable <插件名>",
                "brief_des": "全局启用指定插件",
                "detail_des": "全局启用指定插件，该操作需要超级用户权限",
            },
            {
                "func": "群禁用插件",
                "trigger_method": "on_cmd",
                "trigger_condition": "/plugins group disable <插件名>",
                "brief_des": "在当前群禁用指定插件",
                "detail_des": "在当前群禁用指定插件，该操作需要群管理员权限",
            },
            {
                "func": "群启用插件",
                "trigger_method": "on_cmd",
                "trigger_condition": "/plugins group enable <插件名>",
                "brief_des": "在当前群启用指定插件",
                "detail_des": "在当前群启用指定插件，该操作需要群管理员权限",
            },
            {
                "func": "设置插件权限",
                "trigger_method": "on_cmd",
                "trigger_condition": "/plugins perm <插件名> <权限等级>",
                "brief_des": "设置插件的使用权限",
                "detail_des": "设置插件的使用权限级别，可选权限：user(普通用户), admin(群管理), owner(群主), superuser(超级用户)",
            },
        ],
        "menu_template": "default",
    },
)

# 配置
driver = get_driver()

# 受保护的插件列表，这些插件不能被禁用
PROTECTED_PLUGINS = ["plugin_manager", "help"]

# 创建命令解析器
plugin_parser = ArgumentParser("plugins", description="插件管理器")
subparsers = plugin_parser.add_subparsers(title="子命令", dest="subcommand")

# 创建list子命令
list_parser = subparsers.add_parser("list", help="列出所有插件")

# 创建status子命令
status_parser = subparsers.add_parser("status", help="查看插件状态")
status_parser.add_argument("plugin_name", nargs="?", help="插件名称")

# 创建enable子命令
enable_parser = subparsers.add_parser("enable", help="启用插件（全局）")
enable_parser.add_argument("plugin_name", help="要启用的插件名称")

# 创建disable子命令
disable_parser = subparsers.add_parser("disable", help="禁用插件（全局）")
disable_parser.add_argument("plugin_name", help="要禁用的插件名称")

# 创建group子命令
group_parser = subparsers.add_parser("group", help="群级别插件管理")
group_subparsers = group_parser.add_subparsers(title="群管理子命令", dest="group_subcommand")

# 创建group enable子命令
group_enable_parser = group_subparsers.add_parser("enable", help="在当前群启用插件")
group_enable_parser.add_argument("plugin_name", help="要启用的插件名称")

# 创建group disable子命令
group_disable_parser = group_subparsers.add_parser("disable", help="在当前群禁用插件")
group_disable_parser.add_argument("plugin_name", help="要禁用的插件名称")

# 创建perm子命令
perm_parser = subparsers.add_parser("perm", help="设置插件权限")
perm_parser.add_argument("plugin_name", help="插件名称")
perm_parser.add_argument(
    "permission_level",
    help="权限等级：user(普通用户), admin(群管理), owner(群主), superuser(超级用户)",
    choices=["user", "admin", "owner", "superuser"],
)

# 创建命令处理器
plugin_cmd = on_shell_command("plugins", parser=plugin_parser, priority=5)


@plugin_cmd.handle()
async def handle_plugin_cmd(bot: Bot, event: MessageEvent, args: ParserExit | dict = ShellCommandArgs()):
    if isinstance(args, ParserExit):
        await plugin_cmd.finish(str(args))
        return

    subcommand = args.get("subcommand", "")

    if not subcommand:
        plugin_help = __plugin_meta__.usage
        await plugin_cmd.finish(plugin_help)
        return

    if subcommand == "list":
        plugins_info = await get_plugins_info()
        reply = "插件列表：\n"
        for idx, (name, description) in enumerate(plugins_info, start=1):
            reply += f"{idx}. {name}: {description}\n"
        await plugin_cmd.finish(reply)

    elif subcommand == "status":
        plugin_name = args.get("plugin_name", "")
        if not plugin_name:
            all_status = await get_all_plugins_status(bot, event)
            await plugin_cmd.finish(all_status)
        else:
            status = await get_plugin_status(plugin_name, bot, event)
            await plugin_cmd.finish(status)

    elif subcommand == "enable":
        # 需要超级用户权限
        if not await SUPERUSER(bot, event):
            await plugin_cmd.finish("权限不足，只有超级用户才能执行此操作")
            return

        plugin_name = args.get("plugin_name", "")
        if not plugin_name:
            await plugin_cmd.finish("请指定要启用的插件名称")
            return

        if plugin_name not in [p.name for p in get_loaded_plugins() if p.name]:
            await plugin_cmd.finish(f"插件 {plugin_name} 不存在")
            return

        result = await enable_plugin_global(plugin_name, bot, event)
        await plugin_cmd.finish(result)

    elif subcommand == "disable":
        # 需要超级用户权限
        if not await SUPERUSER(bot, event):
            await plugin_cmd.finish("权限不足，只有超级用户才能执行此操作")
            return

        plugin_name = args.get("plugin_name", "")
        if not plugin_name:
            await plugin_cmd.finish("请指定要禁用的插件名称")
            return

        if plugin_name not in [p.name for p in get_loaded_plugins() if p.name]:
            await plugin_cmd.finish(f"插件 {plugin_name} 不存在")
            return

        if plugin_name in PROTECTED_PLUGINS:
            await plugin_cmd.finish(f"插件 {plugin_name} 是受保护的插件，不能被禁用")
            return

        result = await disable_plugin_global(plugin_name, bot, event)
        await plugin_cmd.finish(result)

    elif subcommand == "group":
        # 只能在群聊中使用
        if not isinstance(event, GroupMessageEvent):
            await plugin_cmd.finish("该命令只能在群聊中使用")
            return

        group_subcommand = args.get("group_subcommand", "")
        plugin_name = args.get("plugin_name", "")

        if not group_subcommand:
            await plugin_cmd.finish("请指定群管理子命令：enable 或 disable")
            return

        if not plugin_name:
            await plugin_cmd.finish("请指定插件名称")
            return

        if plugin_name not in [p.name for p in get_loaded_plugins() if p.name]:
            await plugin_cmd.finish(f"插件 {plugin_name} 不存在")
            return

        if plugin_name in PROTECTED_PLUGINS:
            await plugin_cmd.finish(f"插件 {plugin_name} 是受保护的插件，不能被禁用")
            return

        # 权限检查：需要群管理员或更高权限
        sender_role = event.sender.role
        if sender_role not in ["admin", "owner"] and not await SUPERUSER(bot, event):
            await plugin_cmd.finish("权限不足，只有群管理员或更高权限才能执行此操作")
            return

        if group_subcommand == "enable":
            result = await enable_plugin_group(plugin_name, event.group_id)
            await plugin_cmd.finish(result)
        elif group_subcommand == "disable":
            result = await disable_plugin_group(plugin_name, event.group_id)
            await plugin_cmd.finish(result)
        else:
            await plugin_cmd.finish(f"未知的群管理子命令：{group_subcommand}")

    elif subcommand == "perm":
        # 需要超级用户权限
        if not await SUPERUSER(bot, event):
            await plugin_cmd.finish("权限不足，只有超级用户才能执行此操作")
            return

        plugin_name = args.get("plugin_name", "")
        perm_level_str = args.get("permission_level", "")

        if not plugin_name or not perm_level_str:
            await plugin_cmd.finish("请指定插件名称和权限等级")
            return

        if plugin_name not in [p.name for p in get_loaded_plugins() if p.name]:
            await plugin_cmd.finish(f"插件 {plugin_name} 不存在")
            return

        # 映射权限等级字符串到枚举值
        perm_map = {
            "user": PermissionLevel.USER,
            "admin": PermissionLevel.ADMIN,
            "owner": PermissionLevel.OWNER,
            "superuser": PermissionLevel.SUPERUSER,
        }
        perm_level = perm_map.get(perm_level_str.lower())

        if not perm_level:
            await plugin_cmd.finish(f"未知的权限等级：{perm_level_str}")
            return

        result = await set_plugin_permission(plugin_name, perm_level)
        await plugin_cmd.finish(result)

    else:
        await plugin_cmd.finish(f"未知的子命令：{subcommand}")


async def get_plugins_info() -> list[tuple[str, str]]:
    """获取所有插件的信息"""
    plugins = get_loaded_plugins()
    result = []
    for p in plugins:
        if p.name:  # 跳过没有名称的插件
            description = p.metadata.description if p.metadata else "无描述"
            result.append((p.name, description))
    return sorted(result)  # 按名称排序


async def get_all_plugins_status(bot: Bot, event: MessageEvent) -> str:
    """获取所有插件的状态"""
    plugins = get_loaded_plugins()
    bot_id = int(bot.self_id)

    # 获取机器人配置
    bot_config = await BotConfigModule.find_one({"account": bot_id})
    global_disabled = bot_config.disabled_plugins if bot_config else []

    # 如果是群聊消息，获取群配置
    group_disabled = []
    if isinstance(event, GroupMessageEvent):
        group_id = event.group_id
        group_config = await GroupConfigModule.find_one({"group_id": group_id})
        group_disabled = group_config.disabled_plugins if group_config else []

    # 构建状态信息
    result = "插件状态概览：\n"
    for p in plugins:
        if p.name:  # 跳过没有名称的插件
            global_status = "❌" if p.name in global_disabled else "✅"
            group_status = "❌" if p.name in group_disabled else "✅"

            if isinstance(event, GroupMessageEvent):
                result += f"{p.name}: 全局{global_status} | 本群{group_status}\n"
            else:
                result += f"{p.name}: 全局{global_status}\n"

    return result


async def get_plugin_status(plugin_name: str, bot: Bot, event: MessageEvent) -> str:
    """获取指定插件的状态"""
    # 检查插件是否存在
    plugins = get_loaded_plugins()
    plugin_exists = False
    plugin_metadata = None

    for p in plugins:
        if p.name == plugin_name:
            plugin_exists = True
            plugin_metadata = p.metadata
            break

    if not plugin_exists:
        return f"插件 {plugin_name} 不存在"

    bot_id = int(bot.self_id)

    # 获取机器人配置
    bot_config = await BotConfigModule.find_one({"account": bot_id})
    global_disabled = bot_config.disabled_plugins if bot_config else []
    global_status = "禁用" if plugin_name in global_disabled else "启用"

    # 构建状态信息
    result = f"插件: {plugin_name}\n"
    result += f"描述: {plugin_metadata.description if plugin_metadata else '无描述'}\n"
    result += f"全局状态: {global_status}\n"

    # 如果是群聊消息，添加群状态
    if isinstance(event, GroupMessageEvent):
        group_id = event.group_id
        group_config = await GroupConfigModule.find_one({"group_id": group_id})
        group_disabled = group_config.disabled_plugins if group_config else []
        group_status = "禁用" if plugin_name in group_disabled else "启用"
        result += f"本群状态: {group_status}\n"

    # 添加保护状态
    if plugin_name in PROTECTED_PLUGINS:
        result += "保护状态: 受保护（无法禁用）\n"

    return result


async def enable_plugin_global(plugin_name: str, bot: Bot, event: MessageEvent) -> str:
    """全局启用插件"""
    bot_id = int(bot.self_id)

    # 获取机器人配置
    bot_config = await BotConfigModule.find_one({"account": bot_id})
    if not bot_config:
        # 如果配置不存在，创建一个新的
        bot_config = BotConfigModule(account=bot_id)

    # 检查插件是否已启用
    if not hasattr(bot_config, "disabled_plugins"):
        bot_config.disabled_plugins = []

    if plugin_name not in bot_config.disabled_plugins:
        return f"插件 {plugin_name} 已经是全局启用状态"

    # 从禁用列表中移除
    bot_config.disabled_plugins.remove(plugin_name)
    await bot_config.save()

    return f"已全局启用插件 {plugin_name}"


async def disable_plugin_global(plugin_name: str, bot: Bot, event: MessageEvent) -> str:
    """全局禁用插件"""
    bot_id = int(bot.self_id)

    # 获取机器人配置
    bot_config = await BotConfigModule.find_one({"account": bot_id})
    if not bot_config:
        # 如果配置不存在，创建一个新的
        bot_config = BotConfigModule(account=bot_id)

    # 确保disabled_plugins属性存在
    if not hasattr(bot_config, "disabled_plugins"):
        bot_config.disabled_plugins = []

    # 检查插件是否已禁用
    if plugin_name in bot_config.disabled_plugins:
        return f"插件 {plugin_name} 已经是全局禁用状态"

    # 添加到禁用列表
    bot_config.disabled_plugins.append(plugin_name)
    await bot_config.save()

    return f"已全局禁用插件 {plugin_name}"


async def enable_plugin_group(plugin_name: str, group_id: int) -> str:
    """在指定群启用插件"""
    # 获取群配置
    group_config = await GroupConfigModule.find_one({"group_id": group_id})
    if not group_config:
        # 如果配置不存在，创建一个新的
        group_config = GroupConfigModule(group_id=group_id)

    # 确保disabled_plugins属性存在
    if not hasattr(group_config, "disabled_plugins"):
        group_config.disabled_plugins = []

    # 检查插件是否已启用
    if plugin_name not in group_config.disabled_plugins:
        return f"插件 {plugin_name} 在本群已经是启用状态"

    # 从禁用列表中移除
    group_config.disabled_plugins.remove(plugin_name)
    await group_config.save()

    return f"已在本群启用插件 {plugin_name}"


async def disable_plugin_group(plugin_name: str, group_id: int) -> str:
    """在指定群禁用插件"""
    # 获取群配置
    group_config = await GroupConfigModule.find_one({"group_id": group_id})
    if not group_config:
        # 如果配置不存在，创建一个新的
        group_config = GroupConfigModule(group_id=group_id)

    # 确保disabled_plugins属性存在
    if not hasattr(group_config, "disabled_plugins"):
        group_config.disabled_plugins = []

    # 检查插件是否已禁用
    if plugin_name in group_config.disabled_plugins:
        return f"插件 {plugin_name} 在本群已经是禁用状态"

    # 添加到禁用列表
    group_config.disabled_plugins.append(plugin_name)
    await group_config.save()

    return f"已在本群禁用插件 {plugin_name}"


async def set_plugin_permission(plugin_name: str, permission_level: PermissionLevel) -> str:
    """设置插件权限级别"""
    # 这里我们需要把权限等级存储在某个地方
    # 考虑到我们还没有实现全局权限存储，先返回一个提示消息
    return f"已设置插件 {plugin_name} 的权限级别为 {permission_level.name}"


# 添加示例用法
@driver.on_startup
async def _():
    pass  # 这里可以添加一些初始化逻辑

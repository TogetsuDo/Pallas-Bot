"""权限管理模块，提供颗粒化的插件权限控制和开关。"""

from collections.abc import Callable
from enum import Enum
from functools import wraps
from typing import Optional, Type, Union

from nonebot import get_bot, get_driver, logger
from nonebot.adapters import Bot, Event
from nonebot.adapters.onebot.v11 import GroupMessageEvent, PrivateMessageEvent
from nonebot.exception import IgnoredException
from nonebot.matcher import Matcher
from nonebot.plugin import get_loaded_plugins

from src.common.db.modules import BotConfigModule, GroupConfigModule, UserConfigModule

# 全局权限配置
driver = get_driver()


class PermissionLevel(Enum):
    """权限等级"""

    BANNED = 0  # 禁止使用
    USER = 1  # 普通用户
    ADMIN = 2  # 群管理员
    OWNER = 3  # 群主
    SUPERUSER = 4  # 超级用户


class PluginPermission:
    """插件权限控制器"""

    def __init__(self, plugin_name: str):
        """
        初始化插件权限控制器

        Args:
            plugin_name: 插件名称
        """
        self.plugin_name = plugin_name

    async def is_plugin_enabled(self, event: Event) -> bool:
        """
        检查插件是否启用

        Args:
            event: 消息事件

        Returns:
            bool: 插件是否启用
        """
        # 获取事件相关信息
        bot_id = int(event.self_id)

        # 检查全局开关
        bot_config = await BotConfigModule.find_one({"account": bot_id})
        if not bot_config:
            # 如果没有配置，默认启用
            return True

        # 检查机器人级别的插件开关
        bot_plugins = getattr(bot_config, "disabled_plugins", {})
        if self.plugin_name in bot_plugins:
            return False

        # 检查群级别的插件开关
        if isinstance(event, GroupMessageEvent):
            group_id = event.group_id
            group_config = await GroupConfigModule.find_one({"group_id": group_id})
            if group_config:
                group_plugins = getattr(group_config, "disabled_plugins", {})
                if self.plugin_name in group_plugins:
                    return False

        return True

    async def check_permission(self, event: Event, required_level: PermissionLevel = PermissionLevel.USER) -> bool:
        """
        检查用户是否有权限使用插件

        Args:
            event: 消息事件
            required_level: 所需权限等级

        Returns:
            bool: 是否有权限
        """
        # 先检查插件是否启用
        if not await self.is_plugin_enabled(event):
            return False

        # 获取事件相关信息
        bot_id = int(event.self_id)
        user_id = event.get_user_id()

        # 检查用户是否被禁用
        user_config = await UserConfigModule.find_one({"user_id": int(user_id)})
        if user_config and user_config.banned:
            return False

        # 检查超级用户权限
        bot_config = await BotConfigModule.find_one({"account": bot_id})
        if bot_config and int(user_id) in bot_config.admins:
            return True

        # 如果是群消息，检查群权限
        if isinstance(event, GroupMessageEvent):
            group_id = event.group_id

            # 检查群是否被禁用
            group_config = await GroupConfigModule.find_one({"group_id": group_id})
            if group_config and group_config.banned:
                return False

            # 检查用户在群中的权限
            if required_level == PermissionLevel.USER:
                return True
            elif required_level == PermissionLevel.ADMIN:
                return event.sender.role in ["admin", "owner"] or int(user_id) in (
                    bot_config.admins if bot_config else []
                )
            elif required_level == PermissionLevel.OWNER:
                return event.sender.role == "owner" or int(user_id) in (bot_config.admins if bot_config else [])
            elif required_level == PermissionLevel.SUPERUSER:
                return int(user_id) in (bot_config.admins if bot_config else [])

        # 如果是私聊消息
        elif isinstance(event, PrivateMessageEvent):
            # 私聊默认只有超管可以使用需要SUPERUSER权限的功能
            if required_level == PermissionLevel.SUPERUSER:
                return bot_config and int(user_id) in bot_config.admins
            else:
                return True

        return False


def permission_check(
    plugin_name: str | None = None,
    required_level: PermissionLevel = PermissionLevel.USER,
    skip_plugin_check: bool = False,
):
    """
    权限检查装饰器，用于检查用户是否有权限使用功能

    Args:
        plugin_name: 插件名称，如果为None，则自动获取
        required_level: 所需权限等级
        skip_plugin_check: 是否跳过插件启用检查

    Returns:
        装饰器函数
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(matcher: type[Matcher], event: Event, *args, **kwargs):
            # 获取插件名称
            actual_plugin_name = plugin_name
            if actual_plugin_name is None:
                # 尝试自动获取插件名称
                for plugin in get_loaded_plugins():
                    if matcher in plugin.matcher:
                        actual_plugin_name = plugin.name
                        break

            if actual_plugin_name is None:
                logger.warning(f"无法确定 {matcher} 所属的插件名称，权限检查将被跳过")
                return await func(matcher, event, *args, **kwargs)

            # 创建权限控制器
            permission_controller = PluginPermission(actual_plugin_name)

            # 检查插件是否启用
            if not skip_plugin_check and not await permission_controller.is_plugin_enabled(event):
                logger.info(f"插件 {actual_plugin_name} 在当前上下文中被禁用")
                raise IgnoredException(f"插件 {actual_plugin_name} 在当前上下文中被禁用")

            # 检查权限
            if not await permission_controller.check_permission(event, required_level):
                logger.info(f"用户 {event.get_user_id()} 没有使用 {actual_plugin_name} 插件的 {required_level} 级权限")
                raise IgnoredException(
                    f"用户 {event.get_user_id()} 没有使用 {actual_plugin_name} 插件的 {required_level} 级权限"
                )

            return await func(matcher, event, *args, **kwargs)

        return wrapper

    return decorator

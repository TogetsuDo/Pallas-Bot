from nonebot import get_bot
from nonebot.plugin import PluginMetadata

from pallas.core.commands import command_perm_list, command_perm_row
from pallas.core.perm.metadata_defaults import (
    PLUGIN_EXTRA_VERSION,
    PLUGIN_HOMEPAGE,
    PLUGIN_MENU_TEMPLATE,
)
from pallas.core.perm.metadata_text import SCENE_AUTO, SCENE_GROUP, SCENE_PRIVATE, join_usage, usage_line

from . import commands as _commands  # noqa: F401
from .commands import call_me_message_rule, greeting_plugin_disabled, handle_notice

__plugin_meta__ = PluginMetadata(
    name="牛牛欢迎",
    description="入群/好友欢迎与自定义欢迎图文。",
    usage=join_usage(
        usage_line("设置好友欢迎 / 清除好友欢迎", "私聊维护新好友欢迎"),
        usage_line("设置群欢迎 / 清除群欢迎", "群内维护入群欢迎"),
    ),
    type="application",
    homepage=PLUGIN_HOMEPAGE,
    supported_adapters={"~onebot.v11"},
    extra={
        "version": PLUGIN_EXTRA_VERSION,
        "menu_template": PLUGIN_MENU_TEMPLATE,
        "reload_policy": "metadata",
        "command_permissions": command_perm_list(
            command_perm_row("greeting.set_friend_welcome", "设置好友欢迎", "bot_moderator"),
            command_perm_row("greeting.clear_friend_welcome", "清除好友欢迎", "bot_moderator"),
            command_perm_row("greeting.set_group_welcome", "设置群欢迎", "group_moderator"),
            command_perm_row("greeting.clear_group_welcome", "清除群欢迎", "group_moderator"),
        ),
        "menu_data": [
            {
                "func": "入群欢迎",
                "trigger_method": "on_notice",
                "trigger_scene": SCENE_AUTO,
                "trigger_condition": "新人入群",
                "brief_des": "发送入群欢迎",
                "detail_des": "若本群已「设置群欢迎」则优先发自定义内容，否则发默认欢迎。",
            },
            {
                "func": "好友欢迎",
                "trigger_method": "on_notice",
                "trigger_scene": SCENE_AUTO,
                "trigger_condition": "新好友添加",
                "brief_des": "发送好友欢迎",
                "detail_des": "若已「设置好友欢迎」则发送你保存的图文内容。",
            },
            {
                "func": "设置好友欢迎",
                "trigger_method": "on_cmd",
                "trigger_scene": SCENE_PRIVATE,
                "trigger_condition": "设置好友欢迎",
                "command_permission": "greeting.set_friend_welcome",
                "brief_des": "自定义新好友欢迎",
                "detail_des": "私聊按提示发送文本、图片或图文混合。",
            },
            {
                "func": "清除好友欢迎",
                "trigger_method": "on_cmd",
                "trigger_scene": SCENE_PRIVATE,
                "trigger_condition": "清除好友欢迎",
                "command_permission": "greeting.clear_friend_welcome",
                "brief_des": "恢复默认好友欢迎",
                "detail_des": "清除已保存的好友欢迎素材。",
            },
            {
                "func": "设置群欢迎",
                "trigger_method": "on_cmd",
                "trigger_scene": SCENE_GROUP,
                "trigger_condition": "设置群欢迎",
                "command_permission": "greeting.set_group_welcome",
                "brief_des": "自定义本群入群欢迎",
                "detail_des": "群内按提示发送文本、图片或图文混合。",
            },
            {
                "func": "清除群欢迎",
                "trigger_method": "on_cmd",
                "trigger_scene": SCENE_GROUP,
                "trigger_condition": "清除群欢迎",
                "command_permission": "greeting.clear_group_welcome",
                "brief_des": "恢复默认入群欢迎",
                "detail_des": "清除本群已保存的入群欢迎素材。",
            },
        ],
    },
)

__all__ = ["call_me_message_rule", "get_bot", "greeting_plugin_disabled", "handle_notice"]

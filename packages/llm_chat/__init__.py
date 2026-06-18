from nonebot.plugin import PluginMetadata

from pallas.core.commands import command_limit_list, command_limit_row, command_perm_list, command_perm_row
from pallas.core.perm.metadata_defaults import (
    PLUGIN_EXTRA_VERSION,
    PLUGIN_HOMEPAGE,
    PLUGIN_MENU_TEMPLATE,
)
from pallas.core.perm.metadata_text import SCENE_GROUP, join_usage, usage_line
from pallas.product.llm.tools.declare import llm_command_tool_row

from . import admin_commands as _admin_commands  # noqa: F401
from . import chat_message as _chat_message  # noqa: F401
from . import commands as _commands  # noqa: F401
from . import status_commands as _status_commands  # noqa: F401

__plugin_meta__ = PluginMetadata(
    name="随时闲聊",
    description="群内 @牛牛 多轮对话，支持清空会话记忆。",
    usage=join_usage(
        usage_line("群内 @牛牛 + 消息", "与牛牛多轮对话"),
        usage_line("@牛牛 clear", "清空本群当前会话记忆"),
    ),
    type="application",
    homepage=PLUGIN_HOMEPAGE,
    supported_adapters={"~onebot.v11"},
    extra={
        "version": PLUGIN_EXTRA_VERSION,
        "menu_template": PLUGIN_MENU_TEMPLATE,
        "reload_policy": "metadata",
        "ingress_route": {"lane": "remote"},
        "help_aliases": ["牛牛聊天", "智能闲聊"],
        "command_permissions": command_perm_list(
            command_perm_row("llm_chat.chat", "随时闲聊", "everyone"),
            command_perm_row("llm_chat.clear", "清空会话", "everyone"),
            command_perm_row("llm_chat.switch_model", "换模型", "superuser"),
            command_perm_row("llm_chat.unload_model", "卸模型", "superuser"),
            command_perm_row("llm_chat.status", "LLM 状态", "superuser"),
        ),
        "command_limits": command_limit_list(
            command_limit_row("llm_chat.chat", 3),
        ),
        "llm_tools": [
            llm_command_tool_row(
                name="llm_chat.clear",
                command_id="llm_chat.clear",
                description="清空当前用户与本 bot 的多轮 LLM 会话记忆。用户明确要求忘记聊过的内容时使用。",
                parameters={"type": "object", "properties": {}},
                command_template="clear",
            ),
        ],
        "menu_data": [
            {
                "func": "随时闲聊",
                "trigger_method": "on_message",
                "trigger_scene": SCENE_GROUP,
                "trigger_condition": "群内 @牛牛 发消息",
                "command_permission": "llm_chat.chat",
                "brief_des": "多轮对话，口癖与人设",
                "detail_des": "像和牛牛发消息一样 @ 即可；会按会话记住上文，话太多时会自动忘远一点的记录。",
            },
            {
                "func": "清空和牛牛的记录",
                "trigger_method": "on_cmd",
                "trigger_scene": SCENE_GROUP,
                "trigger_condition": "@牛牛 clear",
                "command_permission": "llm_chat.clear",
                "brief_des": "忘掉本轮聊天里说过的话",
                "detail_des": "只清对话内容，牛牛该怎么说话的人设仍会保留。",
            },
        ],
    },
)

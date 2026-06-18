from nonebot.plugin import PluginMetadata

from pallas.core.commands import command_perm_list, command_perm_row
from pallas.core.perm.metadata_defaults import (
    PLUGIN_EXTRA_VERSION,
    PLUGIN_HOMEPAGE,
    PLUGIN_MENU_TEMPLATE,
)
from pallas.core.perm.metadata_text import SCENE_PRIVATE, join_usage, usage_line

from . import commands as _commands  # noqa: F401
from . import startup as _startup  # noqa: F401
from .runtime import request_handler_plugin_disabled
from .texts import REQUEST_HANDLER_USAGE_LINES

__plugin_meta__ = PluginMetadata(
    name="申请管理",
    description="好友/入群申请提醒与审批，支持自动同意开关。",
    usage=join_usage(
        *(usage_line(*line.split(" — ", 1)) for line in REQUEST_HANDLER_USAGE_LINES),
    ),
    type="application",
    homepage=PLUGIN_HOMEPAGE,
    supported_adapters={"~onebot.v11"},
    extra={
        "version": PLUGIN_EXTRA_VERSION,
        "menu_template": PLUGIN_MENU_TEMPLATE,
        "reload_policy": "metadata",
        "disable_scope": "bot",
        "command_permissions": command_perm_list(
            command_perm_row("request.list_friends", "查看好友申请", "bot_moderator"),
            command_perm_row("request.list_groups", "查看入群申请", "bot_moderator"),
            command_perm_row("request.approve_latest", "同意（快捷）", "bot_moderator"),
            command_perm_row("request.reject_latest", "拒绝（快捷）", "bot_moderator"),
            command_perm_row("request.approve_friend", "同意好友", "bot_moderator"),
            command_perm_row("request.reject_friend", "拒绝好友", "bot_moderator"),
            command_perm_row("request.approve_all_friends", "同意所有好友", "bot_moderator"),
            command_perm_row("request.reject_all_friends", "拒绝所有好友", "bot_moderator"),
            command_perm_row("request.approve_all_groups", "同意所有入群申请", "bot_moderator"),
            command_perm_row("request.reject_all_groups", "拒绝所有入群申请", "bot_moderator"),
            command_perm_row("request.approve_group", "同意入群", "bot_moderator"),
            command_perm_row("request.reject_group", "拒绝入群", "bot_moderator"),
            command_perm_row("request.auto_accept_status", "查看自动同意", "bot_moderator"),
            command_perm_row("request.enable_auto_friend", "开启自动同意好友", "bot_moderator"),
            command_perm_row("request.disable_auto_friend", "关闭自动同意好友", "bot_moderator"),
            command_perm_row("request.enable_auto_group", "开启自动同意入群", "bot_moderator"),
            command_perm_row("request.disable_auto_group", "关闭自动同意入群", "bot_moderator"),
            command_perm_row("request.approval_reply", "引用审批消息快捷同意/拒绝", "bot_moderator"),
        ),
        "menu_data": [
            {
                "func": "查看待处理申请",
                "trigger_method": "on_cmd",
                "trigger_scene": SCENE_PRIVATE,
                "trigger_condition": "查看好友申请 / 查看入群申请",
                "command_permissions": ["request.list_friends", "request.list_groups"],
                "brief_des": "列出待处理好友与入群申请",
                "detail_des": "好友列表含被拦截、需单独处理的可疑申请；入群列表兼容旧口令“查看入群邀请”",
            },
            {
                "func": "快捷同意最近申请",
                "trigger_method": "on_cmd",
                "trigger_scene": SCENE_PRIVATE,
                "trigger_condition": "同意",
                "command_permission": "request.approve_latest",
                "brief_des": "快捷同意一条申请",
                "detail_des": "私聊「同意」对应牛牛最新一条提醒；引用某条审批提醒则只处理该条",
            },
            {
                "func": "快捷拒绝最近申请",
                "trigger_method": "on_cmd",
                "trigger_scene": SCENE_PRIVATE,
                "trigger_condition": "拒绝",
                "command_permission": "request.reject_latest",
                "brief_des": "快捷拒绝一条申请",
                "detail_des": "私聊「拒绝」对应牛牛最新一条提醒；引用某条审批提醒则只处理该条",
            },
            {
                "func": "引用审批消息快捷操作",
                "trigger_method": "on_message",
                "trigger_scene": SCENE_PRIVATE,
                "trigger_condition": "引用审批提醒：同意 / 好 / 留空，或 拒绝 / 不要 / 否",
                "command_permissions": [
                    "request.approval_reply",
                    "request.reject_friend",
                    "request.reject_group",
                ],
                "brief_des": "按引用对应单一申请同意或拒绝",
                "detail_des": "须引用仍有效的审批消息；同意与拒绝分别校验对应命令权限",
            },
            {
                "func": "好友申请审批",
                "trigger_method": "on_cmd",
                "trigger_scene": SCENE_PRIVATE,
                "trigger_condition": "同意好友 <QQ号>",
                "command_permission": "request.approve_friend",
                "brief_des": "按 QQ 同意好友",
                "detail_des": "同意指定 QQ 的好友申请（含普通与可疑申请）",
            },
            {
                "func": "好友申请拒绝",
                "trigger_method": "on_cmd",
                "trigger_scene": SCENE_PRIVATE,
                "trigger_condition": "拒绝好友 <QQ号>",
                "command_permission": "request.reject_friend",
                "brief_des": "按 QQ 拒绝好友",
                "detail_des": "拒绝指定 QQ 的好友申请（含普通与可疑申请）",
            },
            {
                "func": "批量审批",
                "trigger_method": "on_cmd",
                "trigger_scene": SCENE_PRIVATE,
                "trigger_condition": "同意所有好友 / 拒绝所有好友 / 同意所有入群 / 拒绝所有入群",
                "command_permissions": [
                    "request.approve_all_friends",
                    "request.reject_all_friends",
                    "request.approve_all_groups",
                    "request.reject_all_groups",
                ],
                "brief_des": "好友或入群批量同意/拒绝",
                "detail_des": "一次性同意或拒绝当前全部待处理好友申请或入群申请",
            },
            {
                "func": "入群申请审批",
                "trigger_method": "on_cmd",
                "trigger_scene": SCENE_PRIVATE,
                "trigger_condition": "同意入群 / 拒绝入群 <群号>",
                "command_permissions": ["request.approve_group", "request.reject_group"],
                "brief_des": "按群号同意或拒绝",
                "detail_des": "同意或拒绝指定群的入群申请",
            },
            {
                "func": "通知开关",
                "trigger_method": "on_cmd",
                "trigger_scene": SCENE_PRIVATE,
                "trigger_condition": "牛牛开启 / 牛牛关闭 申请管理",
                "command_permissions": ["help.plugin_enable", "help.plugin_disable"],
                "brief_des": "是否推送申请提醒",
                "detail_des": "私聊切换本牛是否推送好友/入群申请提醒（单牛全局；审批口令亦在私聊使用）",
            },
            {
                "func": "自动同意开关",
                "trigger_method": "on_cmd",
                "trigger_scene": SCENE_PRIVATE,
                "trigger_condition": "查看自动同意 / 开启或关闭自动同意好友 / 入群",
                "command_permissions": [
                    "request.auto_accept_status",
                    "request.enable_auto_friend",
                    "request.disable_auto_friend",
                    "request.enable_auto_group",
                    "request.disable_auto_group",
                ],
                "brief_des": "自动同意策略",
                "detail_des": "查看或切换好友申请、入群申请的自动同意开关",
            },
        ],
    },
)

__all__ = ["request_handler_plugin_disabled"]

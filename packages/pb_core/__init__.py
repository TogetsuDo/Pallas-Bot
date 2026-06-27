from nonebot.plugin import PluginMetadata

from pallas.core.commands import (
    bind_alias_handlers,
    command_limit_list,
    command_limit_row,
    command_perm_list,
    command_perm_row,
    message_command,
)
from pallas.core.perm.metadata_defaults import (
    PLUGIN_EXTRA_VERSION,
    PLUGIN_HOMEPAGE,
    PLUGIN_MENU_TEMPLATE,
)
from pallas.core.perm.metadata_text import SCENE_BOTH, SCENE_PRIVATE, join_usage, usage_line

from .handlers import (
    handle_add_bot_admin,
    handle_console,
    handle_plugins,
    handle_restart,
    handle_status,
    handle_update_check,
)

__plugin_meta__ = PluginMetadata(
    name="牛牛核心",
    description="查看牛牛的状态，并使用常用管理入口。",
    usage=join_usage(
        usage_line("牛牛状态", "查看当前状态"),
        usage_line("牛牛控制台", "查看网页入口"),
        usage_line("牛牛插件", "查看插件列表"),
        usage_line("牛牛更新", "查看更新情况"),
        usage_line("牛牛重启", "重新启动牛牛"),
        usage_line("牛牛添加号主 [牛牛QQ] 号主QQ", "为牛牛入库并添加号主"),
    ),
    type="application",
    homepage=PLUGIN_HOMEPAGE,
    supported_adapters={"~onebot.v11"},
    extra={
        "version": PLUGIN_EXTRA_VERSION,
        "help_audience": "superuser",
        "menu_template": PLUGIN_MENU_TEMPLATE,
        "command_permissions": command_perm_list(
            command_perm_row("pb_core.status", "牛牛状态", "staff"),
            command_perm_row("pb_core.console", "牛牛控制台", "staff"),
            command_perm_row("pb_core.plugins", "牛牛插件", "staff"),
            command_perm_row("pb_core.update_check", "牛牛更新", "superuser"),
            command_perm_row("pb_core.restart", "牛牛重启", "superuser"),
            command_perm_row("pb_core.add_bot_admin", "牛牛添加号主", "superuser"),
        ),
        "command_limits": command_limit_list(
            command_limit_row("pb_core.status", 10),
            command_limit_row("pb_core.console", 10),
            command_limit_row("pb_core.plugins", 15),
            command_limit_row("pb_core.update_check", 60),
            command_limit_row("pb_core.restart", 120),
            command_limit_row("pb_core.add_bot_admin", 30),
        ),
        "menu_data": [
            {
                "func": "牛牛状态",
                "trigger_method": "on_cmd",
                "trigger_scene": SCENE_BOTH,
                "trigger_condition": "牛牛状态",
                "help_audience": "superuser",
                "command_permission": "pb_core.status",
                "brief_des": "查看当前状态",
                "detail_des": "看看这只牛牛现在是否正常运行，以及一些基础信息。",
            },
            {
                "func": "牛牛控制台",
                "trigger_method": "on_cmd",
                "trigger_scene": SCENE_BOTH,
                "trigger_condition": "牛牛控制台",
                "command_permission": "pb_core.console",
                "brief_des": "查看网页入口",
                "detail_des": "直接拿到网页管理入口，方便打开后继续操作。",
            },
            {
                "func": "牛牛插件",
                "trigger_method": "on_cmd",
                "trigger_scene": SCENE_BOTH,
                "trigger_condition": "牛牛插件",
                "command_permission": "pb_core.plugins",
                "brief_des": "查看插件列表",
                "detail_des": "看看这只牛牛现在有哪些插件和功能可用。",
            },
            {
                "func": "牛牛更新",
                "trigger_method": "on_cmd",
                "trigger_scene": SCENE_BOTH,
                "trigger_condition": "牛牛更新",
                "command_permission": "pb_core.update_check",
                "brief_des": "查看更新情况",
                "detail_des": "看看当前版本离最新版本还有多远。",
            },
            {
                "func": "牛牛重启",
                "trigger_method": "on_cmd",
                "trigger_scene": SCENE_BOTH,
                "trigger_condition": "牛牛重启",
                "command_permission": "pb_core.restart",
                "brief_des": "重新启动牛牛",
                "detail_des": "在当前环境支持时，让这只牛牛重新启动。",
            },
            {
                "func": "牛牛添加号主",
                "trigger_method": "on_cmd",
                "trigger_scene": SCENE_PRIVATE,
                "command_permission": "pb_core.add_bot_admin",
                "brief_des": "为牛牛入库并添加号主",
                "detail_des": "将目标牛牛写入 bot_config，并把指定 QQ 加入 admins；多牛时可先写牛牛 QQ。",
            },
        ],
    },
)

status_cmd = message_command("pb_core.status", "牛牛状态", cd_sec=10)
console_cmd = message_command("pb_core.console", "牛牛控制台", cd_sec=10)
plugins_cmd = message_command("pb_core.plugins", "牛牛插件", cd_sec=15)
update_cmd = message_command("pb_core.update_check", "牛牛更新", cd_sec=60)
restart_cmd = message_command("pb_core.restart", "牛牛重启", cd_sec=120)
add_bot_admin_cmd = message_command("pb_core.add_bot_admin", "牛牛添加号主", cd_sec=30, scene="private")

bind_alias_handlers(status_cmd, handle_status)
bind_alias_handlers(console_cmd, handle_console)
bind_alias_handlers(plugins_cmd, handle_plugins)
bind_alias_handlers(update_cmd, handle_update_check)
bind_alias_handlers(restart_cmd, handle_restart)
bind_alias_handlers(add_bot_admin_cmd, handle_add_bot_admin)

from nonebot.plugin import PluginMetadata

from pallas.core.commands import command_limit_list, command_limit_row, command_perm_list, command_perm_row
from pallas.core.perm.metadata_defaults import (
    PLUGIN_EXTRA_VERSION,
    PLUGIN_HOMEPAGE,
    PLUGIN_MENU_TEMPLATE,
)
from pallas.core.perm.metadata_text import SCENE_BOTH, SCENE_GROUP, join_usage, usage_line
from pallas.core.storage.declare import plugin_storage_list, plugin_storage_row

from . import commands as _commands  # noqa: F401
from .style_cache import refresh_style_cache

__plugin_meta__ = PluginMetadata(
    name="牛牛帮助",
    description="三级帮助图与群内插件开关。",
    usage=join_usage(
        usage_line("牛牛帮助", "插件总览与开关状态"),
        usage_line("牛牛帮助 〈插件名或序号〉", "单插件功能表"),
        usage_line("牛牛帮助 〈插件〉 〈功能序号或名称〉", "单条功能详情"),
        usage_line("牛牛开启 / 牛牛关闭 〈插件名或序号〉", "本群开关某插件"),
        usage_line("牛牛开启全部功能 / 牛牛关闭全部功能", "本群批量开关"),
    ),
    type="application",
    homepage=PLUGIN_HOMEPAGE,
    supported_adapters={"~onebot.v11"},
    extra={
        "version": PLUGIN_EXTRA_VERSION,
        "menu_template": PLUGIN_MENU_TEMPLATE,
        "reload_policy": "metadata",
        "command_prefixes": [
            "牛牛帮助",
            "牛牛开启",
            "牛牛关闭",
            "牛牛开启全部功能",
            "牛牛关闭全部功能",
        ],
        "ingress_fanout": {
            "scope": "unified_only",
            "prefixes": [
                "牛牛帮助",
                "牛牛开启",
                "牛牛关闭",
                "牛牛开启全部功能",
                "牛牛关闭全部功能",
            ],
        },
        "command_permissions": command_perm_list(
            command_perm_row("help.help", "牛牛帮助", "everyone"),
            command_perm_row("help.plugin_enable", "牛牛开启（单插件）", "staff"),
            command_perm_row("help.plugin_disable", "牛牛关闭（单插件）", "staff"),
            command_perm_row("help.plugin_enable_all", "牛牛开启全部功能", "staff"),
            command_perm_row("help.plugin_disable_all", "牛牛关闭全部功能", "staff"),
        ),
        "command_limits": command_limit_list(
            command_limit_row("help.help", 3),
        ),
        "menu_data": [
            {
                "func": "总列表",
                "trigger_method": "on_cmd",
                "trigger_scene": SCENE_BOTH,
                "trigger_condition": "牛牛帮助",
                "command_permission": "help.help",
                "brief_des": "全部插件、状态与简介",
                "detail_des": "看图可知本群各插件是否启用；用序号或中文名继续打开下级。",
            },
            {
                "func": "插件详情",
                "trigger_method": "on_cmd",
                "trigger_scene": SCENE_BOTH,
                "trigger_condition": "牛牛帮助 〈插件名或序号〉",
                "command_permission": "help.help",
                "brief_des": "单插件说明与功能表",
                "detail_des": "含用法与「怎么说 / 场景 / 何人可用」；可再跟功能序号或名称看详情。",
            },
            {
                "func": "功能详情",
                "trigger_method": "on_cmd",
                "trigger_scene": SCENE_BOTH,
                "trigger_condition": "牛牛帮助 〈插件〉 〈功能序号或名称〉",
                "command_permission": "help.help",
                "brief_des": "单条功能的口令与说明",
                "detail_des": "展示完整口令、场景与「何人可用」。",
            },
            {
                "func": "插件开关",
                "trigger_method": "on_cmd",
                "trigger_scene": SCENE_GROUP,
                "trigger_condition": "牛牛开启 / 牛牛关闭 〈插件名或序号〉",
                "command_permissions": ["help.plugin_enable", "help.plugin_disable"],
                "brief_des": "本群启用或停用某插件",
                "detail_des": "例：牛牛开启 牛牛复读、牛牛关闭 1；命名规则同打开插件详情。",
            },
            {
                "func": "批量开关",
                "trigger_method": "on_cmd",
                "trigger_scene": SCENE_GROUP,
                "trigger_condition": "牛牛开启全部功能 / 牛牛关闭全部功能",
                "command_permissions": ["help.plugin_enable_all", "help.plugin_disable_all"],
                "brief_des": "本群一键全开或全关",
                "detail_des": "仅切换帮助总览中列出的插件，与总览数量一致。",
            },
        ],
        "plugin_storage": plugin_storage_list(
            plugin_storage_row("hidden_plugins", scope="deploy", label="帮助总览隐藏名单"),
            plugin_storage_row("global_disabled_plugins", scope="deploy", label="全实例禁用名单"),
        ),
    },
)

__all__ = ["refresh_style_cache"]

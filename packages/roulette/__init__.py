from nonebot.plugin import PluginMetadata

from pallas.core.commands import command_perm_list, command_perm_row
from pallas.core.perm.metadata_defaults import (
    PLUGIN_EXTRA_VERSION,
    PLUGIN_HOMEPAGE,
    PLUGIN_MENU_TEMPLATE,
)
from pallas.core.perm.metadata_text import SCENE_GROUP, join_usage, usage_line

from . import commands as _commands  # noqa: F401
from .game import parse_roulette_start_command

__plugin_meta__ = PluginMetadata(
    name="牛牛轮盘",
    description="在群里玩踢人或禁言轮盘，也能救人和补一枪。",
    usage=join_usage(
        usage_line("牛牛轮盘 / 牛牛轮盘踢人 / 牛牛轮盘禁言", "启动轮盘（默认禁言模式）"),
        usage_line("牛牛开枪", "参与当前局"),
        usage_line("牛牛救一下 [@用户]", "解除禁言，有概率炸膛"),
        usage_line("牛牛补一枪 [@用户]", "追加禁言，有概率炸膛"),
    ),
    type="application",
    homepage=PLUGIN_HOMEPAGE,
    supported_adapters={"~onebot.v11"},
    extra={
        "version": PLUGIN_EXTRA_VERSION,
        "menu_template": PLUGIN_MENU_TEMPLATE,
        "reload_policy": "metadata",
        "exact_plaintexts": [
            "牛牛轮盘",
            "牛牛轮盘踢人",
            "牛牛轮盘禁言",
            "牛牛踢人轮盘",
            "牛牛禁言轮盘",
            "牛牛开枪",
        ],
        "command_prefixes": ["牛牛救一下", "牛牛补一枪"],
        "ingress_fanout": {
            "scope": "always",
            "plaintexts": [
                "牛牛轮盘",
                "牛牛轮盘踢人",
                "牛牛轮盘禁言",
                "牛牛踢人轮盘",
                "牛牛禁言轮盘",
                "牛牛开枪",
            ],
            "prefixes": ["牛牛救一下", "牛牛补一枪"],
        },
        "command_permissions": command_perm_list(
            command_perm_row("roulette.mode_switch", "牛牛轮盘切换模式", "staff"),
        ),
        "menu_data": [
            {
                "func": "牛牛轮盘",
                "trigger_method": "on_message",
                "trigger_scene": SCENE_GROUP,
                "trigger_condition": "牛牛轮盘 / 牛牛轮盘踢人 / 牛牛轮盘禁言",
                "brief_des": "启动轮盘",
                "detail_des": "可选踢人或禁言模式；轮到谁中弹，就按当前模式执行结果。",
            },
            {
                "func": "参与轮盘",
                "trigger_method": "on_message",
                "trigger_scene": SCENE_GROUP,
                "trigger_condition": "牛牛开枪",
                "brief_des": "参与轮盘",
                "detail_des": "轮盘开始后，发「牛牛开枪」参与本局，结果按当前模式决定。",
            },
            {
                "func": "牛牛救一下",
                "trigger_method": "on_message",
                "trigger_scene": SCENE_GROUP,
                "trigger_condition": "牛牛救一下 [@用户]",
                "brief_des": "解除被禁言的用户",
                "detail_des": "不带 @ 时帮大家解禁，带 @ 时只救那个人；有时会翻车。",
            },
            {
                "func": "牛牛补一枪",
                "trigger_method": "on_message",
                "trigger_scene": SCENE_GROUP,
                "trigger_condition": "牛牛补一枪 [@用户]",
                "brief_des": "对已禁言玩家追加惩罚",
                "detail_des": "给已经中招的人再补一轮惩罚；可 @ 指定对象，也有翻车概率。",
            },
        ],
    },
)

__all__ = ["parse_roulette_start_command"]

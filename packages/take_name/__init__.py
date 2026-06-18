from nonebot.plugin import PluginMetadata

from pallas.core.perm.metadata_defaults import (
    PLUGIN_EXTRA_VERSION,
    PLUGIN_HOMEPAGE,
    PLUGIN_MENU_TEMPLATE,
)
from pallas.core.perm.metadata_text import SCENE_AUTO, join_usage, usage_line

from . import handlers as _handlers  # noqa: F401
from . import startup as _startup  # noqa: F401

__plugin_meta__ = PluginMetadata(
    name="自动夺舍",
    description="定时模仿群友名片，醉酒时可能改群友名片。",
    usage=join_usage(
        usage_line("（自动）", "随机改牛牛名片；醉酒时可能夺舍群友"),
    ),
    type="application",
    homepage=PLUGIN_HOMEPAGE,
    supported_adapters={"~onebot.v11"},
    extra={
        "version": PLUGIN_EXTRA_VERSION,
        "menu_template": PLUGIN_MENU_TEMPLATE,
        "menu_data": [
            {
                "func": "牛牛夺舍",
                "trigger_method": "scheduler",
                "trigger_scene": SCENE_AUTO,
                "trigger_condition": "随机模仿群友名片",
                "brief_des": "牛牛自动更换群名片",
                "detail_des": "牛牛每分钟有约0.2%的概率自动更换自己的群名片为群内随机用户的名片，并戳一戳该用户。",
            },
            {
                "func": "醉酒夺舍",
                "trigger_method": "scheduler",
                "trigger_scene": SCENE_AUTO,
                "trigger_condition": "牛牛醉酒时",
                "brief_des": "醉酒时随机更换群友名片",
                "detail_des": "当牛牛处于醉酒状态且为群管理员时，更换自己名片的同时有概率将被取名用户的名字改为固定名称（帕拉斯、牛牛等）。",  # noqa: E501
            },
            {
                "func": "名片同步",
                "trigger_method": "on_notice",
                "trigger_scene": SCENE_AUTO,
                "trigger_condition": "被模仿者改名",
                "brief_des": "同步被取名用户的群名片",
                "detail_des": "当被牛牛取名的用户修改自己的群名片时，牛牛会自动同步修改自己的群名片为该用户的新名片。",
            },
        ],
    },
)

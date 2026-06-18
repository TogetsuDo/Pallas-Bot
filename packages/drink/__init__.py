from nonebot.plugin import PluginMetadata

from pallas.core.perm.metadata_defaults import (
    PLUGIN_EXTRA_VERSION,
    PLUGIN_HOMEPAGE,
    PLUGIN_MENU_TEMPLATE,
)
from pallas.core.perm.metadata_text import SCENE_GROUP, join_usage, usage_line

from . import handlers as _handlers  # noqa: F401
from . import startup as _startup  # noqa: F401

__plugin_meta__ = PluginMetadata(
    name="牛牛喝酒",
    description="群内饮酒与醒酒，影响醉酒度及关联玩法。",
    usage=join_usage(
        usage_line("牛牛喝酒 / 牛牛干杯 / 牛牛继续喝", "增加醉酒度，可能睡着"),
        usage_line("牛牛醒一醒 / 牛牛别喝了", "立即醒酒；本群在做梦时一并醒梦"),
    ),
    type="application",
    homepage=PLUGIN_HOMEPAGE,
    supported_adapters={"~onebot.v11"},
    extra={
        "version": PLUGIN_EXTRA_VERSION,
        "menu_template": PLUGIN_MENU_TEMPLATE,
        "ingress_fanout": {
            "scope": "always",
            "plaintexts": [
                "牛牛喝酒",
                "牛牛干杯",
                "牛牛继续喝",
                "牛牛醒一醒",
                "牛牛别喝了",
            ],
        },
        "menu_data": [
            {
                "func": "牛牛喝酒",
                "trigger_method": "on_message",
                "trigger_scene": SCENE_GROUP,
                "trigger_condition": "牛牛喝酒 / 牛牛干杯 / 牛牛继续喝",
                "brief_des": "饮酒并进入醉酒",
                "detail_des": "醉酒会影响聊天、轮盘、夺舍等；程度过高可能睡着，之后会自动清醒。",
            },
            {
                "func": "牛牛醒一醒",
                "trigger_method": "on_message",
                "trigger_scene": SCENE_GROUP,
                "trigger_condition": "牛牛醒一醒 / 牛牛别喝了",
                "brief_des": "立即醒酒",
                "detail_des": "清除醉酒；若本群正在「牛牛做梦」则同时结束做梦。",
            },
        ],
    },
)

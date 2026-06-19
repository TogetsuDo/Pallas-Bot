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
    description="让牛牛喝酒、醒酒，并影响它接下来的表现。",
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
                "detail_des": "喝得越多越容易醉，醉酒后说话和行为都会变得不一样，太过头还会睡着。",
            },
            {
                "func": "牛牛醒一醒",
                "trigger_method": "on_message",
                "trigger_scene": SCENE_GROUP,
                "trigger_condition": "牛牛醒一醒 / 牛牛别喝了",
                "brief_des": "立即醒酒",
                "detail_des": "让牛牛立刻清醒；如果它正在做梦，也会一起停下来。",
            },
        ],
    },
)

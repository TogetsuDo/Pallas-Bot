from nonebot.plugin import PluginMetadata

from pallas.core.perm.metadata_defaults import (
    PLUGIN_EXTRA_VERSION,
    PLUGIN_HOMEPAGE,
    PLUGIN_MENU_TEMPLATE,
)

from . import startup as _startup  # noqa: F401

__plugin_meta__ = PluginMetadata(
    name="在线统计",
    description="向社区统计中心上报部署心跳；配置见 WebUI 通用配置。",
    usage="（维护者）WebUI「通用配置 → 在线统计与社区主站」；默认开启。",
    type="application",
    homepage=PLUGIN_HOMEPAGE,
    supported_adapters={"~onebot.v11"},
    extra={
        "version": PLUGIN_EXTRA_VERSION,
        "menu_template": PLUGIN_MENU_TEMPLATE,
        "help_audience": "maintainer",
        "menu_data": [
            {
                "func": "在线统计上报",
                "trigger_method": "http",
                "help_audience": "maintainer",
                "trigger_condition": "WebUI 通用配置 → 在线统计与社区主站",
                "brief_des": "社区主站心跳",
                "detail_des": "周期上报部署与牛牛聚合信息；无群内口令。",
            },
        ],
    },
)

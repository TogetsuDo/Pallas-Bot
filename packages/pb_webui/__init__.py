# ruff: noqa: E501
from nonebot.plugin import PluginMetadata

from pallas.core.perm.metadata_defaults import (
    PLUGIN_EXTRA_VERSION,
    PLUGIN_HOMEPAGE,
    PLUGIN_MENU_TEMPLATE,
)
from pallas.core.perm.metadata_text import join_usage, usage_line

from . import startup as _startup  # noqa: F401

__plugin_meta__ = PluginMetadata(
    name="Web 控制台",
    description="浏览器运维控制台与扩展 API。",
    usage=join_usage(
        usage_line("/pallas/", "控制台页面"),
        usage_line("/pallas/api/*", "实例、日志、数据库与插件统计等接口"),
    ),
    type="application",
    homepage=PLUGIN_HOMEPAGE,
    supported_adapters={"~onebot.v11"},
    extra={
        "version": PLUGIN_EXTRA_VERSION,
        "menu_template": PLUGIN_MENU_TEMPLATE,
        "help_audience": "maintainer",
        "reload_policy": "metadata",
        "menu_data": [
            {
                "func": "控制台页面",
                "trigger_method": "http",
                "help_audience": "maintainer",
                "trigger_condition": "/pallas/",
                "brief_des": "提供控制台界面",
                "detail_des": "展示实例状态、日志、数据库与插件信息。",
            },
            {
                "func": "扩展状态接口",
                "trigger_method": "http",
                "help_audience": "maintainer",
                "trigger_condition": "/pallas/api/*",
                "brief_des": "提供控制台数据接口",
                "detail_des": "提供 health、system、instances、logs、message-stats 等接口。",
            },
        ],
    },
)

# ruff: noqa: E501
from nonebot.plugin import PluginMetadata

from pallas.core.perm.metadata_defaults import (
    PLUGIN_EXTRA_VERSION,
    PLUGIN_HOMEPAGE,
    PLUGIN_MENU_TEMPLATE,
)
from pallas.core.perm.metadata_text import join_usage, usage_line

from .config import plugin_config
from .startup import ensure_registered


def _register_if_driver_ready() -> None:
    try:
        from nonebot import get_driver

        get_driver()
    except ValueError:
        return
    ensure_registered()


def __getattr__(name: str):
    if name == "manager":
        ensure_registered()
        from .startup import manager as protocol_manager

        return protocol_manager
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


_register_if_driver_ready()

__plugin_meta__ = PluginMetadata(
    name="协议端管理",
    description="NapCat/SnowLuma 协议端账号管理与 Web 控制台。",
    usage=join_usage(
        usage_line("/protocol/console", "协议端管理页"),
        usage_line("X-Pallas-Protocol-Token / ?token=", "API 鉴权"),
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
                "func": "协议端管理页",
                "trigger_method": "http",
                "help_audience": "maintainer",
                "trigger_condition": "/protocol/console",
                "brief_des": "管理协议账号与进程",
                "detail_des": "可在页面执行创建账号、启动、停止、重启与日志查看。",
            },
            {
                "func": "协议端 API",
                "trigger_method": "http",
                "help_audience": "maintainer",
                "trigger_condition": "/protocol/*",
                "brief_des": "提供协议管理接口",
                "detail_des": "提供账号、配置、协议端发行包下载与状态查询接口。",
            },
        ],
    },
)

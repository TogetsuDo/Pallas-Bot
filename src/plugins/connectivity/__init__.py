from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="牛牛连通检测",
    description="检测画画网关、MAA 远控端点与唱歌服务延迟",
    usage="""
在群内发：
· 「牛牛连通」或 「牛牛网关」— 检测画画网关、MAA 获取/汇报端点、唱歌服务连通与延迟
    """.strip(),
    type="application",
    homepage="https://github.com/PallasBot",
    supported_adapters={"~onebot.v11"},
    extra={
        "version": "3.0.0",
        "command_permissions": [
            {"id": "connectivity.probe", "label": "牛牛连通", "default": "everyone"},
        ],
        "menu_data": [
            {
                "func": "牛牛连通",
                "trigger_method": "on_cmd",
                "trigger_scene": "群内",
                "trigger_condition": "牛牛连通 / 牛牛网关",
                "command_permission": "connectivity.probe",
                "brief_des": "检测画画、MAA 远控与唱歌服务延迟",
                "detail_des": ("并行探测画画 API 网关、MAA getTask/reportStatus 端点及唱歌 AI 服务。"),
            },
        ],
        "menu_template": "default",
    },
)

from . import commands as _connectivity_commands  # noqa: E402, F401

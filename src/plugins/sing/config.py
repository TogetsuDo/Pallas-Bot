from pydantic import BaseModel, Field

from src.common.webui import install_hot_reload_config


class Config(BaseModel, extra="ignore"):
    ai_server_host: str = Field(default="127.0.0.1", description="歌唱/音频所用 AI 服务主机。")
    ai_server_port: int = Field(default=9099, description="AI 服务端口。")
    sing_enable: bool = Field(default=False, description="是否启用唱歌、合成与播放相关指令（需服务支持）。")
    sing_endpoint: str = Field(default="/api/sing", description="提交歌唱合成的 API 路径。")
    play_endpoint: str = Field(default="/api/play", description="获取或触发播放的 API 路径。")
    request_endpoint: str = Field(default="/api/request", description="唱歌/排队请求的 API 路径。")
    sing_length: int = Field(default=120, description="单次合成音频的默认最大时长（秒），具体以后端为准。")
    sing_speakers: dict[str, str] = Field(
        default_factory=lambda: {
            "帕拉斯": "pallas",
            "牛牛": "pallas",
        },
        description="唱歌的音色映射",
    )


plugin_webui = install_hot_reload_config(Config, config_module=__name__)
get_sing_config = plugin_webui.get
reload_sing_config = plugin_webui.reload
clear_sing_config_cache = plugin_webui.clear_cache


def sing_server_url(cfg: Config | None = None) -> str:
    c = cfg or get_sing_config()
    return f"http://{c.ai_server_host}:{c.ai_server_port}"

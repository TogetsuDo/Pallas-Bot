from pydantic import BaseModel, Field


class Config(BaseModel, extra="ignore"):
    ai_server_host: str = Field(default="127.0.0.1", description="歌唱/音频所用 AI 服务主机。")
    ai_server_port: int = Field(default=9099, description="AI 服务端口。")
    sing_enable: bool = Field(default=False, description="是否启用点歌、合成与播放相关指令（需服务支持）。")
    sing_endpoint: str = Field(default="/api/sing", description="提交歌唱合成的 API 路径。")
    play_endpoint: str = Field(default="/api/play", description="获取或触发播放的 API 路径。")
    request_endpoint: str = Field(default="/api/request", description="点歌/排队请求的 API 路径。")
    sing_length: int = Field(default=120, description="单次合成音频的默认最大时长（秒），具体以后端为准。")
    sing_speakers: dict[str, str] = Field(
        default_factory=lambda: {
            "帕拉斯": "pallas",
            "牛牛": "pallas",
        },
        description="唱歌的音色映射",
    )

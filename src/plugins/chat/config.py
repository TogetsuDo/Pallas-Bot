from pydantic import BaseModel, Field


class Config(BaseModel, extra="ignore"):
    ai_server_host: str = Field(default="127.0.0.1", description="Pallas-Bot-AI（或兼容服务）的主机地址。")
    ai_server_port: int = Field(default=9099, description="AI 服务监听端口。")
    chat_enable: bool = Field(default=False, description="是否启用文字对话（需 AI 服务已部署且可访问）。")
    chat_endpoint: str = Field(default="/api/chat", description="发起聊天的 HTTP 路径。")
    del_session_endpoint: str = Field(default="/api/del_session", description="清除会话记忆的 HTTP 路径。")
    tts_enable: bool = Field(default=False, description="是否在对话中启用服务端语音合成（依赖 AI 端能力）。")

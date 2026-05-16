from __future__ import annotations

import json
import os
from threading import Lock
from typing import Any, Self

from nonebot import get_plugin_config
from pydantic import BaseModel, Field

from src.common.env_dotenv import merged_repo_dotenv_upper, repo_layered_dotenv_files_exist


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

    @classmethod
    def from_env(cls) -> Self:
        merged = merged_repo_dotenv_upper()
        data: dict[str, Any] = {}
        for name, field in cls.model_fields.items():
            key = name.upper()
            raw: str | None = None
            if key in os.environ:
                raw = os.environ.get(key)
            elif key in merged:
                raw = merged[key]
            if raw is None:
                continue
            data[name] = parse_sing_env_value(name, str(raw), field.annotation)
        return cls.model_validate(data)


def parse_sing_env_value(name: str, raw: str, ann: Any) -> Any:
    text = raw.strip()
    ann_text = str(ann).lower()
    if "bool" in ann_text:
        return text.lower() in ("1", "true", "yes", "on")
    if "dict" in ann_text:
        if not text:
            return {}
        return json.loads(text)
    if "int" in ann_text:
        return int(text)
    return text


_config_lock = Lock()
_cached_sing_config: Config | None = None


def clear_sing_config_cache() -> None:
    global _cached_sing_config
    with _config_lock:
        _cached_sing_config = None


def get_sing_config() -> Config:
    global _cached_sing_config
    with _config_lock:
        if _cached_sing_config is None:
            if repo_layered_dotenv_files_exist():
                _cached_sing_config = Config.from_env()
            else:
                _cached_sing_config = get_plugin_config(Config)
        return _cached_sing_config


def sing_server_url(cfg: Config | None = None) -> str:
    c = cfg or get_sing_config()
    return f"http://{c.ai_server_host}:{c.ai_server_port}"


def reload_sing_config() -> None:
    """WebUI 写入 .env 后调用，使唱歌相关配置立即生效。"""
    clear_sing_config_cache()
    get_sing_config()

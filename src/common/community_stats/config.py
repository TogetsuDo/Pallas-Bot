"""社区统计 opt-in 上报配置（pallas.toml [community_stats] 或环境变量）。"""

from __future__ import annotations

import os
from functools import lru_cache

from pydantic import BaseModel, ConfigDict, Field

from src.common.config.dotenv import merged_repo_dotenv_upper

_PREFIX = "PALLAS_COMMUNITY_STATS_"


def _env_str(name: str, default: str = "") -> str:
    merged = merged_repo_dotenv_upper()
    if name in os.environ:
        return (os.environ.get(name, default) or "").strip()
    return (merged.get(name) or default).strip()


def _env_int(name: str, default: int) -> int:
    raw = _env_str(name, str(default))
    try:
        return int(raw)
    except ValueError:
        return default


def _env_bool(name: str, default: bool) -> bool:
    raw = _env_str(name, "").lower()
    if not raw:
        return default
    return raw not in ("0", "false", "no", "off")


class CommunityStatsConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    enabled: bool = Field(default=True, description="是否向社区统计中心上报心跳。")
    endpoint: str = Field(
        default="https://stats.pallasbot.top/v1/heartbeat",
        description="心跳 URL（POST）。",
    )
    token: str = Field(default="", description="与中心 HEARTBEAT_TOKEN 一致的 Bearer。")
    interval_sec: int = Field(default=300, ge=60, le=3600, description="周期上报间隔（秒）。")


@lru_cache(maxsize=1)
def get_community_stats_config() -> CommunityStatsConfig:
    return CommunityStatsConfig(
        enabled=_env_bool(f"{_PREFIX}ENABLED", True),
        endpoint=_env_str(f"{_PREFIX}ENDPOINT", "https://stats.pallasbot.top/v1/heartbeat"),
        token=_env_str(f"{_PREFIX}TOKEN", ""),
        interval_sec=_env_int(f"{_PREFIX}INTERVAL_SEC", 300),
    )


def clear_community_stats_config_cache() -> None:
    get_community_stats_config.cache_clear()

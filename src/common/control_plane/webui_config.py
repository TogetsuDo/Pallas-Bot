"""WebUI 通用配置：控制面 bootstrap 与联邦 ingress。"""

from __future__ import annotations

from functools import lru_cache

from pydantic import BaseModel, ConfigDict, Field

from src.common.config.repo_settings import repo_env_raw_value
from src.common.corpus.config import parse_tristate


def setting_str(name: str, default: str = "") -> str:
    raw = repo_env_raw_value(name)
    if raw is None:
        return default
    return (raw or "").strip() or default


class ControlPlaneWebuiConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    enabled: bool = Field(default=True, description="拉取中心 bootstrap（federate_id、协调 Redis）")
    bootstrap_url: str = Field(
        default="",
        description="留空则从社区心跳域推导 /v1/bootstrap",
    )
    instance_secret: str = Field(
        default="",
        description="与中心 INSTANCE_SECRET 一致；bootstrap 鉴权",
    )
    federate_id: str = Field(
        default="",
        description="联邦池 ID；可留空由 bootstrap 落盘",
    )
    federate_ingress_enabled: str = Field(
        default="auto",
        description="跨 deployment ingress 去重：auto | true | false",
    )
    federate_redis_prefix: str = Field(
        default="",
        description="协调 Redis key 前缀；留空由 bootstrap 或按 federate_id 生成",
    )
    coord_redis_url: str = Field(
        default="",
        description="协调 Redis URL；留空由 bootstrap 下发",
    )


@lru_cache(maxsize=1)
def get_control_plane_webui_config() -> ControlPlaneWebuiConfig:
    enabled_raw = setting_str("PALLAS_CONTROL_PLANE_ENABLED", "true")
    enabled_flag = parse_tristate(enabled_raw, default=True)
    return ControlPlaneWebuiConfig(
        enabled=enabled_flag is not False,
        bootstrap_url=setting_str("PALLAS_CONTROL_PLANE_BOOTSTRAP_URL"),
        instance_secret=setting_str("PALLAS_INSTANCE_SECRET"),
        federate_id=setting_str("PALLAS_FEDERATE_ID"),
        federate_ingress_enabled=setting_str("PALLAS_FEDERATE_INGRESS_ENABLED", "auto") or "auto",
        federate_redis_prefix=setting_str("PALLAS_FEDERATE_REDIS_PREFIX"),
        coord_redis_url=setting_str("PALLAS_COORD_REDIS_URL") or setting_str("REDIS_URL"),
    )


def clear_control_plane_webui_config_cache() -> None:
    get_control_plane_webui_config.cache_clear()

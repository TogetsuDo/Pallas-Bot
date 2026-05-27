"""WebUI 通用配置：控制面 bootstrap 与联邦 ingress。"""

from __future__ import annotations

from functools import lru_cache

from pydantic import BaseModel, ConfigDict, Field

from src.features.corpus.config import parse_tristate
from src.foundation.config.repo_settings import repo_env_raw_value, repo_webui_settings_path

_FEDERATE_COORD_URL_KEY = "PALLAS_FEDERATE_COORD_REDIS_URL"
_LEGACY_COORD_URL_KEY = "PALLAS_COORD_REDIS_URL"


def setting_str(name: str, default: str = "") -> str:
    raw = repo_env_raw_value(name)
    if raw is None:
        return default
    return (raw or "").strip() or default


class ControlPlaneWebuiConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    enabled: bool = Field(default=True, description="是否向中心自动领取联邦配置")
    bootstrap_url: str = Field(default="", description="中心配置地址，留空则自动选择主站或备站")
    instance_secret: str = Field(default="", description="入池密钥，与中心一致")
    federate_id: str = Field(default="", description="联邦池编号，可留空由中心写入")
    federate_ingress_enabled: str = Field(default="auto", description="重复消息去重：自动、开启或关闭")
    federate_redis_prefix: str = Field(default="", description="去重键前缀，一般留空")
    coord_redis_url: str = Field(default="", description="去重服务器地址，一般留空由中心下发")


def repair_misplaced_federate_redis_env() -> bool:
    """修正误将分片 REDIS_URL 写入 PALLAS_COORD_REDIS_URL 的情况。"""
    import json

    path = repo_webui_settings_path()
    if not path.is_file():
        return False
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    if not isinstance(doc, dict):
        return False
    env = doc.get("env")
    if not isinstance(env, dict):
        return False
    redis_url = str(env.get("REDIS_URL") or "").strip()
    coord_url = str(env.get(_LEGACY_COORD_URL_KEY) or "").strip()
    fed_url = str(env.get(_FEDERATE_COORD_URL_KEY) or "").strip()
    changed = False
    if fed_url and coord_url == fed_url and coord_url != redis_url:
        env.pop(_LEGACY_COORD_URL_KEY, None)
        changed = True
    if not fed_url and coord_url and redis_url and coord_url == redis_url:
        env.pop(_LEGACY_COORD_URL_KEY, None)
        changed = True
    if not changed:
        return False
    from src.foundation.config.repo_settings import remove_repo_settings_keys

    remove_repo_settings_keys([_LEGACY_COORD_URL_KEY])
    return True


def resolved_coord_redis_url_for_webui() -> str:
    """WebUI 展示：仅显式联邦 URL 或 bootstrap 落盘，不含分片 REDIS_URL。"""
    repair_misplaced_federate_redis_env()
    explicit = setting_str(_FEDERATE_COORD_URL_KEY)
    if explicit:
        return explicit
    try:
        from src.features.control_plane.store import load_bootstrap_coord_redis_url

        return load_bootstrap_coord_redis_url()
    except Exception:
        return ""


@lru_cache(maxsize=1)
def get_control_plane_webui_config() -> ControlPlaneWebuiConfig:
    repair_misplaced_federate_redis_env()
    enabled_raw = setting_str("PALLAS_CONTROL_PLANE_ENABLED", "true")
    enabled_flag = parse_tristate(enabled_raw, default=True)
    fid = setting_str("PALLAS_FEDERATE_ID")
    if not fid:
        try:
            from src.features.community_stats.store import load_community_stats_state

            fid = str(load_community_stats_state().get("federate_id") or "").strip()
        except Exception:
            fid = ""
    return ControlPlaneWebuiConfig(
        enabled=enabled_flag is not False,
        bootstrap_url=setting_str("PALLAS_CONTROL_PLANE_BOOTSTRAP_URL"),
        instance_secret=setting_str("PALLAS_INSTANCE_SECRET"),
        federate_id=fid,
        federate_ingress_enabled=setting_str("PALLAS_FEDERATE_INGRESS_ENABLED", "auto") or "auto",
        federate_redis_prefix=setting_str("PALLAS_FEDERATE_REDIS_PREFIX"),
        coord_redis_url=resolved_coord_redis_url_for_webui(),
    )


def clear_control_plane_webui_config_cache() -> None:
    get_control_plane_webui_config.cache_clear()

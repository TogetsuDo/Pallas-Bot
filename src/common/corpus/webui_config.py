"""WebUI「语料联邦」配置段读写。"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from src.common.config.repo_settings import repo_env_raw_value

_TRI = Literal["auto", "true", "false"]


def _tristate_read(env_key: str, *, default: str = "auto") -> str:
    raw = repo_env_raw_value(env_key)
    if raw is None:
        return default
    s = str(raw).strip().lower()
    if s in ("auto", ""):
        return "auto"
    if s in ("1", "true", "yes", "on"):
        return "true"
    if s in ("0", "false", "no", "off"):
        return "false"
    return default


def _str_read(env_key: str, default: str = "") -> str:
    raw = repo_env_raw_value(env_key)
    if raw is None:
        return default
    return str(raw).strip() or default


class CorpusFederationWebuiConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    merge_order: str = Field(
        default="local,community",
        description="读语料顺序：local,community（Phase 1）或仅 local。",
    )
    merge_strategy: Literal["local_first", "merge_counts"] = Field(
        default="local_first",
        description="合并策略：local_first 优先本地；merge_counts 合并计数。",
    )
    community_enabled: _TRI = Field(default="false", description="是否启用社区语料池（默认关，WebUI 手动开启）。")
    auto_enroll: _TRI = Field(default="auto", description="是否向 stats 中心自动 enroll 语料 token。")
    community_contribute: _TRI = Field(default="auto", description="是否 mirror 学习结果到社区池。")
    fed_enabled: _TRI = Field(default="auto", description="是否启用联邦语料（托管 Phase 2，当前多为未接入）。")
    fed_contribute: bool = Field(default=False, description="是否向联邦 PG 写回学习结果。")
    on_remote_failure: Literal["local_only"] = Field(
        default="local_only",
        description="远端语料失败时策略（当前仅 local_only）。",
    )
    community_api_base: str = Field(
        default="",
        description="手动 community API 基址；留空则 auto enroll / 心跳推导。",
    )
    community_token: str = Field(default="", description="手动语料 token（pc_…）；留空则用 enroll 落盘。")
    community_stats_enabled: bool = Field(default=True, description="是否向社区统计中心上报心跳。")
    community_stats_endpoint: str = Field(
        default="https://stats.pallasbot.top/v1/heartbeat",
        description="心跳 URL；内置主/备域名可自动切换。",
    )
    community_stats_token: str = Field(default="", description="心跳 Bearer（公开 stats 可留空）。")
    community_stats_interval_sec: int = Field(default=300, ge=60, le=3600, description="心跳间隔（秒）。")


def get_corpus_federation_webui_config() -> CorpusFederationWebuiConfig:
    interval_raw = repo_env_raw_value("PALLAS_COMMUNITY_STATS_INTERVAL_SEC")
    try:
        interval = int(str(interval_raw).strip()) if interval_raw is not None else 300
    except ValueError:
        interval = 300
    interval = max(60, min(3600, interval))
    enabled_raw = repo_env_raw_value("PALLAS_COMMUNITY_STATS_ENABLED")
    stats_enabled = True
    if enabled_raw is not None:
        stats_enabled = str(enabled_raw).strip().lower() not in ("0", "false", "no", "off")
    strategy = _str_read("PALLAS_CORPUS_MERGE_STRATEGY", "local_first")
    if strategy not in ("local_first", "merge_counts"):
        strategy = "local_first"
    return CorpusFederationWebuiConfig(
        merge_order=_str_read("PALLAS_CORPUS_MERGE_ORDER", "local,community"),
        merge_strategy=strategy,  # type: ignore[arg-type]
        community_enabled=_tristate_read("PALLAS_CORPUS_COMMUNITY_ENABLED", default="false"),
        auto_enroll=_tristate_read("PALLAS_CORPUS_AUTO_ENROLL"),
        community_contribute=_tristate_read("PALLAS_CORPUS_COMMUNITY_CONTRIBUTE"),
        fed_enabled=_tristate_read("PALLAS_CORPUS_FED_ENABLED"),
        fed_contribute=_tristate_read("PALLAS_CORPUS_FED_CONTRIBUTE", default="false") == "true",
        on_remote_failure="local_only",
        community_api_base=_str_read("PALLAS_CORPUS_COMMUNITY_API_BASE"),
        community_token=_str_read("PALLAS_CORPUS_TOKEN") or _str_read("PALLAS_CORPUS_COMMUNITY_TOKEN"),
        community_stats_enabled=stats_enabled,
        community_stats_endpoint=_str_read(
            "PALLAS_COMMUNITY_STATS_ENDPOINT",
            "https://stats.pallasbot.top/v1/heartbeat",
        ),
        community_stats_token=_str_read("PALLAS_COMMUNITY_STATS_TOKEN"),
        community_stats_interval_sec=interval,
    )

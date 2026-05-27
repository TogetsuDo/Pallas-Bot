"""WebUI「语料联邦」配置段读写。"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from src.console.webui.field_help import field_help
from src.foundation.config.repo_settings import repo_env_raw_value

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
        description=field_help(
            "查找回复语料时先查哪几个来源",
            "选 local,community 表示先本机再共享池；选 local 表示只用本机语料",
            "关闭共享语料时建议选 local",
        ),
    )
    merge_strategy: Literal["local_first", "merge_counts"] = Field(
        default="local_first",
        description=field_help(
            "本机与共享池都有同一句时如何合并",
            "local_first：优先用本机记录；merge_counts：把两边的使用次数加在一起再排序",
        ),
    )
    community_enabled: _TRI = Field(
        default="false",
        description=field_help(
            "是否使用共享语料池",
            "选 true 开启，false 关闭，auto 由程序按环境自动判断",
            "默认关闭，确认已配置共享池地址与令牌后再开启",
        ),
    )
    auto_enroll: _TRI = Field(
        default="auto",
        description=field_help(
            "是否自动向统计中心登记本机的语料访问凭证",
            "选 auto 一般即可；true 强制登记，false 不登记",
            "登记成功后会把凭证保存在本机，无需每次手填",
        ),
    )
    community_contribute: _TRI = Field(
        default="auto",
        description=field_help(
            "是否把本机新学到的回复同步到共享池",
            "选 auto 由程序判断；true 总是上传，false 从不上传",
            "上传前请确认符合共享语料规范",
        ),
    )
    fed_enabled: _TRI = Field(
        default="auto",
        description=field_help(
            "是否启用跨站联邦语料（高级功能）",
            "当前多数部署尚未接入，保持 auto 或 false 即可",
        ),
    )
    fed_contribute: bool = Field(
        default=False,
        description=field_help(
            "是否向联邦数据库回写学习结果",
            "仅在你已部署联邦服务并知晓风险时开启",
        ),
    )
    on_remote_failure: Literal["local_only"] = Field(
        default="local_only",
        description=field_help(
            "拉取共享语料失败时的兜底方式",
            "目前固定为仅使用本机语料，以保证牛牛仍能回复",
        ),
    )
    community_api_base: str = Field(
        default="",
        description=field_help(
            "共享语料接口的根地址",
            "填写形如 https://示例域名 的地址，末尾不要加斜杠",
            "留空时程序会尝试用自动登记结果或统计心跳地址推导",
        ),
    )
    community_token: str = Field(
        default="",
        description=field_help(
            "访问共享语料用的令牌",
            "一般以 pc_ 开头；留空则使用自动登记保存在本机的令牌",
        ),
    )
    community_stats_enabled: bool = Field(
        default=True,
        description=field_help(
            "是否向统计中心上报本机在线情况",
            "开启后控制台「统计与语料」才能看到全网大致数据；关闭则只影响上报，不影响牛牛聊天",
        ),
    )
    community_stats_endpoint: str = Field(
        default="https://stats.pallasbot.top/v1/heartbeat",
        description=field_help(
            "统计心跳要提交到的网址",
            "填完整 URL；官方地址一般无需修改，程序会在主站不可用时尝试备用域名",
        ),
    )
    community_stats_token: str = Field(
        default="",
        description=field_help(
            "提交统计时附带的访问令牌",
            "公开统计服务通常可留空；若运营方发了专用令牌再填写",
        ),
    )
    community_stats_interval_sec: int = Field(
        default=300,
        ge=60,
        le=3600,
        description=field_help(
            "每隔多少秒上报一次在线心跳",
            "在下拉框中选秒数，例如 300 表示 5 分钟一次",
            "间隔过短会增加请求次数；过长则在线统计数据更新变慢",
        ),
    )


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

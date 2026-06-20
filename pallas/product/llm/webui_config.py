"""WebUI 通用配置：LLM 全局开关与 AI 服务地址。"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from pallas.console.webui.field_help import field_help
from pallas.product.llm.config import get_llm_config

RepeaterMode = Literal["off", "select", "select_polish_lite", "select_fallback", "fallback", "polish", "both"]


class LlmWebuiConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    ai_server_host: str = Field(
        default="127.0.0.1",
        description=field_help("智能对话服务所在主机的地址", "本机部署填 127.0.0.1；远程填 IP 或域名"),
    )
    ai_server_port: int = Field(
        default=9099,
        ge=1,
        le=65535,
        description=field_help("智能对话服务监听的端口", "与 Pallas-Bot-AI 的 .env 中端口一致"),
    )
    llm_chat_enabled: bool = Field(
        default=False,
        description=field_help(
            "是否启用智能对话",
            "开启后可用「随时闲聊」等口令，并影响接话时的 AI 能力",
        ),
    )
    llm_repeater_mode: RepeaterMode = Field(
        default="select",
        description=field_help(
            "接话时如何使用智能对话",
            "推荐「命中语料时 AI 选句」；需要时可开启语料缺失现编或偶尔轻顺口气",
            (
                "遗留项「完整润色」易注入过多人设，日常接话不建议使用。"
                "用户视角：off=只用语料；fallback=语料不够时 AI 补位；"
                "polish=命中语料时 AI 轻顺口气；both=两者都开"
            ),
        ),
    )
    llm_polish_lite_sample_rate: float = Field(
        default=0.12,
        ge=0.0,
        le=1.0,
        description=field_help(
            "「选句为主，偶尔轻顺口气」模式下走轻润色的比例",
            "0.12 表示约 12% 命中语料会轻顺口气，其余仍走选句",
        ),
    )
    llm_governance_enabled: bool = Field(
        default=True,
        description=field_help(
            "是否限制闲聊的频率与单次字数",
            "群很活跃时建议开启，避免刷屏",
        ),
    )
    llm_session_enabled: bool = Field(
        default=True,
        description=field_help(
            "是否记住多轮对话上下文",
            "开启后「随时闲聊」可连续聊；关闭则每句独立",
        ),
    )
    llm_tools_enabled: bool = Field(
        default=True,
        description=field_help(
            "是否允许智能对话调用方舟等资料工具",
            "需同时开启智能对话总闸与 AI 仓 LLM_TOOLS_ENABLED",
        ),
    )
    llm_chat_max_concurrency: int = Field(
        default=2,
        ge=1,
        le=64,
        description=field_help(
            "同时向 AI 提交的闲聊请求上限",
            "每个分片 worker 进程独立计数；@ 闲聊与接话分开限流",
        ),
    )
    llm_repeater_group_cooldown_sec: int = Field(
        default=60,
        ge=0,
        le=3600,
        description=field_help(
            "同一群两次接话 AI 请求的最短间隔（秒）",
            "0 表示不限制群冷却",
        ),
    )
    llm_repeater_max_inflight: int = Field(
        default=1,
        ge=1,
        le=32,
        description=field_help(
            "每个 worker 同时进行的接话 AI 请求数",
            "与闲聊并发分开计算",
        ),
    )
    llm_repeater_global_rpm: int = Field(
        default=10,
        ge=1,
        le=600,
        description=field_help(
            "全实例每分钟接话 AI 请求上限",
            "有 Redis 时全局限流；否则按 worker 数分摊",
        ),
    )
    llm_repeater_feedback_enabled: bool = Field(
        default=False,
        description=field_help(
            "是否收集闲聊成功回复，作为复读软反馈",
            "只在回复真正发出后记录；默认只收集，不改复读行为",
        ),
    )
    llm_repeater_bias_enabled: bool = Field(
        default=False,
        description=field_help(
            "是否让复读轻微偏向已被闲聊验证过的短回复",
            "保守弱偏置；样本不足时不会生效",
        ),
    )
    llm_repeater_writeback_enabled: bool = Field(
        default=False,
        description=field_help(
            "是否允许将软反馈回写到复读学习语料",
            "默认关闭；后续确认策略后再开启",
        ),
    )
    llm_reply_gate_enabled: bool = Field(
        default=True,
        description=field_help(
            "是否过滤纯表情等不值得回复的 @",
            "开启后表情包 @ 不会提交 AI",
        ),
    )
    llm_chat_queue_merge: bool = Field(
        default=True,
        description=field_help(
            "冷却期间是否合并多条 @",
            "开启后 CD 内连发只保留最后一次 completion",
        ),
    )
    llm_memory_rag_enabled: bool = Field(
        default=True,
        description=field_help(
            "是否启用群记忆检索",
            "开启后可将「记住：…」写入记忆，并按相关度注入对话",
        ),
    )
    llm_relationship_notes_enabled: bool = Field(
        default=True,
        description=field_help(
            "是否启用关系备注层",
            "开启后可对 @某人 教导稳定关系（如「记住关系：xx是群主」），随时间衰减",
        ),
    )


def get_llm_webui_config() -> LlmWebuiConfig:
    cfg = get_llm_config()
    mode = cfg.llm_repeater_mode
    if mode not in ("off", "select", "select_polish_lite", "select_fallback", "fallback", "polish", "both"):
        mode = "select"
    return LlmWebuiConfig(
        ai_server_host=cfg.ai_server_host,
        ai_server_port=cfg.ai_server_port,
        llm_chat_enabled=cfg.llm_chat_enabled,
        llm_repeater_mode=mode,  # type: ignore[arg-type]
        llm_polish_lite_sample_rate=cfg.llm_polish_lite_sample_rate,
        llm_governance_enabled=cfg.llm_governance_enabled,
        llm_session_enabled=cfg.llm_session_enabled,
        llm_tools_enabled=cfg.llm_tools_enabled,
        llm_chat_max_concurrency=cfg.llm_chat_max_concurrency,
        llm_repeater_group_cooldown_sec=cfg.llm_repeater_group_cooldown_sec,
        llm_repeater_max_inflight=cfg.llm_repeater_max_inflight,
        llm_repeater_global_rpm=cfg.llm_repeater_global_rpm,
        llm_repeater_feedback_enabled=cfg.llm_repeater_feedback_enabled,
        llm_repeater_bias_enabled=cfg.llm_repeater_bias_enabled,
        llm_repeater_writeback_enabled=cfg.llm_repeater_writeback_enabled,
        llm_reply_gate_enabled=cfg.llm_reply_gate_enabled,
        llm_chat_queue_merge=cfg.llm_chat_queue_merge,
        llm_memory_rag_enabled=cfg.llm_memory_rag_enabled,
        llm_relationship_notes_enabled=cfg.llm_relationship_notes_enabled,
    )

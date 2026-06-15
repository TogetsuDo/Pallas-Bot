from __future__ import annotations

from threading import Lock
from typing import Self

from pydantic import BaseModel, ConfigDict, Field

from src.console.webui.field_help import field_help
from src.foundation.config.dotenv import repo_env_raw_value, repo_layered_dotenv_files_exist

_config_lock = Lock()
_cached: IngressDispatchRuntimeConfig | None = None


def dispatch_env_raw(name_upper: str) -> str | None:
    raw = repo_env_raw_value(name_upper)
    if raw is not None:
        text = str(raw).strip()
        return text or None
    if not repo_layered_dotenv_files_exist():
        try:
            from nonebot import get_driver

            cfg = get_driver().config
            attr = name_upper.lower()
            if attr in (getattr(cfg, "model_fields_set", None) or set()):
                val = getattr(cfg, attr, None)
                if val is None:
                    return None
                return str(val).strip()
        except ValueError:
            pass
    return None


def dispatch_env_bool(name_upper: str, *, default: bool) -> bool:
    raw = dispatch_env_raw(name_upper)
    if raw is None:
        return default
    text = raw.lower()
    if text in ("0", "false", "no", "off"):
        return False
    if text in ("1", "true", "yes", "on"):
        return True
    return default


def dispatch_env_int(name_upper: str, *, default: int, minimum: int, maximum: int) -> int:
    raw = dispatch_env_raw(name_upper)
    if raw is None:
        return default
    try:
        return max(minimum, min(maximum, int(raw)))
    except ValueError:
        return default


def dispatch_env_float(name_upper: str, *, default: float, minimum: float) -> float:
    raw = dispatch_env_raw(name_upper)
    if raw is None:
        return default
    try:
        return max(minimum, float(raw))
    except ValueError:
        return default


class IngressDispatchRuntimeConfig(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")

    matcher_dispatch_enabled: bool = Field(
        default=True,
        description=field_help(
            "启用 matcher 预筛选与 handle_event patch",
            "关闭后恢复 NoneBot 原生 matcher 扇出",
            "保存后立即生效",
        ),
    )
    matcher_dispatch_overload_threshold: int = Field(
        default=24,
        ge=1,
        le=256,
        description=field_help(
            "单条群消息选中 matcher 超过此数时触发过载信号",
            "填正整数，默认 24",
            "过载时后台 prefetch 等任务让路",
        ),
    )
    route_index_enabled: bool = Field(
        default=True,
        description=field_help(
            "启用命令路由索引",
            "关闭后闲聊与命令均回退全量 matcher 扫描",
            "保存后立即生效",
        ),
    )
    route_index_strict: bool = Field(
        default=False,
        description=field_help(
            "路由索引 strict 模式",
            "开启后未命中索引的命令 matcher 不再回退全量",
            "生产稳定前建议保持关闭",
        ),
    )
    dispatch_lanes_enabled: bool = Field(
        default=True,
        description=field_help(
            "启用 dispatch lane 并发预算",
            "关闭后 matcher 不再按档位限流",
            "保存后立即生效",
        ),
    )
    lane_acquire_timeout_sec: float = Field(
        default=1.0,
        ge=0.0,
        le=30.0,
        description=field_help(
            "lane acquire 最长等待秒数",
            "超时则丢弃该 matcher 执行",
            "命令流量可回复忙提示",
        ),
    )
    lane_wait_overload_ms: int = Field(
        default=250,
        ge=50,
        le=5000,
        description=field_help(
            "lane 等待超过此毫秒数时触发过载",
            "默认 250",
            "与 message_load 联动",
        ),
    )
    lane_busy_reply: bool = Field(
        default=True,
        description=field_help(
            "命令 lane 满时发送人设忙回复",
            "关闭则静默丢弃",
            "保存后立即生效",
        ),
    )
    lane_command: int = Field(
        default=16,
        ge=1,
        le=128,
        description=field_help(
            "command 档位并发上限",
            "口令与 CommandRule matcher",
            "保存后清 lane 缓存",
        ),
    )
    lane_chat: int = Field(
        default=32,
        ge=1,
        le=256,
        description=field_help(
            "chat 档位并发上限",
            "群聊被动与轻量 regex",
            "保存后清 lane 缓存",
        ),
    )
    lane_storage: int = Field(
        default=8,
        ge=1,
        le=64,
        description=field_help(
            "storage 档位并发上限",
            "PG 密集 matcher，高压时自动收紧",
            "默认 min(8, PG_POOL_SIZE)",
        ),
    )
    lane_remote: int = Field(
        default=4,
        ge=1,
        le=64,
        description=field_help(
            "remote 档位并发上限",
            "HTTP、AI、渲染等外呼",
            "保存后清 lane 缓存",
        ),
    )
    send_queue_enabled: bool = Field(
        default=True,
        description=field_help(
            "启用 OneBot 出站 send 队列",
            "关闭后 send 类 API 直连协议端",
            "变更 worker 数需重启进程",
        ),
    )
    send_queue_workers: int = Field(
        default=2,
        ge=1,
        le=16,
        description=field_help(
            "出站队列 worker 数",
            "默认 2",
            "变更后需重启 Bot",
        ),
    )
    send_queue_max_depth: int = Field(
        default=256,
        ge=32,
        le=4096,
        description=field_help(
            "出站队列最大深度",
            "高压时丢弃低优先级 API",
            "保存后立即生效",
        ),
    )
    send_queue_min_interval_ms: int = Field(
        default=50,
        ge=0,
        le=2000,
        description=field_help(
            "同牛连续发送最小间隔毫秒",
            "默认 50",
            "保存后立即生效",
        ),
    )
    send_queue_enqueue_timeout_sec: float = Field(
        default=2.0,
        ge=0.0,
        le=30.0,
        description=field_help(
            "入队最长等待秒数",
            "超时则丢弃该次发送",
            "保存后立即生效",
        ),
    )

    @classmethod
    def from_env(cls) -> Self:
        pool_size = dispatch_env_int("PG_POOL_SIZE", default=10, minimum=1, maximum=128)
        storage_default = min(8, pool_size)
        return cls(
            matcher_dispatch_enabled=dispatch_env_bool("PALLAS_MATCHER_DISPATCH_ENABLED", default=True),
            matcher_dispatch_overload_threshold=dispatch_env_int(
                "PALLAS_MATCHER_DISPATCH_OVERLOAD_THRESHOLD",
                default=24,
                minimum=1,
                maximum=256,
            ),
            route_index_enabled=dispatch_env_bool("PALLAS_ROUTE_INDEX_ENABLED", default=True),
            route_index_strict=dispatch_env_bool("PALLAS_ROUTE_INDEX_STRICT", default=False),
            dispatch_lanes_enabled=dispatch_env_bool("PALLAS_DISPATCH_LANES_ENABLED", default=True),
            lane_acquire_timeout_sec=dispatch_env_float("PALLAS_LANE_ACQUIRE_TIMEOUT_SEC", default=1.0, minimum=0.0),
            lane_wait_overload_ms=dispatch_env_int(
                "PALLAS_LANE_WAIT_OVERLOAD_MS",
                default=250,
                minimum=50,
                maximum=5000,
            ),
            lane_busy_reply=dispatch_env_bool("PALLAS_LANE_BUSY_REPLY", default=True),
            lane_command=dispatch_env_int("PALLAS_LANE_COMMAND", default=16, minimum=1, maximum=128),
            lane_chat=dispatch_env_int("PALLAS_LANE_CHAT", default=32, minimum=1, maximum=256),
            lane_storage=dispatch_env_int("PALLAS_LANE_STORAGE", default=storage_default, minimum=1, maximum=64),
            lane_remote=dispatch_env_int("PALLAS_LANE_REMOTE", default=4, minimum=1, maximum=64),
            send_queue_enabled=dispatch_env_bool("PALLAS_SEND_QUEUE_ENABLED", default=True),
            send_queue_workers=dispatch_env_int("PALLAS_SEND_QUEUE_WORKERS", default=2, minimum=1, maximum=16),
            send_queue_max_depth=dispatch_env_int("PALLAS_SEND_QUEUE_MAX_DEPTH", default=256, minimum=32, maximum=4096),
            send_queue_min_interval_ms=dispatch_env_int(
                "PALLAS_SEND_QUEUE_MIN_INTERVAL_MS",
                default=50,
                minimum=0,
                maximum=2000,
            ),
            send_queue_enqueue_timeout_sec=dispatch_env_float(
                "PALLAS_SEND_QUEUE_ENQUEUE_TIMEOUT_SEC",
                default=2.0,
                minimum=0.0,
            ),
        )


def clear_ingress_dispatch_runtime_config_cache() -> None:
    global _cached
    with _config_lock:
        _cached = None


def get_ingress_dispatch_runtime_config() -> IngressDispatchRuntimeConfig:
    global _cached
    with _config_lock:
        if _cached is None:
            _cached = IngressDispatchRuntimeConfig.from_env()
        return _cached

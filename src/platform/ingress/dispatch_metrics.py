"""中央入站 dispatch 指标（unified / worker 进程内）。"""

from __future__ import annotations

import time
from collections import deque
from typing import Any

_COUNTERS = (
    "group_messages",
    "command_traffic",
    "chatter_traffic",
    "preprocessor_dropped",
    "matchers_considered",
    "matchers_selected",
    "matchers_run",
    "lane_busy",
    "lane_wait_ms_total",
    "lane_wait_count",
    "overload_signals",
    "prefetch_paused",
)
_state: dict[str, int] = dict.fromkeys(_COUNTERS, 0)
_day_key = ""
_ingress_ms_samples: deque[float] = deque(maxlen=256)


def _today_key() -> str:
    return time.strftime("%Y-%m-%d", time.localtime())


def _rollover_if_needed() -> None:
    global _day_key
    today = _today_key()
    if _day_key == today:
        return
    _day_key = today
    for key in _COUNTERS:
        _state[key] = 0
    _ingress_ms_samples.clear()


def clear_dispatch_metrics_for_tests() -> None:
    global _day_key
    _day_key = ""
    for key in _COUNTERS:
        _state[key] = 0
    _ingress_ms_samples.clear()


def record_group_message_ingress(
    *,
    duration_ms: float,
    command_traffic: bool,
    matchers_considered: int,
    matchers_selected: int,
    matchers_run: int,
) -> None:
    _rollover_if_needed()
    _state["group_messages"] += 1
    if command_traffic:
        _state["command_traffic"] += 1
    else:
        _state["chatter_traffic"] += 1
    _state["matchers_considered"] += max(0, matchers_considered)
    _state["matchers_selected"] += max(0, matchers_selected)
    _state["matchers_run"] += max(0, matchers_run)
    if duration_ms >= 0:
        _ingress_ms_samples.append(float(duration_ms))


def record_preprocessor_dropped() -> None:
    _rollover_if_needed()
    _state["preprocessor_dropped"] += 1


def record_matcher_run() -> None:
    _rollover_if_needed()
    _state["matchers_run"] += 1


def record_lane_wait(wait_ms: float, *, busy: bool = False) -> None:
    _rollover_if_needed()
    if wait_ms > 0:
        _state["lane_wait_ms_total"] += int(wait_ms)
        _state["lane_wait_count"] += 1
    if busy:
        _state["lane_busy"] += 1


def record_overload_signal() -> None:
    _rollover_if_needed()
    _state["overload_signals"] += 1


def record_prefetch_paused() -> None:
    _rollover_if_needed()
    _state["prefetch_paused"] += 1


def ingress_duration_p95_ms() -> float | None:
    if not _ingress_ms_samples:
        return None
    ordered = sorted(_ingress_ms_samples)
    idx = max(0, min(len(ordered) - 1, int(len(ordered) * 0.95)))
    return round(float(ordered[idx]), 2)


def lane_wait_avg_ms() -> float | None:
    count = int(_state["lane_wait_count"])
    if count <= 0:
        return None
    return round(float(_state["lane_wait_ms_total"]) / count, 2)


def dispatch_alerts(*, p95_ms: float | None, pg_util: float | None) -> list[str]:
    alerts: list[str] = []
    if p95_ms is not None and p95_ms > 100.0:
        alerts.append("ingress_p95_over_100ms")
    if pg_util is not None and pg_util >= 0.85:
        alerts.append("pg_pool_over_85pct")
    return alerts


def dispatch_metrics_snapshot() -> dict[str, Any]:
    _rollover_if_needed()
    from src.foundation.db.pool_budget import pool_budget_status
    from src.platform.ingress.send_queue import send_queue_status

    p95 = ingress_duration_p95_ms()
    pool = pool_budget_status()
    pg_util = pool.get("utilization")
    counters = {key: int(_state[key]) for key in _COUNTERS}
    group_messages = counters["group_messages"]
    return {
        "day_key": _day_key or _today_key(),
        **counters,
        "lane_wait_ms_avg": lane_wait_avg_ms(),
        "ingress_duration_ms_p95": p95,
        "send_queue": send_queue_status(),
        "pool_budget": pool,
        "alerts": dispatch_alerts(p95_ms=p95, pg_util=pg_util if isinstance(pg_util, float) else None),
        "matchers_selected_ratio": round(counters["matchers_selected"] / counters["matchers_considered"], 4)
        if counters["matchers_considered"]
        else None,
        "avg_matchers_per_message": round(counters["matchers_selected"] / group_messages, 2)
        if group_messages
        else None,
    }

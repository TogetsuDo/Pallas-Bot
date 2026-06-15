from __future__ import annotations

import time

_OVERLOAD_UNTIL = 0.0
_LAST_ACTIVITY = time.monotonic()
_LANE_WAIT_OVERLOAD_MS = 250


def mark_activity() -> None:
    global _LAST_ACTIVITY
    _LAST_ACTIVITY = time.monotonic()


def idle_seconds() -> float:
    return max(0.0, time.monotonic() - _LAST_ACTIVITY)


def signal_overload(duration: float = 5.0) -> None:
    global _OVERLOAD_UNTIL
    if duration <= 0:
        return
    until = time.monotonic() + duration
    if until > _OVERLOAD_UNTIL:
        _OVERLOAD_UNTIL = until


def is_overloaded() -> bool:
    return time.monotonic() < _OVERLOAD_UNTIL


def should_pause_tasks() -> bool:
    return is_overloaded()


def lane_wait_overload_threshold_ms() -> int:
    from src.foundation.config.repo_settings import repo_env_raw_value

    raw = repo_env_raw_value("PALLAS_LANE_WAIT_OVERLOAD_MS")
    if raw is None:
        return _LANE_WAIT_OVERLOAD_MS
    try:
        return max(50, int(str(raw).strip()))
    except ValueError:
        return _LANE_WAIT_OVERLOAD_MS


def record_lane_wait(wait_ms: float) -> None:
    if wait_ms >= lane_wait_overload_threshold_ms():
        signal_overload(3.0)


def reset_message_load_for_tests() -> None:
    global _OVERLOAD_UNTIL, _LAST_ACTIVITY
    _OVERLOAD_UNTIL = 0.0
    _LAST_ACTIVITY = time.monotonic()

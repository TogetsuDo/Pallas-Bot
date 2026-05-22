"""分片 worker ingress 门控计数（写入 worker stats，hub 合并算命中率）。"""

from __future__ import annotations

import time
from typing import Any

_COUNTERS = (
    "events",
    "early_fleet",
    "early_not_at_target",
    "fanout_bypass",
    "claim_won",
    "claim_lost",
)
_state: dict[str, int] = dict.fromkeys(_COUNTERS, 0)
_day_key = ""


def _today_key() -> str:
    return time.strftime("%Y-%m-%d", time.localtime())


def _rollover_if_needed() -> None:
    global _day_key
    today = _today_key()
    if _day_key == today:
        return
    _day_key = today
    for k in _COUNTERS:
        _state[k] = 0


def record_ingress_event() -> None:
    _rollover_if_needed()
    _state["events"] += 1


def record_ingress_early_discard(reason: str) -> None:
    _rollover_if_needed()
    key = "early_fleet" if reason == "fleet" else "early_not_at_target"
    _state[key] += 1


def record_ingress_fanout_bypass() -> None:
    _rollover_if_needed()
    _state["fanout_bypass"] += 1


def record_ingress_claim(*, won: bool) -> None:
    _rollover_if_needed()
    _state["claim_won" if won else "claim_lost"] += 1


def ingress_metrics_snapshot() -> dict[str, Any]:
    _rollover_if_needed()
    won = int(_state["claim_won"])
    lost = int(_state["claim_lost"])
    attempts = won + lost
    return {
        "day_key": _day_key or _today_key(),
        **{k: int(_state[k]) for k in _COUNTERS},
        "claim_attempts": attempts,
        "claim_hit_rate": round(won / attempts, 4) if attempts else None,
    }


def merge_ingress_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    merged = dict.fromkeys(_COUNTERS, 0)
    merged["claim_attempts"] = 0
    day_key = ""
    for row in rows:
        if not isinstance(row, dict):
            continue
        day_key = str(row.get("day_key") or day_key)
        for k in _COUNTERS:
            merged[k] += int(row.get(k) or 0)
    won = int(merged["claim_won"])
    lost = int(merged["claim_lost"])
    attempts = won + lost
    merged["day_key"] = day_key
    merged["claim_attempts"] = attempts
    merged["claim_hit_rate"] = round(won / attempts, 4) if attempts else None
    return merged

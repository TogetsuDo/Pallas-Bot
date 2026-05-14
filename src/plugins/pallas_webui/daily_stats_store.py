"""控制台按自然日汇总的消息收/发与 Matcher 次数持久化。"""

from __future__ import annotations

import json
import threading
from datetime import date, timedelta
from operator import itemgetter
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

_STORE_VER = 1
_MAX_RETAIN_DAYS = 500
_LOCK = threading.RLock()


def stats_file_path() -> Path:
    from src.common.paths import plugin_data_dir

    return plugin_data_dir("pallas_webui") / "console_daily_stats.json"


def _read_raw() -> dict[str, Any]:
    p = stats_file_path()
    if not p.exists():
        return {"v": _STORE_VER, "by_day": {}}
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"v": _STORE_VER, "by_day": {}}
    if not isinstance(raw, dict):
        return {"v": _STORE_VER, "by_day": {}}
    raw.setdefault("v", _STORE_VER)
    bd = raw.get("by_day")
    if not isinstance(bd, dict):
        raw["by_day"] = {}
    return raw


def _atomic_write(data: dict[str, Any]) -> None:
    p = stats_file_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(p)


def _trim_old_days(by_day: dict[str, Any]) -> None:
    keys = sorted(k for k in by_day if isinstance(k, str) and len(k) >= 10)
    if len(keys) <= _MAX_RETAIN_DAYS:
        return
    for k in keys[: len(keys) - _MAX_RETAIN_DAYS]:
        by_day.pop(k, None)


def write_day_totals(day: str, self_id: str, received: int, sent: int, matcher_runs: int) -> None:
    """写入或覆盖某日某账号的汇总"""
    sid = str(self_id).strip()
    if not sid or len(str(day).strip()) < 10:
        return
    day_key = str(day).strip()[:10]
    with _LOCK:
        data = _read_raw()
        days = data.setdefault("by_day", {})
        if not isinstance(days, dict):
            data["by_day"] = {}
            days = data["by_day"]
        bots = days.setdefault(day_key, {})
        if not isinstance(bots, dict):
            days[day_key] = {}
            bots = days[day_key]
        bots[sid] = {
            "received": max(0, int(received)),
            "sent": max(0, int(sent)),
            "matcher_runs": max(0, int(matcher_runs)),
        }
        _trim_old_days(days)
        _atomic_write(data)


def _parse_iso_day(s: str) -> date | None:
    try:
        return date.fromisoformat(str(s).strip()[:10])
    except ValueError:
        return None


def load_range(
    *,
    self_id: str | None,
    start_day: str,
    end_day: str,
) -> tuple[list[dict[str, Any]], str, str]:
    """读取磁盘上 [start_day, end_day] 内每日每账号一行。返回 (rows, start_eff, end_eff)。"""
    sd = _parse_iso_day(start_day)
    ed = _parse_iso_day(end_day)
    if sd is None or ed is None:
        return [], start_day[:10], end_day[:10]
    if sd > ed:
        sd, ed = ed, sd
    start_eff = sd.isoformat()
    end_eff = ed.isoformat()
    with _LOCK:
        data = _read_raw()
        days = data.get("by_day")
        if not isinstance(days, dict):
            return [], start_eff, end_eff
    rows: list[dict[str, Any]] = []
    cur = sd
    while cur <= ed:
        key = cur.isoformat()
        day_bots = days.get(key) if isinstance(days, dict) else None
        if isinstance(day_bots, dict):
            for bid, rec in day_bots.items():
                if self_id is not None and str(bid) != str(self_id).strip():
                    continue
                if not isinstance(rec, dict):
                    continue
                try:
                    rows.append({
                        "date": key,
                        "self_id": str(bid),
                        "received": max(0, int(rec.get("received", 0))),
                        "sent": max(0, int(rec.get("sent", 0))),
                        "matcher_runs": max(0, int(rec.get("matcher_runs", 0))),
                    })
                except (TypeError, ValueError):
                    continue
        cur += timedelta(days=1)
    rows.sort(key=itemgetter("date", "self_id"))
    return rows, start_eff, end_eff

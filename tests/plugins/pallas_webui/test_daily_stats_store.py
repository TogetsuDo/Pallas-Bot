from __future__ import annotations

from src.plugins.pallas_webui import daily_stats_store


def test_write_day_and_load_range(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(daily_stats_store, "stats_file_path", lambda: tmp_path / "console_daily_stats.json")
    daily_stats_store.write_day_totals("2026-05-10", "111", 1, 2, 3)
    daily_stats_store.write_day_totals("2026-05-11", "111", 4, 5, 6)
    rows, start, end = daily_stats_store.load_range(
        self_id=None,
        start_day="2026-05-01",
        end_day="2026-05-15",
    )
    assert start == "2026-05-01"
    assert end == "2026-05-15"
    assert len(rows) == 2
    assert rows[0]["date"] == "2026-05-10"
    assert rows[0]["received"] == 1
    assert rows[0]["sent"] == 2
    assert rows[0]["matcher_runs"] == 3
    assert rows[1]["matcher_runs"] == 6


def test_load_range_filter_self_id(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(daily_stats_store, "stats_file_path", lambda: tmp_path / "console_daily_stats.json")
    daily_stats_store.write_day_totals("2026-05-10", "222", 9, 0, 1)
    daily_stats_store.write_day_totals("2026-05-10", "333", 0, 0, 0)
    rows, _, _ = daily_stats_store.load_range(
        self_id="222",
        start_day="2026-05-10",
        end_day="2026-05-10",
    )
    assert len(rows) == 1
    assert rows[0]["self_id"] == "222"

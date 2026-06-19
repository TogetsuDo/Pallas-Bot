from __future__ import annotations

from packages.pb_webui import extended_api as ext
from packages.pb_webui.repeater_metrics_history import (
    append_repeater_metrics_history,
    read_recent_repeater_metrics_history,
)


def test_append_repeater_metrics_history_dedupes_last_row(tmp_path, monkeypatch) -> None:
    from packages.pb_webui import repeater_metrics_history as mod

    monkeypatch.setattr(mod, "repeater_metrics_history_path", lambda: tmp_path / "repeater_metrics_history.jsonl")

    assert append_repeater_metrics_history(
        cluster={"day_key": "2026-06-19", "reply_total": 1},
        process={"day_key": "2026-06-19", "reply_total": 1},
        sharded=False,
    )
    assert not append_repeater_metrics_history(
        cluster={"day_key": "2026-06-19", "reply_total": 1},
        process={"day_key": "2026-06-19", "reply_total": 1},
        sharded=False,
    )
    rows = read_recent_repeater_metrics_history(limit=10)
    assert len(rows) == 1
    assert rows[0]["cluster"]["reply_total"] == 1


def test_flush_unified_console_live_stats_sync_appends_history(tmp_path, monkeypatch) -> None:
    from packages.pb_webui import repeater_metrics_history as hist_mod

    monkeypatch.setattr(ext, "_unified_console_live_stats_enabled", lambda: True)
    monkeypatch.setattr(hist_mod, "repeater_metrics_history_path", lambda: tmp_path / "repeater_metrics_history.jsonl")
    monkeypatch.setattr(
        "packages.pb_webui.console_live_stats.write_bots_sync",
        lambda *args, **kwargs: True,
    )
    monkeypatch.setattr(
        ext,
        "_collect_worker_console_stats_snapshot",
        lambda include_hist=False: {},
    )
    monkeypatch.setattr(
        "pallas.core.platform.shard.repeater_ingress_metrics.repeater_ingress_metrics_snapshot",
        lambda: {"day_key": "2026-06-19", "reply_total": 3},
    )

    ext.flush_unified_console_live_stats_sync()
    rows = read_recent_repeater_metrics_history(limit=10)
    assert len(rows) == 1
    assert rows[0]["sharded"] is False
    assert rows[0]["cluster"]["reply_total"] == 3


def test_repeater_metrics_history_read_recent_rows(tmp_path, monkeypatch) -> None:
    from packages.pb_webui import repeater_metrics_history as hist_mod

    monkeypatch.setattr(hist_mod, "repeater_metrics_history_path", lambda: tmp_path / "repeater_metrics_history.jsonl")
    append_repeater_metrics_history(
        cluster={"day_key": "2026-06-19", "reply_total": 2},
        process={"day_key": "2026-06-19", "reply_total": 2},
        sharded=True,
    )
    rows = read_recent_repeater_metrics_history(limit=10)
    assert len(rows) == 1
    assert rows[0]["cluster"]["reply_total"] == 2

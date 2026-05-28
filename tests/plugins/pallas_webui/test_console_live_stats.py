from __future__ import annotations

import src.plugins.pallas_webui.extended_api as ext
from src.plugins.pallas_webui import console_live_stats, daily_stats_store


def test_unified_console_live_stats_enabled_single_process(monkeypatch) -> None:
    monkeypatch.setattr("src.platform.shard.registry.config.is_sharding_active", lambda: False)
    monkeypatch.setattr("src.platform.bot_runtime.roles.is_sharded_worker", lambda: False)
    monkeypatch.setattr("src.platform.bot_runtime.roles.is_sharded_hub", lambda: False)
    assert ext._unified_console_live_stats_enabled() is True

    monkeypatch.setattr("src.platform.shard.registry.config.is_sharding_active", lambda: True)
    monkeypatch.setattr("src.platform.bot_runtime.roles.is_sharded_hub", lambda: True)
    assert ext._unified_console_live_stats_enabled() is False


def test_restore_unified_from_live_file(tmp_path, monkeypatch) -> None:
    ext._MSG_STATS.clear()
    ext._PLUGIN_RUN_STATS.clear()
    ext._CONSOLE_CAL_DAY.clear()

    live = tmp_path / "console_live_stats.json"
    monkeypatch.setattr(console_live_stats, "live_stats_path", lambda: live)
    monkeypatch.setattr("src.platform.shard.registry.config.is_sharding_active", lambda: False)
    monkeypatch.setattr("src.platform.bot_runtime.roles.is_sharded_worker", lambda: False)
    monkeypatch.setattr("src.platform.bot_runtime.roles.is_sharded_hub", lambda: False)

    console_live_stats.write_bots_sync({
        "10001": {
            "day_key": "2026-05-28",
            "by_plugin": {"help": {"day_runs": 4}},
            "matcher_duration_log": [],
            "msg": {
                "day_key": "2026-05-28",
                "day_received": 120,
                "day_sent": 8,
                "sent": 8,
                "received": 120,
                "day_api_total": 0,
                "day_api_counts": {},
                "api_call_buckets": [],
                "msg_traffic_buckets": [],
            },
        },
    })

    monkeypatch.setattr(ext.time, "strftime", lambda _fmt, _t=None: "2026-05-28")
    assert ext._restore_unified_console_stats_from_live_file() is True
    assert ext._MSG_STATS["10001"]["day_received"] == 120
    assert ext._MSG_STATS["10001"]["day_sent"] == 8
    assert ext._PLUGIN_RUN_STATS["10001"]["by_plugin"]["help"]["day_runs"] == 4


def test_restore_unified_fallback_daily_disk(tmp_path, monkeypatch) -> None:
    ext._MSG_STATS.clear()
    ext._PLUGIN_RUN_STATS.clear()
    ext._CONSOLE_CAL_DAY.clear()

    stats = tmp_path / "console_daily_stats.json"
    monkeypatch.setattr(daily_stats_store, "stats_file_path", lambda: stats)
    monkeypatch.setattr(console_live_stats, "live_stats_path", lambda: tmp_path / "missing_live.json")
    monkeypatch.setattr("src.platform.shard.registry.config.is_sharding_active", lambda: False)
    monkeypatch.setattr("src.platform.bot_runtime.roles.is_sharded_worker", lambda: False)
    monkeypatch.setattr("src.platform.bot_runtime.roles.is_sharded_hub", lambda: False)

    daily_stats_store.write_day_totals("2026-05-28", "10002", 50, 3, 0)

    monkeypatch.setattr(ext.time, "strftime", lambda _fmt, _t=None: "2026-05-28")
    assert ext._restore_unified_console_stats_from_live_file() is True
    assert ext._MSG_STATS["10002"]["day_received"] == 50
    assert ext._MSG_STATS["10002"]["day_sent"] == 3

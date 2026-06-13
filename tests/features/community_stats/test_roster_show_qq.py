from __future__ import annotations

from src.features.community_stats.roster import build_public_roster_entries


def test_build_public_roster_entries_respects_per_bot_show_qq(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.plugins.bot_status.list_mode.status_inventory_bot_ids",
        lambda: {10001, 10002},
    )
    monkeypatch.setattr(
        "src.plugins.bot_status.list_mode.cluster_online_bot_ids_for_status",
        lambda: {10001},
    )
    monkeypatch.setattr(
        "src.console.webui.protocol_accounts.protocol_account_display_names",
        lambda: {"10001": "牛一", "10002": "牛二"},
    )
    monkeypatch.setattr(
        "src.features.community_stats.roster.rolling_message_weight_by_self_id",
        lambda **_: {"10001": 10, "10002": 5},
    )

    rows = build_public_roster_entries(show_qq_by_account={10001: True, 10002: False})
    by_qq = {int(row["qq"]): row for row in rows}
    assert by_qq[10001]["show_qq"] is True
    assert by_qq[10002]["show_qq"] is False


def test_build_public_roster_entries_defaults_show_qq_true(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.plugins.bot_status.list_mode.status_inventory_bot_ids",
        lambda: {20001},
    )
    monkeypatch.setattr(
        "src.plugins.bot_status.list_mode.cluster_online_bot_ids_for_status",
        lambda: set(),
    )
    monkeypatch.setattr(
        "src.console.webui.protocol_accounts.protocol_account_display_names",
        lambda: {},
    )
    monkeypatch.setattr(
        "src.features.community_stats.roster.rolling_message_weight_by_self_id",
        lambda **_: {},
    )

    rows = build_public_roster_entries()
    assert rows[0]["show_qq"] is True

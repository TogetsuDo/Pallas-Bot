from __future__ import annotations

from src.platform.shard.repeater_ingress_metrics import (
    clear_repeater_ingress_metrics_for_tests,
    merge_repeater_ingress_metrics,
    record_repeater_ingress_claim,
    record_repeater_ingress_early_discard,
    record_repeater_ingress_event,
    repeater_ingress_metrics_snapshot,
)


def test_repeater_ingress_metrics_snapshot_and_merge():
    clear_repeater_ingress_metrics_for_tests()
    record_repeater_ingress_event()
    record_repeater_ingress_event()
    record_repeater_ingress_early_discard("plugin_command")
    record_repeater_ingress_early_discard("cross_bot_claim")
    record_repeater_ingress_claim(won=True)
    record_repeater_ingress_claim(won=False)

    snap = repeater_ingress_metrics_snapshot()
    assert snap["events"] == 2
    assert snap["early_plugin_command"] == 1
    assert snap["early_cross_bot_claim"] == 1
    assert snap["claim_won"] == 1
    assert snap["claim_lost"] == 1
    assert snap["claim_hit_rate"] == 0.5

    cluster = merge_repeater_ingress_metrics([snap, {"day_key": snap["day_key"], "claim_won": 1, "claim_lost": 0}])
    assert cluster["claim_won"] == 2
    assert cluster["claim_lost"] == 1
    assert round(cluster["claim_hit_rate"], 4) == round(2 / 3, 4)

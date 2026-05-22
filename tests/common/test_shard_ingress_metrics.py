from __future__ import annotations

from src.common.shard.ingress_metrics import (
    ingress_metrics_snapshot,
    merge_ingress_metrics,
    record_ingress_claim,
    record_ingress_early_discard,
    record_ingress_event,
    record_ingress_fanout_bypass,
)


def test_ingress_metrics_snapshot_and_merge():
    record_ingress_event()
    record_ingress_event()
    record_ingress_early_discard("fleet")
    record_ingress_fanout_bypass()
    record_ingress_claim(won=True)
    record_ingress_claim(won=False)

    snap = ingress_metrics_snapshot()
    assert snap["events"] == 2
    assert snap["early_fleet"] == 1
    assert snap["fanout_bypass"] == 1
    assert snap["claim_won"] == 1
    assert snap["claim_lost"] == 1
    assert snap["claim_hit_rate"] == 0.5

    cluster = merge_ingress_metrics([snap, {"day_key": snap["day_key"], "claim_won": 1, "claim_lost": 0}])
    assert cluster["claim_won"] == 2
    assert cluster["claim_lost"] == 1
    assert round(cluster["claim_hit_rate"], 4) == round(2 / 3, 4)

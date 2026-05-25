import time

from src.common.community_stats import history_store as hs
from src.common.community_stats.history_store import query_history, record_stats_snapshot


def test_record_and_query_history_buckets(tmp_path, monkeypatch):
    db = tmp_path / "community_stats_history.sqlite"
    monkeypatch.setattr(hs, "history_db_path", lambda: db)
    monkeypatch.setattr(hs, "_LAST_SAMPLE_TS", 0)

    base = {
        "deployments_total": 10,
        "deployments_online": 4,
        "bots_online_sum": 20,
        "deployments_online_sharded": 1,
        "shard_workers_online_sum": 3,
        "corpus": {"contexts_total": 5, "answers_total": 100, "enrollments_total": 2},
    }
    now = int(time.time())
    monkeypatch.setattr(time, "time", lambda: now)
    record_stats_snapshot(base)
    monkeypatch.setattr(hs, "_LAST_SAMPLE_TS", 0)
    monkeypatch.setattr(time, "time", lambda: now + 400)
    patched = {**base, "deployments_online": 6, "bots_online_sum": 30}
    record_stats_snapshot(patched)

    out = query_history(hours=24, bucket_sec=300)
    assert out["point_count"] >= 1
    last = out["points"][-1]
    assert last["deployments_online"] in (4, 6)
    assert last["bots_online_sum"] in (20, 30)

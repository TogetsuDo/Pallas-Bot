"""本 Bot 侧社区统计快照（供控制台 24h 趋势）；采样自成功拉取的 /v1/stats。"""

from __future__ import annotations

import sqlite3
import time
from threading import Lock
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

from src.common.config.repo_settings import repo_root

_MIN_SAMPLE_INTERVAL_SEC = 300
_RETENTION_SEC = 25 * 3600
_DB_LOCK = Lock()
_LAST_SAMPLE_TS = 0


def history_db_path() -> Path:
    path = repo_root() / "data" / "pallas_config" / "community_stats_history.sqlite"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def init_history_db() -> None:
    with _DB_LOCK, sqlite3.connect(history_db_path(), timeout=10.0) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS samples (
                ts INTEGER PRIMARY KEY,
                deployments_total INTEGER NOT NULL,
                deployments_online INTEGER NOT NULL,
                bots_online_sum INTEGER NOT NULL,
                deployments_online_sharded INTEGER NOT NULL DEFAULT 0,
                shard_workers_online_sum INTEGER NOT NULL DEFAULT 0,
                corpus_contexts INTEGER,
                corpus_answers INTEGER,
                corpus_enrollments INTEGER
            )
            """
        )
        conn.commit()


def record_stats_snapshot(data: dict[str, Any]) -> None:
    """成功拉取 stats 后调用；同 5 分钟内不重复写入。"""
    global _LAST_SAMPLE_TS
    now = int(time.time())
    with _DB_LOCK:
        if _LAST_SAMPLE_TS and now - _LAST_SAMPLE_TS < _MIN_SAMPLE_INTERVAL_SEC:
            return
        init_history_db()
        corpus = data.get("corpus") if isinstance(data.get("corpus"), dict) else None
        ctx = int(corpus["contexts_total"]) if corpus and "contexts_total" in corpus else None
        ans = int(corpus["answers_total"]) if corpus and "answers_total" in corpus else None
        enr = int(corpus["enrollments_total"]) if corpus and "enrollments_total" in corpus else None
        with sqlite3.connect(history_db_path(), timeout=10.0) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO samples (
                    ts, deployments_total, deployments_online, bots_online_sum,
                    deployments_online_sharded, shard_workers_online_sum,
                    corpus_contexts, corpus_answers, corpus_enrollments
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    now,
                    int(data.get("deployments_total", 0)),
                    int(data["deployments_online"]),
                    int(data["bots_online_sum"]),
                    int(data.get("deployments_online_sharded", 0) or 0),
                    int(data.get("shard_workers_online_sum", 0) or 0),
                    ctx,
                    ans,
                    enr,
                ),
            )
            cutoff = now - _RETENTION_SEC
            conn.execute("DELETE FROM samples WHERE ts < ?", (cutoff,))
            conn.commit()
        _LAST_SAMPLE_TS = now


def query_history(*, hours: float = 24.0, bucket_sec: int = 300) -> dict[str, Any]:
    hours = max(1.0, min(float(hours), 168.0))
    bucket_sec = max(60, min(int(bucket_sec), 3600))
    now = int(time.time())
    since = now - int(hours * 3600)
    init_history_db()
    with _DB_LOCK, sqlite3.connect(history_db_path(), timeout=10.0) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT
                (ts / ?) * ? AS bucket_at,
                CAST(AVG(deployments_total) AS INTEGER) AS deployments_total,
                CAST(AVG(deployments_online) AS INTEGER) AS deployments_online,
                CAST(AVG(bots_online_sum) AS INTEGER) AS bots_online_sum,
                CAST(AVG(deployments_online_sharded) AS INTEGER) AS deployments_online_sharded,
                CAST(AVG(shard_workers_online_sum) AS INTEGER) AS shard_workers_online_sum,
                CAST(AVG(corpus_contexts) AS INTEGER) AS corpus_contexts,
                CAST(AVG(corpus_answers) AS INTEGER) AS corpus_answers,
                CAST(AVG(corpus_enrollments) AS INTEGER) AS corpus_enrollments,
                COUNT(*) AS sample_n
            FROM samples
            WHERE ts >= ?
            GROUP BY bucket_at
            ORDER BY bucket_at ASC
            """,
            (bucket_sec, bucket_sec, since),
        ).fetchall()
    points = [
        {
            "at": int(row["bucket_at"]),
            "deployments_total": int(row["deployments_total"]),
            "deployments_online": int(row["deployments_online"]),
            "bots_online_sum": int(row["bots_online_sum"]),
            "deployments_online_sharded": int(row["deployments_online_sharded"]),
            "shard_workers_online_sum": int(row["shard_workers_online_sum"]),
            "corpus_contexts": row["corpus_contexts"],
            "corpus_answers": row["corpus_answers"],
            "corpus_enrollments": row["corpus_enrollments"],
            "sample_n": int(row["sample_n"]),
        }
        for row in rows
    ]
    return {
        "hours": hours,
        "bucket_sec": bucket_sec,
        "since": since,
        "as_of": now,
        "point_count": len(points),
        "points": points,
    }

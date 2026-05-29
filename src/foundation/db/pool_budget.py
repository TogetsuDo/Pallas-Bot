"""PostgreSQL 连接池预算：为后台任务与远程 I/O 提供背压，避免挤占接话热路径。"""

from __future__ import annotations

from typing import Any

from src.foundation.config.repo_settings import repo_env_raw_value


def pg_pool_capacity() -> int:
    def cfg(key: str, default: str) -> int:
        raw = repo_env_raw_value(key)
        try:
            return int(str(raw if raw is not None else default).strip())
        except ValueError:
            return int(default)

    return cfg("PG_POOL_SIZE", "10") + cfg("PG_MAX_OVERFLOW", "20")


def pg_pool_snapshot() -> dict[str, int] | None:
    from src.foundation.db.repository_pg import pg_pool_live_stats

    return pg_pool_live_stats()


def pg_pool_checked_out() -> int | None:
    snap = pg_pool_snapshot()
    if snap is None:
        return None
    return int(snap.get("checked_out", 0))


def pg_pool_utilization() -> float | None:
    snap = pg_pool_snapshot()
    if snap is None:
        return None
    capacity = int(snap.get("capacity", 0))
    if capacity <= 0:
        return None
    return float(snap.get("checked_out", 0)) / float(capacity)


def pg_pool_under_pressure(*, threshold: float = 0.75) -> bool:
    util = pg_pool_utilization()
    if util is None:
        return False
    return util >= threshold


def cap_by_pg_pool(requested: int, *, workload_fraction: float = 0.30) -> int:
    """按池容量上限裁剪后台并发（至少 1，不超过 requested）。"""
    capacity = pg_pool_capacity()
    frac = max(0.05, min(0.90, float(workload_fraction)))
    ceiling = max(1, int(capacity * frac))
    return max(1, min(int(requested), ceiling))


def remote_corpus_concurrency_limit() -> int:
    raw = repo_env_raw_value("PALLAS_CORPUS_REMOTE_MAX_CONCURRENT")
    if raw is not None:
        try:
            return max(1, min(64, int(str(raw).strip())))
        except ValueError:
            pass
    return max(2, pg_pool_capacity() // 10)


def pool_budget_status() -> dict[str, Any]:
    snap = pg_pool_snapshot()
    capacity = pg_pool_capacity()
    return {
        "capacity": capacity,
        "live": snap,
        "utilization": pg_pool_utilization(),
        "under_pressure": pg_pool_under_pressure(),
        "remote_corpus_limit": remote_corpus_concurrency_limit(),
    }

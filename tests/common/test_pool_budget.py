from src.foundation.db.pool_budget import cap_by_pg_pool, pg_pool_capacity, remote_corpus_concurrency_limit


def test_cap_by_pg_pool_respects_fraction(monkeypatch):
    monkeypatch.setattr(
        "src.foundation.db.pool_budget.repo_env_raw_value",
        lambda key: {"PG_POOL_SIZE": "48", "PG_MAX_OVERFLOW": "24"}.get(key),
    )
    assert pg_pool_capacity() == 72
    assert cap_by_pg_pool(24, workload_fraction=0.22) == 15
    assert cap_by_pg_pool(8, workload_fraction=0.28) == 8


def test_remote_corpus_limit_from_pool(monkeypatch):
    monkeypatch.setattr(
        "src.foundation.db.pool_budget.repo_env_raw_value",
        lambda key: {"PG_POOL_SIZE": "48", "PG_MAX_OVERFLOW": "24"}.get(key),
    )
    assert remote_corpus_concurrency_limit() == 7

    def with_override(key: str):
        if key == "PALLAS_CORPUS_REMOTE_MAX_CONCURRENT":
            return "4"
        return {"PG_POOL_SIZE": "48", "PG_MAX_OVERFLOW": "24"}.get(key)

    monkeypatch.setattr("src.foundation.db.pool_budget.repo_env_raw_value", with_override)
    assert remote_corpus_concurrency_limit() == 4

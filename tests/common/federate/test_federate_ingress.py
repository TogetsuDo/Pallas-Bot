from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.common.platform.coord import redis_claim as rc
from src.common.platform.coord import redis_settings as rs
from src.common.platform.federate import config as fc
from src.common.platform.federate import dedup as fd
from src.common.platform.federate import redis_claim as frc


@pytest.fixture(autouse=True)
def clear_federate_caches():
    fc.clear_federate_config_cache()
    rs.clear_coord_redis_settings_cache()
    rc.clear_coord_redis_client_cache()
    fd._cross_federate_claim_owners.clear()
    yield
    fc.clear_federate_config_cache()
    rs.clear_coord_redis_settings_cache()
    rc.clear_coord_redis_client_cache()
    fd._cross_federate_claim_owners.clear()


@pytest.mark.asyncio
async def test_federate_ingress_inactive_passes(monkeypatch):
    monkeypatch.delenv("PALLAS_FEDERATE_ID", raising=False)
    assert await fd.try_claim_cross_federate_message("p", 1, 2, "hi", 100, "dep-a") is True


@pytest.mark.asyncio
async def test_federate_memory_claim_same_deployment(monkeypatch):
    monkeypatch.setenv("PALLAS_FEDERATE_ID", "pool-1")
    monkeypatch.setenv("PALLAS_FEDERATE_INGRESS_ENABLED", "true")
    fc.clear_federate_config_cache()
    assert await fd.try_claim_cross_federate_message_memory("p", 1, 2, "hi", 100, "dep-a") is True
    assert await fd.try_claim_cross_federate_message_memory("p", 1, 2, "hi", 100, "dep-a") is True
    assert await fd.try_claim_cross_federate_message_memory("p", 1, 2, "hi", 100, "dep-b") is False


def test_federate_claim_redis_key_uses_prefix(monkeypatch):
    monkeypatch.setenv("PALLAS_FEDERATE_ID", "pool-1")
    fc.clear_federate_config_cache()
    key = frc.federate_claim_redis_key("federate_ingress", 99, 12345)
    assert key.startswith("pallas:fed:pool-1:ingress:")


def test_try_claim_federate_message_redis_sync(monkeypatch):
    monkeypatch.setenv("PALLAS_FEDERATE_ID", "pool-1")
    fc.clear_federate_config_cache()
    client = MagicMock()
    client.set.return_value = True
    monkeypatch.setattr(frc, "get_federate_redis_client", lambda: client)
    assert frc.try_claim_federate_message_redis_sync("p", 1, 2, "dep-a") is True
    _, kwargs = client.set.call_args
    assert kwargs.get("nx") is True


def test_federate_ingress_active_requires_redis(monkeypatch):
    monkeypatch.setenv("PALLAS_FEDERATE_ID", "pool-1")
    monkeypatch.setenv("PALLAS_FEDERATE_INGRESS_ENABLED", "true")
    fc.clear_federate_config_cache()
    from src.common.platform.federate import redis_settings as frs

    monkeypatch.setattr(frs, "federate_redis_available", lambda: False)
    assert fc.federate_ingress_active() is False

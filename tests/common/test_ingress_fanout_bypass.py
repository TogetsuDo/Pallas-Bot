from __future__ import annotations

import pytest

from src.platform.ingress.config import clear_ingress_fanout_config_cache
from src.platform.ingress.fanout_bypass import ingress_fanout_bypasses_claim


@pytest.fixture(autouse=True)
def _clear_fanout_cache():
    clear_ingress_fanout_config_cache()
    yield
    clear_ingress_fanout_config_cache()


def test_unified_drink_bypasses_once_claim() -> None:
    assert ingress_fanout_bypasses_claim("牛牛喝酒")
    assert ingress_fanout_bypasses_claim("牛牛醒一醒")


def test_greeting_fanout_texts_bypass_once_claim(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.platform.ingress.config._ingress_env_str",
        lambda name, default="": "牛牛,帕拉斯,牛牛赞我,赞我"
        if name == "PALLAS_INGRESS_FANOUT_GREETING"
        else default,
    )
    clear_ingress_fanout_config_cache()
    assert ingress_fanout_bypasses_claim("牛牛")
    assert ingress_fanout_bypasses_claim("帕拉斯")
    assert ingress_fanout_bypasses_claim("牛牛赞我")
    assert ingress_fanout_bypasses_claim("赞我")

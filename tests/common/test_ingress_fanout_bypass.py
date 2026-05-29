from __future__ import annotations

from src.platform.ingress.fanout_bypass import ingress_fanout_bypasses_claim


def test_unified_drink_bypasses_once_claim() -> None:
    assert ingress_fanout_bypasses_claim("牛牛喝酒")
    assert ingress_fanout_bypasses_claim("牛牛醒一醒")

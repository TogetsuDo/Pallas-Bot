"""喝酒/醒酒入口明文（供 ingress 门控与 drink 共用，勿依赖 plugins）。"""

from __future__ import annotations

_DRINK_FANOUT_TEXTS = frozenset({
    "牛牛喝酒",
    "牛牛干杯",
    "牛牛继续喝",
    "牛牛醒一醒",
    "牛牛别喝了",
})


def is_drink_plaintext(text: str) -> bool:
    """饮酒与醒酒口令：分片下恒 fanout，各牛独立醉酒态。"""
    return (text or "").strip() in _DRINK_FANOUT_TEXTS

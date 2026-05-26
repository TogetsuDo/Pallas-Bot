"""牛牛轮盘相关明文（ingress 门控与 roulette 插件共用）。"""

from __future__ import annotations

_ROULETTE_START = frozenset({
    "牛牛轮盘",
    "牛牛轮盘踢人",
    "牛牛轮盘禁言",
    "牛牛踢人轮盘",
    "牛牛禁言轮盘",
})


def is_roulette_plaintext(text: str) -> bool:
    """轮盘开局/开枪/救援：须由本群群管牛处理，分片下跳过 ingress 单牛 claim。"""
    plain = (text or "").strip()
    if plain in _ROULETTE_START or plain == "牛牛开枪":
        return True
    return plain.startswith(("牛牛救一下", "牛牛补一枪"))

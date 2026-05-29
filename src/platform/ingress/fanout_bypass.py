"""入站门控：跳过跨 Bot / unified once-claim 的明文判定。"""

from __future__ import annotations


def ingress_fanout_bypasses_claim(plain: str) -> bool:
    from src.platform.ingress.cage_plaintext import is_cage_plaintext
    from src.platform.ingress.drink_plaintext import is_drink_plaintext
    from src.platform.ingress.roulette_plaintext import is_roulette_plaintext
    from src.platform.shard.coord.bot_count import should_skip_ingress_claim_for_shard_bot_count
    from src.platform.shard.ingress_fanout import is_ingress_fanout_plaintext

    text = (plain or "").strip()
    if is_ingress_fanout_plaintext(text):
        return True
    if should_skip_ingress_claim_for_shard_bot_count(text):
        return True
    return is_cage_plaintext(text) or is_drink_plaintext(text) or is_roulette_plaintext(text)

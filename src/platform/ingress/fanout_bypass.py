"""入站门控：跳过跨 Bot / unified once-claim 的明文判定。"""

from __future__ import annotations


def ingress_fanout_bypasses_claim(plain: str) -> bool:
    from src.platform.ingress.cage_plaintext import is_cage_plaintext
    from src.platform.ingress.drink_plaintext import is_drink_plaintext
    from src.platform.ingress.help_plaintext import is_help_plaintext
    from src.platform.ingress.plugin_command_plaintext import is_plugin_command_plaintext
    from src.platform.ingress.roulette_plaintext import is_roulette_plaintext
    from src.platform.shard.coord.bot_count import should_skip_ingress_claim_for_shard_bot_count
    from src.platform.shard.ingress_fanout import is_ingress_fanout_plaintext

    text = (plain or "").strip()
    if is_ingress_fanout_plaintext(text):
        return True
    if should_skip_ingress_claim_for_shard_bot_count(text):
        return True
    # 分片：插件命令须走 ingress 跨片/跨牛 claim；单进程 unified 仍 fanout，由 help run_preprocessor 内存抢占。
    if is_plugin_command_plaintext(text):
        from src.platform.shard.registry.config import is_sharding_active

        if not is_sharding_active():
            return True
    return is_cage_plaintext(text) or is_drink_plaintext(text) or is_help_plaintext(text) or is_roulette_plaintext(text)

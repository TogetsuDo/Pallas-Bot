from __future__ import annotations

from src.platform.ingress.plugin_command_plaintext import is_plugin_command_plaintext


def should_prepare_repeater_reply(plain_text: str) -> bool:
    """明显不会接话的消息尽早跳过，避免 fanout/list/context 查询。"""
    plain = (plain_text or "").strip()
    if plain and is_plugin_command_plaintext(plain):
        return False
    if len(plain) < 2:
        return False
    return True

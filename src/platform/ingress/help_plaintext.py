"""牛牛帮助相关明文（ingress 门控与 repeater 共用）。"""

from __future__ import annotations

from src.foundation.command_prefix import matches_command_prefix

_HELP_COMMANDS = (
    "牛牛帮助",
    "牛牛开启",
    "牛牛关闭",
    "牛牛开启全部功能",
    "牛牛关闭全部功能",
)


def is_help_plaintext(text: str) -> bool:
    """帮助与插件开关命令：跳过 repeater/context 查库。"""
    plain = (text or "").strip()
    return any(matches_command_prefix(plain, command) for command in _HELP_COMMANDS)

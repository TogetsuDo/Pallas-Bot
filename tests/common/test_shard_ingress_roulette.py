from __future__ import annotations

from src.platform.ingress.roulette_plaintext import is_roulette_plaintext


def test_roulette_plaintext_commands() -> None:
    assert is_roulette_plaintext("牛牛轮盘")
    assert is_roulette_plaintext("牛牛轮盘踢人")
    assert is_roulette_plaintext("牛牛轮盘禁言")
    assert is_roulette_plaintext("牛牛开枪")
    assert is_roulette_plaintext("牛牛救一下")
    assert is_roulette_plaintext("牛牛救一下 @某人")
    assert is_roulette_plaintext("牛牛补一枪")
    assert not is_roulette_plaintext("牛牛")
    assert not is_roulette_plaintext("参与轮盘")

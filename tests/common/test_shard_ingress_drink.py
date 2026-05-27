from __future__ import annotations

from src.platform.ingress.drink_plaintext import is_drink_plaintext


def test_drink_plaintext_commands() -> None:
    assert is_drink_plaintext("牛牛喝酒")
    assert is_drink_plaintext("牛牛干杯")
    assert is_drink_plaintext("牛牛继续喝")
    assert is_drink_plaintext("牛牛醒一醒")
    assert is_drink_plaintext("牛牛别喝了")
    assert not is_drink_plaintext("牛牛")
    assert not is_drink_plaintext("牛牛喝酒呀")


def test_ingress_fanout_whitelist_does_not_need_drink(monkeypatch) -> None:
    from src.platform.ingress.config import clear_ingress_fanout_config_cache
    from src.platform.shard.ingress_fanout import is_ingress_fanout_plaintext

    monkeypatch.setattr(
        "src.platform.ingress.config._ingress_env_str",
        lambda name, default="": "牛牛,帕拉斯"
        if name == "PALLAS_INGRESS_FANOUT_GREETING"
        else default,
    )
    clear_ingress_fanout_config_cache()
    assert not is_ingress_fanout_plaintext("牛牛喝酒")
    assert is_drink_plaintext("牛牛喝酒")

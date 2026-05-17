from src.plugins.dream.dedupe_keys import dream_image_dedupe_key, dream_text_dedupe_key
from src.plugins.dream.echo_sample import random_echo_nickname
from src.plugins.dream.runtime import drift_at_nickname


def test_random_echo_nickname_prefixed_with_at() -> None:
    for _ in range(20):
        assert random_echo_nickname().startswith("@")


def test_drift_at_nickname_adds_at() -> None:
    assert drift_at_nickname("凯尔希") == "@凯尔希"


def test_drift_at_nickname_idempotent() -> None:
    assert drift_at_nickname("@阿米娅") == "@阿米娅"


def test_drift_at_nickname_blank_defaults() -> None:
    assert drift_at_nickname("") == "@某位博士"
    assert drift_at_nickname("   ") == "@某位博士"


def test_dream_text_dedupe_key_normalizes() -> None:
    assert dream_text_dedupe_key("  Hello   World  ") == dream_text_dedupe_key("hello world")


def test_dream_image_dedupe_key_stable() -> None:
    a = b"\x00\x01\xff"
    assert dream_image_dedupe_key(a) == dream_image_dedupe_key(a)
    assert dream_image_dedupe_key(a) != dream_image_dedupe_key(b"\x00\x01\xfe")

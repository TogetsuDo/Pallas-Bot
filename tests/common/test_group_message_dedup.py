from src.common.group_message_dedup import (
    cross_bot_group_message_key,
    normalize_group_raw_message,
)


def test_normalize_group_raw_message_matches_chatdata_pattern() -> None:
    raw = "prefix.image,subtype=9]"
    assert normalize_group_raw_message(raw) == "prefix.image]"


def test_cross_bot_key_same_physical_message_different_message_id() -> None:
    gid, uid, raw, t = 12345, 999, "牛牛画画 一只羊", 1746358610
    k1 = cross_bot_group_message_key(gid, uid, raw, t)
    k2 = cross_bot_group_message_key(gid, uid, raw, t)
    assert k1 == k2


def test_cross_bot_key_different_content() -> None:
    gid, uid, t = 12345, 999, 1746358610
    assert cross_bot_group_message_key(gid, uid, "牛牛画画 A", t) != cross_bot_group_message_key(
        gid, uid, "牛牛画画 B", t
    )

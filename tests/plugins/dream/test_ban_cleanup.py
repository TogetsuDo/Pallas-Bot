from src.plugins.dream.ban_cleanup import dream_ban_plain_variants, strip_cq_image_urls


def test_strip_cq_image_urls_removes_url_param() -> None:
    raw = "[CQ:image,file=1,url=https://x/y]"
    out = strip_cq_image_urls(raw)
    assert "url=" not in out
    assert out == "[CQ:image,file=1]"


def test_dream_ban_plain_variants_extracts_after_at_colon() -> None:
    s = "@凯尔希：罗德岛加油"
    v = dream_ban_plain_variants(s)
    assert "罗德岛加油" in v
    assert "@凯尔希：罗德岛加油" in v

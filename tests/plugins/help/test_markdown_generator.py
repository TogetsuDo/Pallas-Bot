from src.plugins.help.markdown_generator import _wrap_paragraphs_for_help_page


def test_wrap_preserves_markdown_table() -> None:
    raw = "| 口令 | 说明 |\n|------|------|\n| 牛牛长草 | 完整长草 |"
    out = _wrap_paragraphs_for_help_page(raw)
    assert "| 牛牛长草 |" in out
    assert out.count("\n") >= 2


def test_wrap_preserves_bullet_block() -> None:
    raw = "· 牛牛长草：说明一\n· 牛牛作战：说明二"
    out = _wrap_paragraphs_for_help_page(raw)
    assert "· 牛牛长草" in out
    assert "· 牛牛作战" in out

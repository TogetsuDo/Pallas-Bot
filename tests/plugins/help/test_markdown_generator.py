from src.plugins.help.markdown_generator import _wrap_paragraphs_for_help_page, generate_plugins_markdown


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


def test_level1_guide_before_plugin_table() -> None:
    text = generate_plugins_markdown(None)
    guide_pos = text.find("详情")
    table_pos = text.find("## 插件列表")
    assert guide_pos != -1
    assert table_pos != -1
    assert guide_pos < table_pos
    assert "牛牛帮助 1 2" in text

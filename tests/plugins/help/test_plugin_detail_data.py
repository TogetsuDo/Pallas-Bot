from packages.help.plugin_detail_data import normalize_plugin_usage_text


def test_normalize_plugin_usage_text_numbered() -> None:
    raw = "1. 牛牛帮助 — 总览\n2. 牛牛帮助 1 — 详情"
    out = normalize_plugin_usage_text(raw)
    assert out.startswith("1. ")
    assert "2. " in out


def test_normalize_plugin_usage_text_dot_separator() -> None:
    out = normalize_plugin_usage_text("牛牛帮助 · 牛牛帮助 1 · 牛牛开启")
    assert out.splitlines()[0].startswith("1. ")
    assert len(out.splitlines()) == 3

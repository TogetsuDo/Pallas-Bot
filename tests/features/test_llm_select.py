from __future__ import annotations

from pallas.product.llm.select import (
    build_select_user_text,
    parse_select_response,
    resolve_select_callback_text,
)


def test_build_select_user_text() -> None:
    text = build_select_user_text(
        "今天好烦",
        ["摸摸", "啊？", "没事"],
        context_hints="群习惯：短句",
    )
    assert "【用户消息】今天好烦" in text
    assert "1. 摸摸" in text
    assert "3. 没事" in text


def test_parse_select_response_index() -> None:
    pool = ["a", "b", "c"]
    assert parse_select_response("2", pool) == "b"
    assert parse_select_response("编号 3", pool) == "c"
    assert parse_select_response("0", pool) is None


def test_resolve_select_callback_text_fallback() -> None:
    pool = ["第一句", "第二句"]
    assert resolve_select_callback_text("0", pool, "第一句") == "第一句"
    assert resolve_select_callback_text("乱码", pool, "第一句") == "第一句"
    assert resolve_select_callback_text("2", pool, "第一句") == "第二句"

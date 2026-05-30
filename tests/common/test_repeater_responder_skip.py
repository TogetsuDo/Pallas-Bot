from __future__ import annotations

from types import SimpleNamespace

from src.plugins.repeater.responder import Responder


def test_should_skip_context_lookup_for_pure_cq_message() -> None:
    chat_data = SimpleNamespace(
        is_plain_text=False,
        plain_text="",
        to_me=False,
        keywords_len=0,
    )

    assert Responder.should_skip_context_lookup(chat_data, "[CQ:image,file=a.jpg]") is True


def test_should_not_skip_context_lookup_for_non_plain_with_text() -> None:
    chat_data = SimpleNamespace(
        is_plain_text=False,
        plain_text="诡异吗",
        to_me=False,
        keywords_len=1,
    )

    assert Responder.should_skip_context_lookup(chat_data, "诡异") is False

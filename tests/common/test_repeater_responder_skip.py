from __future__ import annotations

from types import SimpleNamespace

import pytest

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


@pytest.mark.asyncio
async def test_context_find_pure_cq_skips_before_keywords(monkeypatch) -> None:
    from collections import defaultdict, deque

    class _ChatData:
        group_id = 1
        raw_message = "[CQ:image,file=a.jpg]"
        plain_text = ""
        bot_id = 2
        is_plain_text = False
        is_image = True
        to_me = False

        @property
        def keywords(self) -> str:
            raise AssertionError("keywords should not be accessed for pure CQ skip")

    class _Config:
        async def drunkenness(self) -> int:
            return 0

    monkeypatch.setattr(
        "src.plugins.repeater.responder.get_bots",
        dict,
    )

    result = await Responder._context_find(
        _ChatData(),
        _Config(),
        defaultdict(lambda: defaultdict(list)),
        defaultdict(list),
        defaultdict(lambda: deque(maxlen=16)),
    )

    assert result is None

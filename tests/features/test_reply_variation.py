from __future__ import annotations

from types import SimpleNamespace

from pallas.product.llm.reply_variation import build_recent_reply_ending_hint


def test_build_recent_reply_ending_hint_collects_natural_endings() -> None:
    turns = [
        SimpleNamespace(role="assistant", content="其实就是这样"),
        SimpleNamespace(role="assistant", content="那也不是不行。"),
        SimpleNamespace(role="assistant", content="行啊"),
    ]

    hint = build_recent_reply_ending_hint(turns)

    assert hint.startswith("\n【收尾变化参考】")
    assert "就是这样"[-4:] in hint
    assert "不是不行"[-4:] in hint
    assert "行啊" in hint

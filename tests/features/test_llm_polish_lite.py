from __future__ import annotations

from pallas.product.llm.config import (
    resolve_llm_polish_lite_enabled,
    resolve_llm_repeater_flags,
    resolve_llm_repeater_mode,
)
from pallas.product.llm.polish_lite import build_polish_lite_user_text, should_polish_lite_sample


def test_build_polish_lite_user_text() -> None:
    text = build_polish_lite_user_text("夜宵吃什么", "小炒黄牛肉")
    assert "【用户消息】夜宵吃什么" in text
    assert "【候选回复】小炒黄牛肉" in text
    assert "勿加设定词" in text


def test_should_polish_lite_sample_deterministic() -> None:
    first = should_polish_lite_sample(1, 2, 99, sample_rate=0.5)
    second = should_polish_lite_sample(1, 2, 99, sample_rate=0.5)
    assert first == second


def test_resolve_select_polish_lite_mode(monkeypatch) -> None:
    monkeypatch.setattr(
        "pallas.product.llm.config.repo_env_raw_value",
        lambda key: "select_polish_lite" if key == "LLM_REPEATER_MODE" else None,
    )
    assert resolve_llm_repeater_mode() == "select_polish_lite"
    assert resolve_llm_repeater_flags() == (False, False, True)
    assert resolve_llm_polish_lite_enabled() is True

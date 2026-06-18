from __future__ import annotations

from pallas.product.llm.memory.retrieve import memory_relevance_score, tokenize_for_memory
from pallas.product.llm.memory.teach import parse_memory_teach
from pallas.product.llm.status import gate_defer_total, gate_skip_total
from pallas.product.llm.tools.overrides import clear_tool_description_overrides_cache, load_tool_description_overrides


def test_parse_memory_teach() -> None:
    assert parse_memory_teach("记住：银灰是我推") == "银灰是我推"
    assert parse_memory_teach("请你记住这个梗") == "这个梗"
    assert parse_memory_teach("今天天气不错") is None


def test_memory_relevance_score() -> None:
    score = memory_relevance_score("银灰是谁", keywords="银灰,近卫", content="银灰是谢拉格军阀")
    assert score > 0


def test_tokenize_for_memory() -> None:
    tokens = tokenize_for_memory("银灰是我推")
    assert "银灰" in tokens


def test_gate_totals() -> None:
    snap = {"by_task": {"llm_chat": {"reply_gate_skip": 2, "reply_gate_defer": 1}}}
    assert gate_skip_total(snap) == 2
    assert gate_defer_total(snap) == 1


def test_tool_description_overrides_empty_without_file(tmp_path, monkeypatch) -> None:
    clear_tool_description_overrides_cache()
    monkeypatch.setattr(
        "pallas.product.llm.tools.overrides.plugin_data_dir",
        lambda *_args, **_kwargs: tmp_path,
    )
    assert load_tool_description_overrides() == {}

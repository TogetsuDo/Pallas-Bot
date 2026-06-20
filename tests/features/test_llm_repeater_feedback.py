from __future__ import annotations

from pallas.product.llm.config import clear_llm_config_cache, get_llm_config
from pallas.product.llm.repeater_feedback import (
    LlmRepeaterFeedbackEntry,
    append_feedback_entry,
    build_feedback_entry,
    feedback_entries_path,
    group_feedback_bias_snapshot,
    list_group_feedback_entries,
    should_collect_llm_repeater_feedback,
)


def test_llm_repeater_feedback_defaults_disabled_bias_writeback(monkeypatch) -> None:
    clear_llm_config_cache()
    monkeypatch.delenv("LLM_REPEATER_FEEDBACK_ENABLED", raising=False)
    monkeypatch.delenv("LLM_REPEATER_BIAS_ENABLED", raising=False)
    monkeypatch.delenv("LLM_REPEATER_WRITEBACK_ENABLED", raising=False)

    cfg = get_llm_config()

    assert cfg.llm_repeater_feedback_enabled is False
    assert cfg.llm_repeater_bias_enabled is False
    assert cfg.llm_repeater_writeback_enabled is False


def test_should_collect_llm_repeater_feedback_accepts_short_group_reply() -> None:
    accepted = should_collect_llm_repeater_feedback(
        task_type="llm_chat",
        group_id=123,
        user_text="你又来这套",
        reply_text="少来。",
        source_tags=[],
    )

    assert accepted is True


def test_should_collect_llm_repeater_feedback_rejects_long_explanatory_reply() -> None:
    accepted = should_collect_llm_repeater_feedback(
        task_type="llm_chat",
        group_id=123,
        user_text="银灰是谁",
        reply_text="银灰是《明日方舟》中的六星近卫干员，通常被视为谢拉格领袖，拥有很强的爆发能力。",
        source_tags=[],
    )

    assert accepted is False


def test_build_feedback_entry_defaults_writeback_false() -> None:
    entry = build_feedback_entry(
        bot_id=10001,
        group_id=123,
        user_id=456,
        request_id="req-1",
        user_text="你又来这套",
        reply_text="少来。",
    )

    assert isinstance(entry, LlmRepeaterFeedbackEntry)
    assert entry.entry_id == "req-1"
    assert entry.eligible_for_bias is True
    assert entry.eligible_for_writeback is False


def test_group_feedback_bias_snapshot_empty_when_no_entries(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PALLAS_DATA_DIR", str(tmp_path))

    snap = group_feedback_bias_snapshot(group_id=123, limit=50)

    assert snap["count"] == 0
    assert snap["top_replies"] == []


def test_group_feedback_bias_snapshot_aggregates_recent_unique_bias_entries(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PALLAS_DATA_DIR", str(tmp_path))

    append_feedback_entry(
        build_feedback_entry(
            bot_id=10001,
            group_id=123,
            user_id=456,
            request_id="req-1",
            user_text="你又来这套",
            reply_text="少来。",
            behavior_scene="banter",
        )
    )
    append_feedback_entry(
        build_feedback_entry(
            bot_id=10001,
            group_id=123,
            user_id=457,
            request_id="req-2",
            user_text="你继续说",
            reply_text="少来。",
            behavior_scene="banter",
        )
    )
    append_feedback_entry(
        build_feedback_entry(
            bot_id=10001,
            group_id=123,
            user_id=458,
            request_id="req-3",
            user_text="你先别急",
            reply_text="行吧。",
            behavior_scene="venting",
        )
    )
    append_feedback_entry(
        build_feedback_entry(
            bot_id=10001,
            group_id=123,
            user_id=459,
            request_id="req-4",
            user_text="别学这个",
            reply_text="这条不算。",
            behavior_scene="banter",
            eligible_for_bias=False,
        )
    )

    snap = group_feedback_bias_snapshot(group_id=123, limit=50)

    assert snap["count"] == 3
    assert snap["top_replies"] == ["少来。", "行吧。"]
    assert snap["scenes"] == ["banter", "venting"]


def test_group_feedback_bias_snapshot_skips_bad_lines(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PALLAS_DATA_DIR", str(tmp_path))
    append_feedback_entry(
        build_feedback_entry(
            bot_id=10001,
            group_id=123,
            user_id=456,
            request_id="req-1",
            user_text="你又来这套",
            reply_text="少来。",
            behavior_scene="banter",
        )
    )
    path = feedback_entries_path()
    with path.open("a", encoding="utf-8") as handle:
        handle.write("{bad json}\n")
        handle.write('{"request_id":"broken"}\n')
        handle.write('{"entry_id":"req-x"')
    append_feedback_entry(
        build_feedback_entry(
            bot_id=10001,
            group_id=123,
            user_id=457,
            request_id="req-2",
            user_text="你先别急",
            reply_text="行吧。",
            behavior_scene="venting",
        )
    )

    rows = list_group_feedback_entries(group_id=123, limit=50)
    snap = group_feedback_bias_snapshot(group_id=123, limit=50)

    assert [row.request_id for row in rows] == ["req-1", "req-2"]
    assert snap["count"] == 2
    assert snap["top_replies"] == ["少来。", "行吧。"]


def test_list_group_feedback_entries_dedupes_recent_request_id(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PALLAS_DATA_DIR", str(tmp_path))
    append_feedback_entry(
        build_feedback_entry(
            bot_id=10001,
            group_id=123,
            user_id=456,
            request_id="req-1",
            user_text="你又来这套",
            reply_text="少来。",
            behavior_scene="banter",
        )
    )
    append_feedback_entry(
        build_feedback_entry(
            bot_id=10001,
            group_id=123,
            user_id=456,
            request_id="req-1",
            user_text="你又来这套",
            reply_text="少来。",
            behavior_scene="banter",
        )
    )
    append_feedback_entry(
        build_feedback_entry(
            bot_id=10001,
            group_id=123,
            user_id=457,
            request_id="req-2",
            user_text="你先别急",
            reply_text="行吧。",
            behavior_scene="venting",
        )
    )

    rows = list_group_feedback_entries(group_id=123, limit=50)
    snap = group_feedback_bias_snapshot(group_id=123, limit=50)

    assert [row.request_id for row in rows] == ["req-1", "req-2"]
    assert snap["count"] == 2
    assert snap["top_replies"] == ["少来。", "行吧。"]


def test_list_group_feedback_entries_dedupes_same_request_id_with_different_entry_id(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("PALLAS_DATA_DIR", str(tmp_path))
    append_feedback_entry(
        build_feedback_entry(
            entry_id="entry-a",
            bot_id=10001,
            group_id=123,
            user_id=456,
            request_id="req-1",
            user_text="你又来这套",
            reply_text="少来。",
            behavior_scene="banter",
        )
    )
    append_feedback_entry(
        build_feedback_entry(
            entry_id="entry-b",
            bot_id=10001,
            group_id=123,
            user_id=456,
            request_id="req-1",
            user_text="你又来这套",
            reply_text="少来。",
            behavior_scene="banter",
        )
    )
    append_feedback_entry(
        build_feedback_entry(
            entry_id="entry-c",
            bot_id=10001,
            group_id=123,
            user_id=457,
            request_id="req-2",
            user_text="你先别急",
            reply_text="行吧。",
            behavior_scene="venting",
        )
    )

    rows = list_group_feedback_entries(group_id=123, limit=50)
    snap = group_feedback_bias_snapshot(group_id=123, limit=50)

    assert [row.entry_id for row in rows] == ["entry-b", "entry-c"]
    assert [row.request_id for row in rows] == ["req-1", "req-2"]
    assert snap["count"] == 2

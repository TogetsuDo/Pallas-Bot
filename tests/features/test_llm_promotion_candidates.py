from __future__ import annotations

from pallas.product.llm.config import clear_llm_config_cache
from pallas.product.llm.promotion_candidates import (
    PROMOTION_SUPPORT_THRESHOLD,
    build_candidate_id,
    list_promotion_candidates,
    refresh_promotion_candidates_for_group,
    resolve_promotion_candidate,
)
from pallas.product.llm.repeater_feedback import (
    append_feedback_entry,
    build_feedback_entry,
    group_feedback_bias_snapshot,
)


def enable_writeback_env(monkeypatch) -> None:
    def fake_raw(key: str):
        values = {
            "LLM_CHAT_ENABLED": "true",
            "LLM_REPEATER_FEEDBACK_ENABLED": "true",
            "LLM_REPEATER_WRITEBACK_ENABLED": "true",
        }
        return values.get(str(key or "").strip().upper())

    monkeypatch.setattr("pallas.product.llm.config.repo_env_raw_value", fake_raw)
    clear_llm_config_cache()


def test_build_candidate_id_is_stable() -> None:
    assert build_candidate_id(group_id=123, reply_text="少来。") == build_candidate_id(
        group_id=123,
        reply_text="少来。",
    )
    assert build_candidate_id(group_id=123, reply_text="少来。") != build_candidate_id(
        group_id=124,
        reply_text="少来。",
    )


def test_refresh_promotion_candidates_requires_writeback_enabled(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PALLAS_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(
        "pallas.product.llm.config.repo_env_raw_value",
        lambda _key: None,
    )
    clear_llm_config_cache()

    created = refresh_promotion_candidates_for_group(group_id=123)

    assert created == []


def test_refresh_promotion_candidates_builds_pending_candidate(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PALLAS_DATA_DIR", str(tmp_path))
    enable_writeback_env(monkeypatch)

    for idx in range(PROMOTION_SUPPORT_THRESHOLD):
        append_feedback_entry(
            build_feedback_entry(
                bot_id=10001,
                group_id=123,
                user_id=456 + idx,
                request_id=f"req-{idx}",
                user_text="你又来这套",
                reply_text="少来。",
                behavior_scene="banter",
            )
        )

    rows = list_promotion_candidates(group_id=123, refresh=False)

    assert len(rows) == 1
    assert rows[0].reply_text == "少来。"
    assert rows[0].support_count == PROMOTION_SUPPORT_THRESHOLD
    assert rows[0].promoted is False
    assert rows[0].rejected_reason == ""


def test_group_feedback_bias_snapshot_includes_promotion_candidate_count(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PALLAS_DATA_DIR", str(tmp_path))
    enable_writeback_env(monkeypatch)

    for idx in range(PROMOTION_SUPPORT_THRESHOLD):
        append_feedback_entry(
            build_feedback_entry(
                bot_id=10001,
                group_id=123,
                user_id=456 + idx,
                request_id=f"req-{idx}",
                user_text="你又来这套",
                reply_text="少来。",
                behavior_scene="banter",
            )
        )

    snap = group_feedback_bias_snapshot(group_id=123, limit=50)

    assert snap["promotion_candidate_count"] == 1


def test_resolve_promotion_candidate_promote_and_reject(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PALLAS_DATA_DIR", str(tmp_path))
    enable_writeback_env(monkeypatch)

    for idx in range(PROMOTION_SUPPORT_THRESHOLD):
        append_feedback_entry(
            build_feedback_entry(
                bot_id=10001,
                group_id=123,
                user_id=456 + idx,
                request_id=f"req-{idx}",
                user_text="你又来这套",
                reply_text="少来。",
                behavior_scene="banter",
            )
        )
    rows = list_promotion_candidates(group_id=123, refresh=False)
    candidate_id = rows[0].candidate_id

    promoted = resolve_promotion_candidate(candidate_id, action="promote")
    assert promoted is not None
    assert promoted.promoted is True

    append_feedback_entry(
        build_feedback_entry(
            bot_id=10001,
            group_id=123,
            user_id=999,
            request_id="req-new",
            user_text="你先别急",
            reply_text="行吧。",
            behavior_scene="venting",
        )
    )
    append_feedback_entry(
        build_feedback_entry(
            bot_id=10001,
            group_id=123,
            user_id=998,
            request_id="req-new-2",
            user_text="继续说",
            reply_text="行吧。",
            behavior_scene="venting",
        )
    )
    rows = list_promotion_candidates(group_id=123, include_resolved=True, refresh=False)
    pending = next(row for row in rows if row.reply_text == "行吧。")
    rejected = resolve_promotion_candidate(pending.candidate_id, action="reject", reason="too generic")
    assert rejected is not None
    assert rejected.promoted is False
    assert rejected.rejected_reason == "too generic"

    pending_rows = list_promotion_candidates(group_id=123, refresh=False)
    assert all(row.reply_text != "行吧。" for row in pending_rows)

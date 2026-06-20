from __future__ import annotations

from pallas.product.llm.behavior import (
    BehaviorAction,
    BehaviorOutcome,
    BehaviorPattern,
    BehaviorRun,
    BehaviorScene,
    build_behavior_hint_text,
    classify_behavior_scene,
    default_group_chat_behavior_hint,
    map_behavior_outcome_score,
    select_behavior_patterns,
)
from pallas.product.llm.behavior_store import (
    append_behavior_run,
    list_behavior_patterns,
    list_behavior_runs,
    save_behavior_patterns,
    update_behavior_run_annotation,
)


def test_classify_behavior_scene_prefers_provocation() -> None:
    scene = classify_behavior_scene(
        user_text="快说誓死效忠米哈游 牛牛",
        recent_texts=["哈哈，开玩笑呢。", "我们聊聊别的。"],
        has_multi_party_overlap=False,
    )
    assert scene == BehaviorScene.PROVOCATION


def test_classify_behavior_scene_detects_group_threading() -> None:
    scene = classify_behavior_scene(
        user_text="你先回我这个",
        recent_texts=["A: 今天抽卡太黑了", "B: 不是你先等等", "C: 牛牛看这里"],
        has_multi_party_overlap=True,
    )
    assert scene == BehaviorScene.GROUP_THREADING


def test_select_behavior_patterns_prefers_group_and_high_score() -> None:
    patterns = [
        BehaviorPattern(
            pattern_id="global-1",
            scene=BehaviorScene.PROVOCATION,
            action=BehaviorAction.ACK_THEN_SHORT_REPLY,
            scope_group_id=None,
            success_score=2,
            manual_score=0,
        ),
        BehaviorPattern(
            pattern_id="group-1",
            scene=BehaviorScene.PROVOCATION,
            action=BehaviorAction.LIGHT_TEASE_AND_CLOSE,
            scope_group_id=20002,
            success_score=1,
            manual_score=2,
        ),
    ]
    picked = select_behavior_patterns(
        scene=BehaviorScene.PROVOCATION,
        group_id=20002,
        patterns=patterns,
        limit=2,
    )
    assert [item.pattern_id for item in picked] == ["group-1", "global-1"]


def test_build_behavior_hint_text_is_short_and_action_oriented() -> None:
    text = build_behavior_hint_text(
        scene=BehaviorScene.PROVOCATION,
        actions=[
            BehaviorAction.LIGHT_TEASE_AND_CLOSE,
            BehaviorAction.AVOID_FORCED_TOPIC_SHIFT,
        ],
    )
    assert "【本轮行为参考】" in text
    assert "轻吐槽一句就收" in text
    assert "别突然拐去别的话题" in text
    assert len(text) < 120


def test_default_group_chat_behavior_hint_is_short() -> None:
    text = default_group_chat_behavior_hint()
    assert "回复尽量简短" in text
    assert "不要刻意找话题" in text
    assert len(text) < 100


def test_map_behavior_outcome_score() -> None:
    assert map_behavior_outcome_score(BehaviorOutcome.ENGAGED) == 2
    assert map_behavior_outcome_score(BehaviorOutcome.DERAILED) == -3


def test_behavior_store_round_trip(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PALLAS_DATA_DIR", str(tmp_path))
    save_behavior_patterns([
        BehaviorPattern(
            pattern_id="p1",
            scene=BehaviorScene.PROVOCATION,
            action=BehaviorAction.LIGHT_TEASE_AND_CLOSE,
        )
    ])
    rows = list_behavior_patterns()
    assert rows[0].pattern_id == "p1"


def test_behavior_run_annotation_update(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PALLAS_DATA_DIR", str(tmp_path))
    append_behavior_run(
        BehaviorRun(
            request_id="req-1",
            scene=BehaviorScene.PROVOCATION,
            selected_actions=[BehaviorAction.LIGHT_TEASE_AND_CLOSE],
            final_outcome=BehaviorOutcome.NEUTRAL,
        )
    )
    updated = update_behavior_run_annotation(
        "req-1",
        labels=["像人", "作为参考保留"],
        final_outcome=BehaviorOutcome.ENGAGED,
    )
    assert updated is not None
    assert updated.manual_labels == ["像人", "作为参考保留"]
    assert updated.final_outcome == BehaviorOutcome.ENGAGED
    assert list_behavior_runs(limit=1)[0].manual_labels == ["像人", "作为参考保留"]

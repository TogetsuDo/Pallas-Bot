"""Scene-aware behavior primitives for llm_chat."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class BehaviorScene(StrEnum):
    PROVOCATION = "provocation"
    BANTER = "banter"
    SMALLTALK = "smalltalk"
    VENTING = "venting"
    GROUP_THREADING = "group_threading"
    LIGHT_HELP = "light_help"


class BehaviorAction(StrEnum):
    LIGHT_TEASE_AND_CLOSE = "light_tease_and_close"
    ACK_THEN_SHORT_REPLY = "ack_then_short_reply"
    FOLLOW_JOKE_ONCE = "follow_joke_once"
    ACK_EMOTION_NO_LECTURE = "ack_emotion_no_lecture"
    STAY_ON_CURRENT_TOPIC = "stay_on_current_topic"
    AVOID_FORCED_TOPIC_SHIFT = "avoid_forced_topic_shift"
    BRIEF_MULTI_PARTY_ANCHOR = "brief_multi_party_anchor"
    SHORT_HELP_THEN_STOP = "short_help_then_stop"


class BehaviorOutcome(StrEnum):
    ENGAGED = "engaged"
    NEUTRAL = "neutral"
    IGNORED = "ignored"
    AWKWARD = "awkward"
    DERAILED = "derailed"


class BehaviorPattern(BaseModel):
    pattern_id: str
    scene: BehaviorScene
    action: BehaviorAction
    scope_group_id: int | None = None
    success_score: int = 0
    manual_score: int = 0
    disabled: bool = False
    persona_affinity: str = ""
    trigger_features: list[str] = Field(default_factory=list)
    reference_examples: list[str] = Field(default_factory=list)


class BehaviorRun(BaseModel):
    request_id: str
    group_id: int | None = None
    user_id: int | None = None
    bot_id: int | None = None
    scene: BehaviorScene
    selected_pattern_ids: list[str] = Field(default_factory=list)
    selected_actions: list[BehaviorAction] = Field(default_factory=list)
    behavior_hint_text: str = ""
    final_outcome: BehaviorOutcome | None = None
    score_delta: int = 0
    manual_labels: list[str] = Field(default_factory=list)
    disabled: bool = False


_PROVOCATION_TOKENS = ("效忠", "反党", "走资派", "快说", "表态", "忠诚")
_VENTING_TOKENS = ("烦死", "气死", "无语", "沃日", "绷不住", "受不了")
_BANTER_TOKENS = ("哈哈", "乐", "蚌", "绷", "典", "梗")
_HELP_TOKENS = ("怎么", "为啥", "为什么", "咋", "能不能", "可以吗")

_ACTION_HINTS: dict[BehaviorAction, str] = {
    BehaviorAction.LIGHT_TEASE_AND_CLOSE: "这类怪话先接住，轻吐槽一句就收。",
    BehaviorAction.ACK_THEN_SHORT_REPLY: "先接住这句，再短回一句，不要铺开解释。",
    BehaviorAction.FOLLOW_JOKE_ONCE: "顺着梗接一次就好，不要越聊越偏。",
    BehaviorAction.ACK_EMOTION_NO_LECTURE: "先接情绪，不要马上上价值或教育。",
    BehaviorAction.STAY_ON_CURRENT_TOPIC: "只回当前这一句，不要扩成新话题。",
    BehaviorAction.AVOID_FORCED_TOPIC_SHIFT: "别突然拐去别的话题。",
    BehaviorAction.BRIEF_MULTI_PARTY_ANCHOR: "多人插话时只抓一个最该接的锚点。",
    BehaviorAction.SHORT_HELP_THEN_STOP: "给短帮助就收，不强行追问。",
}


def classify_behavior_scene(*, user_text: str, recent_texts: list[str], has_multi_party_overlap: bool) -> BehaviorScene:
    text = str(user_text or "").strip()
    if not text:
        return BehaviorScene.SMALLTALK
    if any(token in text for token in _PROVOCATION_TOKENS):
        return BehaviorScene.PROVOCATION
    if has_multi_party_overlap:
        return BehaviorScene.GROUP_THREADING
    if any(token in text for token in _VENTING_TOKENS):
        return BehaviorScene.VENTING
    if any(token in text for token in _HELP_TOKENS) or "?" in text or "？" in text:
        return BehaviorScene.LIGHT_HELP
    if any(token in text for token in _BANTER_TOKENS):
        return BehaviorScene.BANTER
    if (
        recent_texts
        and any("@" in item or "：" in item for item in recent_texts[-3:])
        and len({item[:1] for item in recent_texts[-3:] if item}) >= 2
    ):
        return BehaviorScene.GROUP_THREADING
    return BehaviorScene.SMALLTALK


def select_behavior_patterns(
    *,
    scene: BehaviorScene,
    group_id: int | None,
    patterns: list[BehaviorPattern],
    limit: int = 2,
) -> list[BehaviorPattern]:
    rows = [
        item
        for item in patterns
        if not item.disabled
        and item.scene == scene
        and (item.scope_group_id is None or item.scope_group_id == group_id)
    ]
    rows.sort(
        key=lambda item: (
            0 if group_id is not None and item.scope_group_id == group_id else 1,
            -(int(item.success_score) + int(item.manual_score)),
            item.pattern_id,
        )
    )
    return rows[: max(1, int(limit))]


def build_behavior_hint_text(*, scene: BehaviorScene, actions: list[BehaviorAction]) -> str:
    lines = [_ACTION_HINTS[item] for item in actions if item in _ACTION_HINTS]
    if not lines:
        return ""
    return "【本轮行为参考】\n- " + "\n- ".join(lines[:2])


def default_group_chat_behavior_hint() -> str:
    return "【群聊注意】回复尽量简短；一次只回一个主话题；注意多人互动；不要刻意找话题。"


def map_behavior_outcome_score(outcome: BehaviorOutcome) -> int:
    return {
        BehaviorOutcome.ENGAGED: 2,
        BehaviorOutcome.NEUTRAL: 0,
        BehaviorOutcome.IGNORED: -1,
        BehaviorOutcome.AWKWARD: -2,
        BehaviorOutcome.DERAILED: -3,
    }[outcome]

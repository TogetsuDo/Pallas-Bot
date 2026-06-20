"""@闲聊短期去重与群聊节奏辅助。"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pallas.product.llm.session_store import LlmChatTurn

_REPEATED_OPENERS = (
    "其实",
    "这倒是",
    "怎么说呢",
    "感觉",
    "我觉得",
    "确实",
    "一般来说",
)

_USER_WAIT_SUFFIXES = ("?", "？", "...", "…", "、")
_USER_WAIT_TOKENS = ("等等", "等下", "先别", "我补一句", "还有", "然后")
_STRUCTURE_MARKERS = ("先", "别", "可以", "不用", "慢慢", "一下", "这事", "你先")


def should_wait_for_more(user_text: str) -> bool:
    text = str(user_text or "").strip()
    if not text:
        return False
    if any(text.endswith(token) for token in _USER_WAIT_SUFFIXES):
        return True
    return any(token in text[-8:] for token in _USER_WAIT_TOKENS)


def repeated_assistant_openers(turns: list[LlmChatTurn], *, limit: int = 3) -> list[str]:
    seen: list[str] = []
    for turn in reversed(turns):
        if turn.role != "assistant":
            continue
        text = str(turn.content or "").strip()
        if not text:
            continue
        opener = next((item for item in _REPEATED_OPENERS if text.startswith(item)), "")
        if opener and opener not in seen:
            seen.append(opener)
        if len(seen) >= limit:
            break
    return seen


def recent_assistant_endings(turns: list[LlmChatTurn], *, limit: int = 3) -> list[str]:
    seen: list[str] = []
    for turn in reversed(turns):
        if turn.role != "assistant":
            continue
        text = str(turn.content or "").strip()
        if not text:
            continue
        compact = text.rstrip("。！？!?~～…，,、 ")
        if not compact:
            continue
        ending = compact[-4:]
        if len(ending) < 2 or ending in seen:
            continue
        seen.append(ending)
        if len(seen) >= limit:
            break
    return seen


def build_recent_reply_ending_hint(turns: list[LlmChatTurn]) -> str:
    endings = recent_assistant_endings(turns)
    if not endings:
        return ""
    return "\n【收尾变化参考】这轮可优先试试这些自然收口：" + "、".join(endings) + "。"


def build_recent_reply_variation_hint(turns: list[LlmChatTurn]) -> str:
    assistant_texts = [str(turn.content or "").strip() for turn in turns if turn.role == "assistant" and turn.content]
    if not assistant_texts:
        return ""

    hints: list[str] = []
    openers = repeated_assistant_openers(turns)
    if openers:
        hints.append("最近几轮别再用这些开头：" + "、".join(openers))

    recent_lengths = [len(text) for text in assistant_texts[-3:]]
    if recent_lengths and min(recent_lengths) >= 28:
        hints.append("最近解释偏满，这轮优先短一点，像顺手接一句")
    elif len(assistant_texts) >= 3:
        structural_texts = assistant_texts[-3:]
        if min(len(text) for text in structural_texts) >= 14:
            shared_markers = sum(
                1
                for marker in _STRUCTURE_MARKERS
                if sum(1 for text in structural_texts if marker in text) >= 2
            )
            if shared_markers >= 3:
                hints.append("最近解释偏满，这轮优先短一点，像顺手接一句")

    if len(assistant_texts) >= 3:
        structural_texts = assistant_texts[-3:]
        shared_markers = [
            marker
            for marker in _STRUCTURE_MARKERS
            if sum(1 for text in structural_texts if marker in text) >= 2
        ]
        if len(shared_markers) >= 4:
            hints.append("最近句式有点一个模子，少用“先判断一下、再补解释”的答法")

    endings = [text[-1] for text in assistant_texts[-3:] if text]
    if len(endings) >= 3 and len(set(endings)) == 1:
        hints.append("最近收尾太像模板，换个自然收口")

    if not hints:
        return ""
    return "【本轮表达去重】\n- " + "\n- ".join(hints[:3])

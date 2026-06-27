from __future__ import annotations

from typing import Any

from .prompt_guard import sanitize_prompt_literal


def match_message_affect_triggers(plain_text: str, triggers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    plain = str(plain_text or "").strip().lower()
    if not plain or not triggers:
        return []
    matched: list[dict[str, Any]] = []
    for item in triggers:
        if not isinstance(item, dict):
            continue
        phrase = str(item.get("phrase") or "").strip().lower()
        if phrase and phrase in plain:
            matched.append(item)
    matched.sort(key=lambda row: float(row.get("weight") or 0.0), reverse=True)
    return matched[:3]


def build_affect_trigger_turn_hint(plain_text: str, matched_triggers: list[dict[str, Any]]) -> str:
    if not matched_triggers:
        return ""

    hints: list[str] = []
    for item in matched_triggers[:2]:
        phrase = sanitize_prompt_literal(str(item.get("phrase") or ""), max_len=24)
        if not phrase:
            continue
        warmth_delta = float(item.get("warmth_delta") or 0.0)
        assertiveness_delta = float(item.get("assertiveness_delta") or 0.0)
        tone_parts: list[str] = []
        if warmth_delta >= 0.08:
            tone_parts.append("语气可稍软、更接梗")
        elif warmth_delta <= -0.08:
            tone_parts.append("语气偏克制")
        if assertiveness_delta >= 0.08:
            tone_parts.append("可适度顶一句")
        elif assertiveness_delta <= -0.08:
            tone_parts.append("少反呛")
        if tone_parts:
            hints.append(f"提到「{phrase}」时，{'，'.join(tone_parts)}")
        else:
            hints.append(f"提到「{phrase}」时，按本群习惯接话")
    if not hints:
        return ""
    return "【情境触发】" + "；".join(hints)


def format_situational_expression_pairs(
    matched_triggers: list[dict[str, Any]],
    candidates: list[str],
    *,
    user_text: str = "",
) -> list[str]:
    lines: list[str] = []
    remaining = [sanitize_prompt_literal(str(item or "").strip(), max_len=24) for item in candidates]
    remaining = [item for item in remaining if item]

    for item in matched_triggers[:3]:
        phrase = sanitize_prompt_literal(str(item.get("phrase") or ""), max_len=24)
        if not phrase:
            continue
        if not remaining:
            break
        reply = remaining.pop(0)
        lines.append(f"当「{phrase}」时，可以参考「{reply}」")

    if remaining and not matched_triggers:
        query_snippet = sanitize_prompt_literal(str(user_text or "").strip()[:16], max_len=16)
        for reply in remaining[:2]:
            if query_snippet:
                lines.append(f"针对「{query_snippet}」，可以参考「{reply}」")
            else:
                lines.append(f"可以参考本群说法「{reply}」")
    return lines


def format_dynamic_expression_hint(trigger_hint: str, situational_lines: list[str]) -> str:
    sections: list[str] = []
    if str(trigger_hint or "").strip():
        sections.append(str(trigger_hint).strip())
    if situational_lines:
        sections.append("【表达习惯参考】" + "；".join(situational_lines))
    if not sections:
        return ""
    return "\n" + "\n".join(sections) + "。"

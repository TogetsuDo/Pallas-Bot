"""按 task_type 解析回调失败文案与会话写入策略。"""

from __future__ import annotations

from pallas.core.platform.ai_callback.task_types import (
    DEFAULT_FAIL_REPLY,
    DRAW_IMAGE_TASK_TYPE,
    LEGACY_LLM_CHAT_TASK_TYPES,
    LLM_SESSION_TASK_TYPES,
    REPEATER_FALLBACK_TASK_TYPE,
    REPEATER_POLISH_LITE_TASK_TYPE,
    REPEATER_POLISH_TASK_TYPE,
    REPEATER_SELECT_TASK_TYPE,
)


def should_suppress_llm_duplicate_reply(task: dict, reply_text: str) -> bool:
    if task.get("task_type") not in LEGACY_LLM_CHAT_TASK_TYPES:
        return False
    text = str(reply_text or "").strip()
    if not text:
        return False
    last = str(task.get("last_reply_text") or "").strip()
    if not last:
        return False
    return text == last


def failure_reply_for_task(task: dict) -> str | None:
    """失败时发往群的消息；None 表示静默失败。"""
    task_type = task.get("task_type")
    if task_type == REPEATER_FALLBACK_TASK_TYPE:
        return None
    if task_type in LEGACY_LLM_CHAT_TASK_TYPES:
        from packages.llm_chat.replies import LLM_CHAT_FAILED_REPLY

        return LLM_CHAT_FAILED_REPLY
    if task_type == REPEATER_POLISH_TASK_TYPE:
        fallback = str(task.get("fallback_text") or "").strip()
        return fallback or DEFAULT_FAIL_REPLY
    if task_type == REPEATER_POLISH_LITE_TASK_TYPE:
        fallback = str(task.get("fallback_text") or "").strip()
        return fallback or None
    if task_type == REPEATER_SELECT_TASK_TYPE:
        fallback = str(task.get("fallback_text") or "").strip()
        return fallback or None
    if task_type == DRAW_IMAGE_TASK_TYPE:
        from pallas.core.platform.plugin_runtime.resolve import import_plugin_submodule

        draw_replies = import_plugin_submodule("draw", "replies")
        return draw_replies.DRAW_VAGUE_REPLY
    return DEFAULT_FAIL_REPLY


def should_append_llm_session(task: dict) -> bool:
    return task.get("task_type") in LLM_SESSION_TASK_TYPES

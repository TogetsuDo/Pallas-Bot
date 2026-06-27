"""Soft feedback primitives for llm_chat -> repeater."""

from __future__ import annotations

import json
import os
import time
from collections import Counter, deque
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from pallas.core.foundation.paths import plugin_data_dir
from pallas.core.platform.ai_callback.task_types import (
    LLM_CHAT_TASK_TYPE,
    REPEATER_FALLBACK_TASK_TYPE,
    REPEATER_POLISH_LITE_TASK_TYPE,
    REPEATER_POLISH_TASK_TYPE,
    REPEATER_SELECT_TASK_TYPE,
)
from pallas.product.llm.kernel.feedback_models import FeedbackBiasSnapshot
from pallas.product.llm.kernel.memory_governance import (
    can_collect_feedback,
    can_promote_writeback,
)

_BLOCKED_SOURCE_TAGS = {"memory", "relationship", "tool", "knowledge"}
_BLOCKED_REPLY_HINTS = (
    "因为",
    "通常",
    "一般来说",
    "总结一下",
    "首先",
)
_MAX_REPLY_LEN = 32
_MAX_CORRECTION_LEN = 120
_TOP_REPLIES_LIMIT = 3
_TOP_SCENES_LIMIT = 5
_RECENT_WINDOW_MULTIPLIER = 4

_FEEDBACK_TASK_TYPES = frozenset({
    LLM_CHAT_TASK_TYPE,
    REPEATER_FALLBACK_TASK_TYPE,
    REPEATER_POLISH_TASK_TYPE,
    REPEATER_POLISH_LITE_TASK_TYPE,
    REPEATER_SELECT_TASK_TYPE,
})

_TASK_TYPE_TO_LLM_ROUTE = {
    REPEATER_FALLBACK_TASK_TYPE: "corpus_fallback",
    REPEATER_POLISH_TASK_TYPE: "corpus_polish",
    REPEATER_POLISH_LITE_TASK_TYPE: "corpus_polish_lite",
    REPEATER_SELECT_TASK_TYPE: "corpus_select",
}


class LlmRepeaterFeedbackEntry(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")

    entry_id: str
    created_at: int
    bot_id: int
    group_id: int
    user_id: int
    request_id: str
    user_text: str
    reply_text: str
    behavior_scene: str = ""
    behavior_actions: list[str] = Field(default_factory=list)
    llm_route: str = ""
    source_tags: list[str] = Field(default_factory=list)
    eligible_for_bias: bool = True
    eligible_for_writeback: bool = False
    corrected_reply_text: str = ""
    corrected_at: int = 0


def feedback_base_dir() -> Path:
    env_dir = str(os.environ.get("PALLAS_DATA_DIR") or "").strip()
    if env_dir:
        root = Path(env_dir)
        root.mkdir(parents=True, exist_ok=True)
        path = root / "llm_repeater_feedback"
        path.mkdir(parents=True, exist_ok=True)
        return path
    path = plugin_data_dir("pb_webui", create=True) / "llm_repeater_feedback"
    path.mkdir(parents=True, exist_ok=True)
    return path


def feedback_entries_path() -> Path:
    return feedback_base_dir() / "entries.jsonl"


def resolve_feedback_llm_route(*, task_type: str, llm_route: str = "") -> str:
    explicit = str(llm_route or "").strip()
    if explicit:
        return explicit
    return _TASK_TYPE_TO_LLM_ROUTE.get(str(task_type or "").strip().lower(), "")


def is_feedback_task_type(task_type: str) -> bool:
    return str(task_type or "").strip().lower() in _FEEDBACK_TASK_TYPES


def should_collect_llm_repeater_feedback(
    *,
    task_type: str,
    group_id: int | None,
    user_text: str,
    reply_text: str,
    source_tags: list[str],
    fallback_text: str = "",
) -> bool:
    normalized_task = str(task_type or "").strip().lower()
    if normalized_task not in _FEEDBACK_TASK_TYPES:
        return False
    if int(group_id or 0) <= 0:
        return False
    trigger_text = str(user_text or "").strip()
    if normalized_task != LLM_CHAT_TASK_TYPE and not trigger_text:
        trigger_text = str(fallback_text or "").strip()
    if not trigger_text:
        return False
    plain_reply = str(reply_text or "").strip()
    if not plain_reply or len(plain_reply) > _MAX_REPLY_LEN:
        return False
    normalized_tags = {str(tag).strip().lower() for tag in source_tags if str(tag).strip()}
    if normalized_tags & _BLOCKED_SOURCE_TAGS:
        return False
    return not any(token in plain_reply for token in _BLOCKED_REPLY_HINTS)


def build_feedback_entry(**kwargs: Any) -> LlmRepeaterFeedbackEntry:
    return LlmRepeaterFeedbackEntry(
        entry_id=str(kwargs.get("entry_id") or kwargs["request_id"]).strip(),
        created_at=int(kwargs.get("created_at") or time.time()),
        bot_id=int(kwargs["bot_id"]),
        group_id=int(kwargs["group_id"]),
        user_id=int(kwargs["user_id"]),
        request_id=str(kwargs["request_id"]).strip(),
        user_text=str(kwargs.get("user_text") or "").strip(),
        reply_text=str(kwargs.get("reply_text") or "").strip(),
        behavior_scene=str(kwargs.get("behavior_scene") or "").strip(),
        behavior_actions=[
            str(item).strip() for item in list(kwargs.get("behavior_actions") or []) if str(item).strip()
        ],
        llm_route=str(kwargs.get("llm_route") or "").strip(),
        source_tags=[str(item).strip() for item in list(kwargs.get("source_tags") or []) if str(item).strip()],
        eligible_for_bias=bool(kwargs.get("eligible_for_bias", True)),
        eligible_for_writeback=bool(kwargs.get("eligible_for_writeback", False)),
        corrected_reply_text=str(kwargs.get("corrected_reply_text") or "").strip(),
        corrected_at=int(kwargs.get("corrected_at") or 0),
    )


def append_feedback_entry(entry: LlmRepeaterFeedbackEntry) -> None:
    path = feedback_entries_path()
    needs_leading_newline = False
    if path.exists() and path.stat().st_size > 0:
        with path.open("rb") as existing:
            existing.seek(-1, os.SEEK_END)
            needs_leading_newline = existing.read(1) != b"\n"
    with path.open("a", encoding="utf-8") as handle:
        if needs_leading_newline:
            handle.write("\n")
        handle.write(json.dumps(entry.model_dump(mode="json"), ensure_ascii=False) + "\n")
    from pallas.product.llm.promotion_candidates import note_feedback_entry_for_promotion

    note_feedback_entry_for_promotion(entry)


def _iter_feedback_entries(path: Path):
    with path.open(encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
                yield LlmRepeaterFeedbackEntry.model_validate(payload)
            except (TypeError, ValueError):
                continue


def _dedupe_key(entry: LlmRepeaterFeedbackEntry) -> str:
    request_id = str(entry.request_id).strip()
    if request_id:
        return f"request:{request_id}"
    entry_id = str(entry.entry_id).strip()
    if entry_id:
        return f"entry:{entry_id}"
    return f"fallback:{entry.group_id}:{entry.user_id}:{entry.created_at}:{entry.reply_text}"


def _write_feedback_entries(rows: list[LlmRepeaterFeedbackEntry]) -> None:
    path = feedback_entries_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for item in rows:
            handle.write(json.dumps(item.model_dump(mode="json"), ensure_ascii=False) + "\n")


def _load_all_feedback_entries() -> list[LlmRepeaterFeedbackEntry]:
    path = feedback_entries_path()
    if not path.exists():
        return []
    return list(_iter_feedback_entries(path))


def find_feedback_entry(*, entry_id: str = "", request_id: str = "") -> LlmRepeaterFeedbackEntry | None:
    target_entry_id = str(entry_id or "").strip()
    target_request_id = str(request_id or "").strip()
    if not target_entry_id and not target_request_id:
        return None
    for item in reversed(_load_all_feedback_entries()):
        if target_entry_id and str(item.entry_id).strip() == target_entry_id:
            return item
        if target_request_id and str(item.request_id).strip() == target_request_id:
            return item
    return None


def effective_feedback_reply_text(entry: LlmRepeaterFeedbackEntry) -> str:
    corrected = str(entry.corrected_reply_text or "").strip()
    if corrected:
        return corrected
    return str(entry.reply_text or "").strip()


def set_feedback_entry_correction(
    *,
    entry_id: str = "",
    request_id: str = "",
    corrected_reply_text: str,
    create_fields: dict[str, Any] | None = None,
) -> LlmRepeaterFeedbackEntry | None:
    text = str(corrected_reply_text or "").strip()
    if not text:
        return None
    if len(text) > _MAX_CORRECTION_LEN:
        text = text[:_MAX_CORRECTION_LEN].rstrip()

    target_entry_id = str(entry_id or "").strip()
    target_request_id = str(request_id or "").strip()
    now = int(time.time())
    rows = _load_all_feedback_entries()
    for idx, item in enumerate(rows):
        matched = False
        if target_entry_id and str(item.entry_id).strip() == target_entry_id:
            matched = True
        elif target_request_id and str(item.request_id).strip() == target_request_id:
            matched = True
        if not matched:
            continue
        item.corrected_reply_text = text
        item.corrected_at = now
        item.eligible_for_bias = True
        rows[idx] = item
        _write_feedback_entries(rows)
        return item

    payload = dict(create_fields or {})
    if not payload:
        return None
    req_id = target_request_id or str(payload.get("request_id") or "").strip()
    if not req_id:
        req_id = f"manual-corr-{now}"
    entry = build_feedback_entry(
        entry_id=target_entry_id or req_id,
        request_id=req_id,
        bot_id=int(payload["bot_id"]),
        group_id=int(payload["group_id"]),
        user_id=int(payload["user_id"]),
        user_text=str(payload.get("user_text") or "").strip(),
        reply_text=str(payload.get("reply_text") or "").strip(),
        behavior_scene=str(payload.get("behavior_scene") or "").strip(),
        llm_route=str(payload.get("llm_route") or "").strip(),
        eligible_for_bias=True,
        corrected_reply_text=text,
        corrected_at=now,
    )
    append_feedback_entry(entry)
    return entry


def clear_feedback_entry_correction(*, entry_id: str = "", request_id: str = "") -> LlmRepeaterFeedbackEntry | None:
    target_entry_id = str(entry_id or "").strip()
    target_request_id = str(request_id or "").strip()
    if not target_entry_id and not target_request_id:
        return None
    rows = _load_all_feedback_entries()
    updated: LlmRepeaterFeedbackEntry | None = None
    for idx, item in enumerate(rows):
        matched = False
        if target_entry_id and str(item.entry_id).strip() == target_entry_id:
            matched = True
        elif target_request_id and str(item.request_id).strip() == target_request_id:
            matched = True
        if not matched:
            continue
        item.corrected_reply_text = ""
        item.corrected_at = 0
        rows[idx] = item
        updated = item
        break
    if updated is None:
        return None
    _write_feedback_entries(rows)
    return updated


def set_feedback_entry_eligibility(
    *,
    entry_id: str = "",
    request_id: str = "",
    eligible_for_bias: bool,
) -> LlmRepeaterFeedbackEntry | None:
    target_entry_id = str(entry_id or "").strip()
    target_request_id = str(request_id or "").strip()
    if not target_entry_id and not target_request_id:
        return None
    rows = _load_all_feedback_entries()
    updated: LlmRepeaterFeedbackEntry | None = None
    for idx, item in enumerate(rows):
        matched = False
        if target_entry_id and str(item.entry_id).strip() == target_entry_id:
            matched = True
        elif target_request_id and str(item.request_id).strip() == target_request_id:
            matched = True
        if not matched:
            continue
        item.eligible_for_bias = bool(eligible_for_bias)
        rows[idx] = item
        updated = item
        break
    if updated is None:
        return None
    _write_feedback_entries(rows)
    return updated


def delete_feedback_entry(*, entry_id: str = "", request_id: str = "") -> bool:
    target_entry_id = str(entry_id or "").strip()
    target_request_id = str(request_id or "").strip()
    if not target_entry_id and not target_request_id:
        return False
    rows = _load_all_feedback_entries()
    kept: list[LlmRepeaterFeedbackEntry] = []
    removed = False
    for item in rows:
        matched = False
        if target_entry_id and str(item.entry_id).strip() == target_entry_id:
            matched = True
        elif target_request_id and str(item.request_id).strip() == target_request_id:
            matched = True
        if matched:
            removed = True
            continue
        kept.append(item)
    if not removed:
        return False
    _write_feedback_entries(kept)
    return True


def list_feedback_entries_for_session(
    *,
    bot_id: int,
    group_id: int,
    user_id: int,
    limit: int = 100,
) -> list[LlmRepeaterFeedbackEntry]:
    path = feedback_entries_path()
    if not path.exists():
        return []
    window_size = max(1, int(limit)) * _RECENT_WINDOW_MULTIPLIER
    recent: deque[LlmRepeaterFeedbackEntry] = deque(maxlen=window_size)
    target_group_id = int(group_id)
    target_bot_id = int(bot_id)
    target_user_id = int(user_id)
    for item in _iter_feedback_entries(path):
        if int(item.group_id) != target_group_id:
            continue
        if int(item.bot_id) != target_bot_id:
            continue
        if int(item.user_id) != target_user_id:
            continue
        recent.append(item)
    deduped: list[LlmRepeaterFeedbackEntry] = []
    seen_ids: set[str] = set()
    for item in reversed(recent):
        dedupe_key = _dedupe_key(item)
        if dedupe_key in seen_ids:
            continue
        seen_ids.add(dedupe_key)
        deduped.append(item)
    deduped.reverse()
    return deduped[-max(1, int(limit)) :]


def list_group_feedback_entries(*, group_id: int, limit: int = 50) -> list[LlmRepeaterFeedbackEntry]:
    path = feedback_entries_path()
    if not path.exists():
        return []
    window_size = max(1, int(limit)) * _RECENT_WINDOW_MULTIPLIER
    recent: deque[LlmRepeaterFeedbackEntry] = deque(maxlen=window_size)
    target_group_id = int(group_id)
    for item in _iter_feedback_entries(path):
        if int(item.group_id) != target_group_id:
            continue
        recent.append(item)
    deduped: list[LlmRepeaterFeedbackEntry] = []
    seen_ids: set[str] = set()
    for item in reversed(recent):
        dedupe_key = _dedupe_key(item)
        if dedupe_key in seen_ids:
            continue
        seen_ids.add(dedupe_key)
        deduped.append(item)
    deduped.reverse()
    return deduped[-max(1, int(limit)) :]


def group_feedback_bias_snapshot(*, group_id: int, limit: int = 50) -> dict[str, Any]:
    rows = [item for item in list_group_feedback_entries(group_id=group_id, limit=limit) if item.eligible_for_bias]
    reply_counter = Counter(
        effective_feedback_reply_text(item) for item in rows if effective_feedback_reply_text(item)
    )
    scene_counter = Counter(item.behavior_scene for item in rows if item.behavior_scene)
    top_replies = [text for text, _ in reply_counter.most_common(_TOP_REPLIES_LIMIT)]
    scenes = [text for text, _ in scene_counter.most_common(_TOP_SCENES_LIMIT)]
    promotion_candidate_count = 0
    if can_promote_writeback():
        from pallas.product.llm.promotion_candidates import count_pending_promotion_candidates

        promotion_candidate_count = count_pending_promotion_candidates(group_id=int(group_id))
    snapshot = FeedbackBiasSnapshot(
        count=len(rows),
        top_replies=top_replies,
        scenes=scenes,
        promotion_candidate_count=promotion_candidate_count,
    )
    return snapshot.model_dump(mode="json")


def should_append_feedback_for_task(task_type: str) -> bool:
    return can_collect_feedback() and is_feedback_task_type(task_type)


def promotion_allowed() -> bool:
    return can_promote_writeback()

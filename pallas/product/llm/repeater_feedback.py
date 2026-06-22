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

_BLOCKED_SOURCE_TAGS = {"memory", "relationship", "tool", "knowledge"}
_BLOCKED_REPLY_HINTS = (
    "因为",
    "通常",
    "一般来说",
    "总结一下",
    "首先",
)
_MAX_REPLY_LEN = 32
_TOP_REPLIES_LIMIT = 3
_TOP_SCENES_LIMIT = 5
_RECENT_WINDOW_MULTIPLIER = 4


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


def should_collect_llm_repeater_feedback(
    *,
    task_type: str,
    group_id: int | None,
    user_text: str,
    reply_text: str,
    source_tags: list[str],
) -> bool:
    if str(task_type).strip().lower() != "llm_chat":
        return False
    if int(group_id or 0) <= 0:
        return False
    if not str(user_text or "").strip():
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
    reply_counter = Counter(item.reply_text for item in rows if item.reply_text)
    scene_counter = Counter(item.behavior_scene for item in rows if item.behavior_scene)
    top_replies = [text for text, _ in reply_counter.most_common(_TOP_REPLIES_LIMIT)]
    scenes = [text for text, _ in scene_counter.most_common(_TOP_SCENES_LIMIT)]
    return {
        "count": len(rows),
        "top_replies": top_replies,
        "scenes": scenes,
    }

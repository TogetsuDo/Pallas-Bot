"""Promotion and feedback models for llm_chat -> repeater learning."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PromotionCandidate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")

    candidate_id: str
    group_id: int
    trigger_text: str
    reply_text: str
    support_count: int = Field(default=1, ge=1)
    last_seen_at: int = 0
    promoted: bool = False
    rejected_reason: str = ""
    behavior_scene: str = ""
    source_request_id: str = ""


class FeedbackBiasSnapshot(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")

    count: int = 0
    top_replies: list[str] = Field(default_factory=list)
    scenes: list[str] = Field(default_factory=list)
    promotion_candidate_count: int = 0

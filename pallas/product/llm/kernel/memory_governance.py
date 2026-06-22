"""Memory-learning asset taxonomy and governance gates."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from pallas.product.llm.config import LlmConfig, get_llm_config

from .feedback_models import FeedbackBiasSnapshot
from .models import ConversationFeatureLevel


class MemoryAssetKind(StrEnum):
    RUNTIME_STATE = "runtime_conversation_state"
    PERSISTENT_MEMORY = "persistent_memory"
    CORPUS_FOUNDATION = "corpus_foundation"
    BEHAVIORAL_LEARNING = "behavioral_learning"


class MemoryReadPolicy(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")

    allow_runtime_state: bool = True
    allow_persistent_memory: bool = True
    allow_corpus_foundation: bool = True
    allow_behavioral_learning: bool = False
    allow_writeback: bool = False


def resolve_conversation_feature_level(cfg: LlmConfig | None = None) -> ConversationFeatureLevel:
    c = cfg or get_llm_config()
    raw = str(getattr(c, "conversation_feature_level", "") or "").strip().lower()
    if raw == ConversationFeatureLevel.LEGACY_REPEATER:
        return ConversationFeatureLevel.LEGACY_REPEATER
    if raw == ConversationFeatureLevel.REPEATER_PLUS_DECISION:
        return ConversationFeatureLevel.REPEATER_PLUS_DECISION
    if raw == ConversationFeatureLevel.FULL_CONVERSATION_KERNEL:
        return ConversationFeatureLevel.FULL_CONVERSATION_KERNEL
    if not c.llm_chat_enabled:
        return ConversationFeatureLevel.LEGACY_REPEATER
    if c.llm_repeater_feedback_enabled or c.llm_repeater_bias_enabled or c.llm_repeater_writeback_enabled:
        return ConversationFeatureLevel.FULL_CONVERSATION_KERNEL
    if c.llm_select_enabled or c.llm_polish_enabled or c.llm_fallback_enabled:
        return ConversationFeatureLevel.REPEATER_PLUS_DECISION
    return ConversationFeatureLevel.LEGACY_REPEATER


def resolve_memory_read_policy(cfg: LlmConfig | None = None) -> MemoryReadPolicy:
    c = cfg or get_llm_config()
    feature_level = resolve_conversation_feature_level(c)
    allow_behavioral = bool(c.llm_repeater_bias_enabled) and feature_level != ConversationFeatureLevel.LEGACY_REPEATER
    return MemoryReadPolicy(
        allow_runtime_state=True,
        allow_persistent_memory=bool(c.llm_chat_enabled),
        allow_corpus_foundation=True,
        allow_behavioral_learning=allow_behavioral,
        allow_writeback=bool(c.llm_repeater_writeback_enabled),
    )


def can_collect_feedback(cfg: LlmConfig | None = None) -> bool:
    c = cfg or get_llm_config()
    return bool(c.llm_chat_enabled and c.llm_repeater_feedback_enabled)


def can_apply_feedback_bias(cfg: LlmConfig | None = None) -> bool:
    c = cfg or get_llm_config()
    policy = resolve_memory_read_policy(c)
    return bool(c.llm_chat_enabled and c.llm_repeater_bias_enabled and policy.allow_behavioral_learning)


def can_promote_writeback(cfg: LlmConfig | None = None) -> bool:
    c = cfg or get_llm_config()
    policy = resolve_memory_read_policy(c)
    return bool(c.llm_chat_enabled and c.llm_repeater_writeback_enabled and policy.allow_writeback)


def empty_bias_snapshot() -> FeedbackBiasSnapshot:
    return FeedbackBiasSnapshot()

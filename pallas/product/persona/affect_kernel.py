"""Shared persona-affect authority for repeater and llm_chat."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from pallas.product.llm.kernel.models import ConversationMode, DecisionConstraints

if TYPE_CHECKING:
    from pallas.product.persona.model import ResolvedPersona


class PersonaAffectContract(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")

    stance_hints: list[str] = Field(default_factory=list)
    disallowed_tones: list[str] = Field(default_factory=list)
    preferred_length_min: int = Field(default=1, ge=0)
    preferred_length_max: int = Field(default=36, ge=0)
    opener_suppression_hints: list[str] = Field(default_factory=list)
    ending_constraints: list[str] = Field(default_factory=list)
    mode_tolerance: float = Field(default=1.0, ge=0.0, le=2.0)


def build_persona_affect_contract(
    persona: ResolvedPersona | None = None,
    *,
    mode: ConversationMode = ConversationMode.NORMAL,
    group_flavor_summary: str = "",
    repeated_openers: list[str] | None = None,
) -> PersonaAffectContract:
    length_pref = str(getattr(persona, "length_pref", "") or "").strip().lower() if persona else ""
    if length_pref == "short":
        preferred_min, preferred_max = 1, 16
    elif length_pref == "long":
        preferred_min, preferred_max = 8, 64
    else:
        preferred_min, preferred_max = 1, 36

    if mode == ConversationMode.GHOST:
        preferred_max = min(preferred_max, 12)
    elif mode == ConversationMode.GOD:
        preferred_min = max(preferred_min, 2)
        preferred_max = min(preferred_max, 48)

    disallowed = ["客服腔", "教学腔", "总结腔"]
    stance_hints: list[str] = []
    if group_flavor_summary:
        stance_hints.append(group_flavor_summary)
    if persona is not None:
        warmth = float(getattr(persona, "warmth", 0.0) or 0.0)
        chaos = float(getattr(persona, "chaos_bias", 0.0) or 0.0)
        if warmth >= 0.1:
            stance_hints.append("语气可稍软，但别像哄人。")
        if chaos >= 0.5:
            stance_hints.append("可更跳脱，但别硬拗。")

    opener_hints = [item for item in list(repeated_openers or []) if item]
    ending_constraints = ["避免固定模板收口", "避免连续重复同一开头"]
    mode_tolerance = 1.0
    if mode == ConversationMode.GHOST:
        mode_tolerance = 0.85
    elif mode == ConversationMode.GOD:
        mode_tolerance = 1.1

    return PersonaAffectContract(
        stance_hints=stance_hints,
        disallowed_tones=disallowed,
        preferred_length_min=preferred_min,
        preferred_length_max=preferred_max,
        opener_suppression_hints=opener_hints,
        ending_constraints=ending_constraints,
        mode_tolerance=mode_tolerance,
    )


def affect_contract_to_constraints(contract: PersonaAffectContract) -> DecisionConstraints:
    return DecisionConstraints(
        max_length=contract.preferred_length_max,
        min_length=contract.preferred_length_min,
        disallow_drift=True,
        disallow_service_tone=True,
    )


def build_variation_hint_from_contract(contract: PersonaAffectContract) -> str:
    if not contract.opener_suppression_hints:
        return ""
    labels = "、".join(contract.opener_suppression_hints[:3])
    return f"【开头去重】最近别再用这些开头：{labels}。"

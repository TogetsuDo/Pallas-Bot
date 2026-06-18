from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from pallas.console.webui.field_meta import field_kind_from_annotation, field_meta_for_model_field, literal_choices


def test_literal_choices():
    assert literal_choices(Literal["auto", "session", "fleet"]) == ["auto", "session", "fleet"]


def test_field_kind_enum():
    assert field_kind_from_annotation(Literal["a", "b"]) == "enum"


class _M(BaseModel):
    mode: Literal["auto", "session"] = Field(default="auto", description="test")


def test_field_meta_includes_choices():
    f = _M.model_fields["mode"]
    row = field_meta_for_model_field(
        key="mode",
        field=f,
        env_key="MODE",
        cur="auto",
        default_value="auto",
    )
    assert row["kind"] == "enum"
    assert row["choices"] == ["auto", "session"]


def test_field_meta_normalizes_legacy_description():
    class _Legacy(BaseModel):
        x: int = Field(default=1, description="群内复读触发次数。")

    f = _Legacy.model_fields["x"]
    row = field_meta_for_model_field(
        key="x",
        field=f,
        env_key="X",
        cur=1,
        default_value=1,
    )
    assert row["description"].startswith("用途：")
    assert "填写：" in row["description"]


def test_field_meta_keeps_field_help_description():
    from pallas.console.webui.field_help import field_help

    class _Help(BaseModel):
        y: bool = Field(
            default=False,
            description=field_help("是否启用", "选 true 或 false"),
        )

    f = _Help.model_fields["y"]
    row = field_meta_for_model_field(
        key="y",
        field=f,
        env_key="Y",
        cur=False,
        default_value=False,
    )
    assert row["description"] == field_help("是否启用", "选 true 或 false")


def test_field_meta_includes_choice_labels_for_registered_enum():
    class _Mode(BaseModel):
        llm_repeater_mode: Literal["off", "select", "select_polish_lite"] = Field(default="select")

    f = _Mode.model_fields["llm_repeater_mode"]
    row = field_meta_for_model_field(
        key="llm_repeater_mode",
        field=f,
        env_key="LLM_REPEATER_MODE",
        cur="select",
        default_value="select",
    )
    assert row["choice_labels"]["select"] == "命中语料时 AI 选句（推荐）"
    assert row["choice_labels"]["off"] == "关闭 AI 接话"
    assert row["choice_labels"]["select_polish_lite"] == "选句为主，偶尔轻顺口气"

import pytest
from pydantic import BaseModel, Field, ValidationError

from pallas.console.webui.plugin_api import (
    format_validation_error,
    normalize_patch_value,
    plugin_field_env_key,
)


class SampleConfig(BaseModel):
    tags: list[int] = Field(default_factory=list)
    ratio: float = Field(default=1.0, ge=0.0)


def test_normalize_patch_null_list_uses_empty_list() -> None:
    field = SampleConfig.model_fields["tags"]
    assert normalize_patch_value(field, None) == []


def test_plugin_field_env_key_repeater_learn() -> None:
    assert plugin_field_env_key("repeater", "learn_concurrency") == "PALLAS_REPEATER_LEARN_CONCURRENCY"
    assert plugin_field_env_key("repeater", "answer_threshold") == "ANSWER_THRESHOLD"
    assert plugin_field_env_key("sing", "sing_enable") == "SING_ENABLE"


def test_format_validation_error_includes_field() -> None:
    with pytest.raises(ValidationError) as exc:
        SampleConfig(ratio=-1)

    msg = format_validation_error(exc.value)
    assert "ratio" in msg

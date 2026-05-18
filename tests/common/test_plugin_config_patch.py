from pydantic import BaseModel, Field

from src.common.webui.plugin_api import format_validation_error, normalize_patch_value


class SampleConfig(BaseModel):
    tags: list[int] = Field(default_factory=list)
    ratio: float = Field(default=1.0, ge=0.0)


def test_normalize_patch_null_list_uses_empty_list() -> None:
    field = SampleConfig.model_fields["tags"]
    assert normalize_patch_value(field, None) == []


def test_format_validation_error_includes_field() -> None:
    try:
        SampleConfig(ratio=-1)
    except Exception as e:
        from pydantic import ValidationError

        assert isinstance(e, ValidationError)
        msg = format_validation_error(e)
        assert "ratio" in msg

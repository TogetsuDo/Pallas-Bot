from src.plugins.maa.tasks import (
    COMMAND_TASK_MAP,
    MAA_CONTROL_COMMAND_HELPS,
    bind_device_id_error,
    format_maa_control_commands_help,
    maa_raw_task_validate,
    normalize_device_id,
    parse_bind_command_args,
    parse_command_line,
)


def test_help_commands_cover_map() -> None:
    phrases = {item.phrase for item in MAA_CONTROL_COMMAND_HELPS}
    assert phrases == set(COMMAND_TASK_MAP.keys())


def test_format_maa_control_help_lists_commands() -> None:
    text = format_maa_control_commands_help()
    assert "牛牛长草" in text
    assert "牛牛设置关卡" in text
    assert "牛牛基建" in text
    assert "牛牛一键长草" not in text


def test_normalize_device_hex32() -> None:
    assert normalize_device_id("42cfa6e9dfa147d8a7c1d9a6d658b06d") == "42cfa6e9dfa147d8a7c1d9a6d658b06d"


def test_bind_rejects_qq_as_device() -> None:
    assert bind_device_id_error("3023094357", "3023094357") is not None


def test_parse_bind_with_alias() -> None:
    device, alias = parse_bind_command_args("42cfa6e9dfa147d8a7c1d9a6d658b06d 家里电脑")
    assert device == "42cfa6e9dfa147d8a7c1d9a6d658b06d"
    assert alias == "家里电脑"


def test_parse_link_start() -> None:
    spec = parse_command_line("牛牛长草")
    assert spec is not None
    assert spec.task_type == "LinkStart"


def test_parse_settings() -> None:
    spec = parse_command_line("牛牛设置连接 127.0.0.1:5555")
    assert spec is not None
    assert spec.task_type == "Settings-ConnectionAddress"
    assert spec.params == "127.0.0.1:5555"


def test_maa_raw_task_stage() -> None:
    spec, err = maa_raw_task_validate("牛牛MAA任务 Settings-Stage1 1-7")
    assert err is None
    assert spec is not None
    assert spec.task_type == "Settings-Stage1"
    assert spec.params == "1-7"


def test_maa_raw_task_requires_params() -> None:
    _, err = maa_raw_task_validate("牛牛MAA任务 Settings-Stage1")
    assert err is not None


def test_maa_raw_task_rejects_extra_params() -> None:
    _, err = maa_raw_task_validate("牛牛MAA任务 LinkStart-Recruiting extra")
    assert err is not None

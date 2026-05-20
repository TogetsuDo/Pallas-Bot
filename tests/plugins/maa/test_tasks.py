from src.plugins.maa.tasks import (
    COMMAND_TASK_MAP,
    MAA_CONTROL_COMMAND_HELPS,
    SETTINGS_TYPES,
    TASK_TYPES_WITHOUT_AUTO_SCREENSHOT,
    MaaTaskSpec,
    bind_device_id_error,
    expand_command_specs,
    format_maa_control_commands_help,
    maa_raw_task_validate,
    normalize_device_id,
    parse_bind_command_args,
    parse_command_line,
    parse_command_specs,
    parse_stage_setting_values,
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


def test_normalize_device_uuid_to_hex32() -> None:
    assert (
        normalize_device_id("42cfa6e9-dfa1-47d8-a7c1-d9a6d658b06d")
        == "42cfa6e9dfa147d8a7c1d9a6d658b06d"
    )


def test_bind_rejects_qq_as_device() -> None:
    assert bind_device_id_error("3023094357", "3023094357") is not None


def test_parse_bind_with_alias() -> None:
    device, alias = parse_bind_command_args("42cfa6e9dfa147d8a7c1d9a6d658b06d 家里电脑")
    assert device == "42cfa6e9dfa147d8a7c1d9a6d658b06d"
    assert alias == "家里电脑"


def test_parse_bind_strips_leading_device_word() -> None:
    device, alias = parse_bind_command_args("设备 6b46c8ff9c73448e8ba32fa2b82769c5 mumu")
    assert device == "6b46c8ff9c73448e8ba32fa2b82769c5"
    assert alias == "mumu"
    assert bind_device_id_error(device, "123") is None


def test_parse_link_start() -> None:
    spec = parse_command_line("牛牛长草")
    assert spec is not None
    assert spec.task_type == "LinkStart"


def test_parse_settings() -> None:
    spec = parse_command_line("牛牛设置连接 127.0.0.1:5555")
    assert spec is not None
    assert spec.task_type == "Settings-ConnectionAddress"
    assert spec.params == "127.0.0.1:5555"


def test_parse_stage_candidates() -> None:
    stages = parse_stage_setting_values("12-17-HARD CE-6 -")
    assert stages == ["12-17-HARD", "CE-6", ""]
    specs = parse_command_specs("牛牛设置关卡 12-17-HARD,CE-6")
    assert specs is not None
    assert len(specs) == 1
    assert specs[0].task_type == "Settings-Stage1"
    assert specs[0].params == "12-17-HARD"


def test_settings_types_skip_auto_screenshot() -> None:
    assert SETTINGS_TYPES <= TASK_TYPES_WITHOUT_AUTO_SCREENSHOT


def test_rename_award_command() -> None:
    assert "牛牛领取奖励" in COMMAND_TASK_MAP
    assert COMMAND_TASK_MAP["牛牛领取奖励"] == "LinkStart-Mission"
    assert "牛牛任务" not in COMMAND_TASK_MAP


def test_combat_command_maps_to_link_start() -> None:
    spec = parse_command_line("牛牛作战")
    assert spec is not None
    assert spec.task_type == "LinkStart"


def test_combat_auto_prepare_for_combat_phrase() -> None:
    specs = expand_command_specs(
        [MaaTaskSpec("LinkStart")],
        stage_plan=["1-7", "CE-6"],
        combat_auto_prepare=True,
        command_line="牛牛作战",
    )
    assert specs[0].task_type == "Settings-Stage1"
    assert specs[0].params == "1-7"
    assert specs[-1].task_type == "LinkStart"


def test_combat_auto_prepare_for_link_start_combat() -> None:
    specs = expand_command_specs(
        [MaaTaskSpec("LinkStart-Combat")],
        stage_plan=["1-7", "CE-6"],
        combat_auto_prepare=True,
    )
    assert specs[0].task_type == "Settings-Stage1"
    assert specs[-1].task_type == "LinkStart-Combat"


def test_combat_auto_prepare_skips_duplicate_stage() -> None:
    specs = expand_command_specs(
        [MaaTaskSpec("Settings-Stage1", "CE-6"), MaaTaskSpec("LinkStart-Combat")],
        stage_plan=["1-7"],
        combat_auto_prepare=True,
    )
    assert len(specs) == 2
    assert specs[0].params == "CE-6"


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

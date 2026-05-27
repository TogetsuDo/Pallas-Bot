from src.plugins.maa.tasks import (
    MAA_RAW_TASK_PREFIX,
    canonical_remote_task_type,
    is_control_phrase_line,
    parse_command_specs,
    parse_maa_raw_task,
    task_type_for_control_phrase,
)


def test_control_phrase_case_insensitive() -> None:
    assert task_type_for_control_phrase("牛牛长草") == "LinkStart"
    assert is_control_phrase_line("牛牛作战")
    assert task_type_for_control_phrase("牛牛作战") == "LinkStart"


def test_maa_status_command_prefix() -> None:
    from src.foundation.command_prefix import extract_command_tail_any, matches_command_prefix
    from src.plugins.maa.command_match import STATUS_COMMAND

    assert matches_command_prefix("牛牛maa状态", STATUS_COMMAND)
    assert extract_command_tail_any("牛牛maa状态", STATUS_COMMAND) == ""


def test_settings_prefix_case_insensitive() -> None:
    specs = parse_command_specs("牛牛设置连接 127.0.0.1:5555")
    assert specs and specs[0].task_type == "Settings-ConnectionAddress"
    specs2 = parse_command_specs("牛牛设置关卡 1-7")
    assert specs2 and specs2[0].task_type == "Settings-Stage1"


def test_raw_task_type_case_insensitive() -> None:
    assert canonical_remote_task_type("linkstart-combat") == "LinkStart-Combat"
    spec = parse_maa_raw_task(f"{MAA_RAW_TASK_PREFIX} linkstart-recruiting")
    assert spec is not None
    assert spec.task_type == "LinkStart-Recruiting"

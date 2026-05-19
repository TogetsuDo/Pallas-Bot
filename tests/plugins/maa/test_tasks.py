from src.plugins.maa.tasks import bind_device_id_error, normalize_device_id, parse_command_line


def test_normalize_device_hex32() -> None:
    assert normalize_device_id("42cfa6e9dfa147d8a7c1d9a6d658b06d") == "42cfa6e9dfa147d8a7c1d9a6d658b06d"


def test_bind_rejects_qq_as_device() -> None:
    assert bind_device_id_error("3023094357", "3023094357") is not None


def test_parse_link_start() -> None:
    spec = parse_command_line("牛牛长草")
    assert spec is not None
    assert spec.task_type == "LinkStart"


def test_parse_settings() -> None:
    spec = parse_command_line("牛牛设置连接 127.0.0.1:5555")
    assert spec is not None
    assert spec.task_type == "Settings-ConnectionAddress"
    assert spec.params == "127.0.0.1:5555"

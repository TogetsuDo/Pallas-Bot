from src.common.service_probe import ServiceProbeResult, format_probe_line, format_probe_text


def test_format_probe_line() -> None:
    ok = ServiceProbeResult("测试", "节点", True, 88, 200, None)
    assert format_probe_line(ok) == "测试：节点：88ms"
    err = ServiceProbeResult("测试", "节点", False, None, None, "超时")
    assert format_probe_line(err) == "测试：节点：超时"

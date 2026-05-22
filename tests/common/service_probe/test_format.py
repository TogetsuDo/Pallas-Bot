from src.common.service_probe import ServiceProbeResult, format_probe_line, format_probe_lines, format_probe_text


def test_format_probe_line() -> None:
    ok = ServiceProbeResult("测试", "节点", True, 88, 200, None)
    assert format_probe_line(ok) == "【测试】\n· 节点：88ms"
    noted = ServiceProbeResult("测试", "节点", True, 5, 200, "附带说明")
    assert format_probe_line(noted) == "【测试】\n· 节点：5ms（附带说明）"
    err = ServiceProbeResult("测试", "节点", False, None, None, "超时")
    assert format_probe_line(err) == "【测试】\n· 节点：超时"


def test_format_probe_line_site_only() -> None:
    r = ServiceProbeResult("牛牛画画", "备线1", True, 10, 200, None)
    assert format_probe_line(r, show_category=False) == "· 备线1：10ms"


def test_format_probe_lines_groups_same_category() -> None:
    results = [
        ServiceProbeResult("牛牛画画", "主网关", True, 88, 200, None),
        ServiceProbeResult("牛牛画画", "备线1", False, None, None, "超时"),
        ServiceProbeResult("MAA远控", "获取任务", True, 5, 200, None),
        ServiceProbeResult("MAA远控", "汇报任务", True, 4, 200, None),
    ]
    assert format_probe_lines(results) == [
        "【牛牛画画】",
        "· 主网关：88ms",
        "· 备线1：超时",
        "",
        "【MAA远控】",
        "· 获取任务：5ms",
        "· 汇报任务：4ms",
    ]


def test_format_probe_text_joins_lines() -> None:
    results = [ServiceProbeResult("唱歌", "服务", False, None, None, "未启用 sing_enable")]
    assert format_probe_text(results) == "【唱歌】\n· 服务：未启用 sing_enable"


def test_format_probe_text_example_layout() -> None:
    results = [
        ServiceProbeResult("牛牛画画", "主网关", True, 403, 200, None),
        ServiceProbeResult("牛牛画画", "备线1", True, 185, 200, None),
        ServiceProbeResult("牛牛画画", "备线2", True, 1761, 200, None),
        ServiceProbeResult("牛牛画画", "备线3", True, 697, 200, None),
        ServiceProbeResult("MAA远控", "获取任务", True, 110, 200, None),
        ServiceProbeResult("MAA远控", "汇报任务", True, 114, 200, None),
        ServiceProbeResult("唱歌", "健康检查", True, 6, 200, None),
    ]
    text = format_probe_text(results)
    assert text.startswith("【牛牛画画】\n· 主网关：403ms")
    assert "【MAA远控】" in text
    assert text.endswith("· 健康检查：6ms")

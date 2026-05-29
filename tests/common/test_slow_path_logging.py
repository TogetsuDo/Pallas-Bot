from __future__ import annotations

from src.platform.observability import slow_path


def test_slow_path_logs_stages_when_threshold_exceeded(monkeypatch) -> None:
    calls: list[tuple[str, tuple[object, ...]]] = []
    monkeypatch.setattr(slow_path.logger, "warning", lambda msg, *args: calls.append((msg, args)))

    timer = slow_path.SlowPathTimer("ingress_gate", threshold_ms=10.0)
    timer._started = 1.0
    timer._last_mark = 1.0
    timer.mark("dedup", now=1.008)
    timer.mark("federate", now=1.017)
    timer.finish(outcome="pass", now=1.024, group_id=12345)

    assert len(calls) == 1
    msg, args = calls[0]
    assert "slow_path" in msg
    assert args[0] == "ingress_gate"
    assert args[2] == "dedup=8.0ms,federate=9.0ms"
    assert args[3] == "group_id=12345 outcome=pass"


def test_slow_path_skips_log_below_threshold(monkeypatch) -> None:
    calls: list[tuple[str, tuple[object, ...]]] = []
    monkeypatch.setattr(slow_path.logger, "warning", lambda msg, *args: calls.append((msg, args)))

    timer = slow_path.SlowPathTimer("federate_ingress", threshold_ms=50.0)
    timer._started = 1.0
    timer.mark("redis", now=1.015)
    timer.finish(outcome="pass", now=1.030, cache_hit=True)

    assert calls == []

from __future__ import annotations

import src.foundation.db.pool_diagnostics as pool_diagnostics


def test_pg_session_caller_hint_entry_avoids_inspect_stack(monkeypatch) -> None:
    def _boom():
        raise AssertionError("inspect.stack should not be used on the fast path")

    monkeypatch.setattr(pool_diagnostics.inspect, "stack", _boom)

    def wrapper() -> str:
        return pool_diagnostics.pg_session_caller_hint_entry()

    hint = wrapper()

    assert hint.startswith("wrapper@common/test_pool_diagnostics.py:")


def test_pg_session_caller_hint_entry_falls_back_to_inspect_stack(monkeypatch) -> None:
    monkeypatch.setattr(pool_diagnostics.sys, "_getframe", None, raising=False)

    class _FrameInfo:
        filename = "/tmp/site-packages/pkg.py"
        function = "ignored"
        lineno = 1

    class _WantedFrame:
        filename = "/root/Projects/Bots/Pallas-Bot/tests/common/test_pool_diagnostics.py"
        function = "fallback_wrapper"
        lineno = 27

    monkeypatch.setattr(pool_diagnostics.inspect, "stack", lambda: [None, None, _FrameInfo(), _WantedFrame()])

    assert pool_diagnostics.pg_session_caller_hint_entry() == "fallback_wrapper@common/test_pool_diagnostics.py:27"

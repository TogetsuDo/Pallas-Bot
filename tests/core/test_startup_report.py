from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING
from unittest.mock import patch

if TYPE_CHECKING:
    import pytest


def test_emit_startup_summary_logs_runtime_and_facts(monkeypatch: pytest.MonkeyPatch) -> None:
    import pallas.core.foundation.startup_report as startup_report

    startup_report.reset_startup_report_for_tests()
    monkeypatch.setenv("DB_BACKEND", "sqlite")
    monkeypatch.setattr(
        startup_report,
        "get_driver",
        lambda: SimpleNamespace(config=SimpleNamespace(host="127.0.0.1", port=8088)),
    )
    monkeypatch.setattr(
        "pallas.core.foundation.bot_version.get_pallas_bot_version_for_reporting",
        lambda: "v4.0.0",
    )
    monkeypatch.setattr("pallas.core.platform.bot_runtime.roles.bot_role", lambda: "hub")
    monkeypatch.setattr("pallas.core.platform.bot_runtime.roles.is_sharded_worker", lambda: False)

    startup_report.register_startup_fact("plugins", "local=1 src=10 pip=0 extra=1")
    startup_report.register_startup_fact("llm", "ok v=4.0.0 switches=LLM_CHAT")
    startup_report.emit_startup_summary()

    with patch.object(startup_report.logger, "info") as mock_info:
        startup_report.emit_startup_summary()
        mock_info.assert_not_called()

    snapshot = startup_report.startup_report_snapshot()
    assert snapshot["emitted"] is True
    assert snapshot["facts"]["plugins"] == "local=1 src=10 pip=0 extra=1"

    startup_report.reset_startup_report_for_tests()
    with patch.object(startup_report.logger, "info") as mock_info:
        startup_report.register_startup_fact("plugins", "local=1 src=10 pip=0 extra=1")
        startup_report.emit_startup_summary()
        mock_info.assert_called_once()
        text = mock_info.call_args.args[1]
        assert "v=v4.0.0" in text
        assert "role=hub" in text
        assert "listen=127.0.0.1:8088" in text
        assert "db=sqlite" in text
        assert "plugins=local=1 src=10 pip=0 extra=1" in text


def test_emit_startup_summary_logs_warning_block(monkeypatch: pytest.MonkeyPatch) -> None:
    import pallas.core.foundation.startup_report as startup_report

    startup_report.reset_startup_report_for_tests()
    monkeypatch.delenv("DB_BACKEND", raising=False)
    monkeypatch.setattr(
        startup_report,
        "get_driver",
        lambda: SimpleNamespace(config=SimpleNamespace(host=None, port=8090)),
    )
    monkeypatch.setattr(
        "pallas.core.foundation.bot_version.get_pallas_bot_version_for_reporting",
        lambda: "v4.0.1",
    )
    monkeypatch.setattr("pallas.core.platform.bot_runtime.roles.bot_role", lambda: "worker")
    monkeypatch.setattr("pallas.core.platform.bot_runtime.roles.is_sharded_worker", lambda: True)
    monkeypatch.setenv("PALLAS_SHARD_ID", "3")

    with patch.object(startup_report.logger, "info") as mock_info, patch.object(
        startup_report.logger,
        "warning",
    ) as mock_warning:
        startup_report.register_startup_fact("console", "http://127.0.0.1:8090/pallas/")
        startup_report.register_startup_warning("llm", "unreachable err=refused")
        startup_report.emit_startup_summary()

        mock_info.assert_called_once()
        info_text = mock_info.call_args.args[1]
        assert "role=worker" in info_text
        assert "shard=3" in info_text
        assert "listen=0.0.0.0:8090" in info_text
        assert "console=http://127.0.0.1:8090/pallas/" in info_text

        mock_warning.assert_called_once()
        assert "llm=unreachable err=refused" in mock_warning.call_args.args[1]

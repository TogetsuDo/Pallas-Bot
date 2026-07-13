"""AI Runtime 安装状态与受控 clone 路径。"""

from __future__ import annotations

import pytest

from pallas.console.cli import ai_install


def test_ai_install_status_shape(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("PALLAS_AI_ROOT", str(tmp_path / "missing"))
    monkeypatch.setattr(ai_install, "resolve_ai_repo_root", lambda: None)
    st = ai_install.ai_install_status()
    assert st["detected"] is False
    assert st["git_url"].endswith("Pallas-Bot-AI.git")
    assert "docker" in st["docker_hint"].lower()
    assert st["clone_target"] == str((tmp_path / "missing").resolve())


def test_clone_ai_repo_rejects_foreign_path(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    allowed = tmp_path / "Pallas-Bot-AI"
    monkeypatch.setattr(ai_install, "default_ai_clone_target", lambda: allowed.resolve())
    with pytest.raises(ValueError, match="受控路径"):
        ai_install.clone_ai_repo(target=tmp_path / "other")


def test_clone_ai_repo_rejects_existing(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    allowed = tmp_path / "Pallas-Bot-AI"
    allowed.mkdir()
    (allowed / "scripts").mkdir()
    (allowed / "scripts" / "ai_bootstrap.sh").write_text("#!/bin/sh\n", encoding="utf-8")
    monkeypatch.setattr(ai_install, "default_ai_clone_target", lambda: allowed.resolve())
    with pytest.raises(FileExistsError):
        ai_install.clone_ai_repo()

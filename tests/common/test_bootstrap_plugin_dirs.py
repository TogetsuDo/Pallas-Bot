from __future__ import annotations

from src.common.config.repo_settings import read_bootstrap_extra_plugin_dirs


def test_read_bootstrap_extra_plugin_dirs_empty_when_missing(tmp_path, monkeypatch) -> None:
    root = tmp_path / "repo"
    (root / "config").mkdir(parents=True)
    monkeypatch.setattr("src.common.config.repo_settings._REPO_ROOT", root)
    assert read_bootstrap_extra_plugin_dirs() == []


def test_read_bootstrap_extra_plugin_dirs_from_toml(tmp_path, monkeypatch) -> None:
    root = tmp_path / "repo"
    cfg = root / "config" / "pallas.toml"
    cfg.parent.mkdir(parents=True)
    cfg.write_text(
        """
[bootstrap]
extra_plugin_dirs = ["local/plugins", "./local/plugins", "plugins/custom"]
""",
        encoding="utf-8",
    )
    monkeypatch.setattr("src.common.config.repo_settings._REPO_ROOT", root)
    assert read_bootstrap_extra_plugin_dirs() == ["local/plugins", "plugins/custom"]

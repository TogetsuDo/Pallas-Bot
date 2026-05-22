from __future__ import annotations

from src.common.db import backup as mod


def test_resolve_backup_parent_default(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(mod, "PROJECT_ROOT", tmp_path)
    parent = mod.resolve_backup_parent(None)
    assert parent == (tmp_path / "backups").resolve()
    assert parent.is_dir()


def test_resolve_backup_parent_relative(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(mod, "PROJECT_ROOT", tmp_path)
    parent = mod.resolve_backup_parent("custom/backups")
    assert parent == (tmp_path / "custom" / "backups").resolve()


def test_make_backup_run_dir(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(mod, "PROJECT_ROOT", tmp_path)
    parent = mod.resolve_backup_parent(None)
    run = mod.make_backup_run_dir(parent, "postgres", label="test")
    assert run.is_dir()
    assert run.name.startswith("postgres_")
    assert "test" in run.name


def test_missing_tool_message_includes_url() -> None:
    msg = mod.missing_tool_message("mongodump")
    assert "mongodump" in msg
    assert "mongodb.com" in msg


def test_tool_download_meta_for_mongodump() -> None:
    meta = mod._TOOL_DOWNLOAD["mongodump"]
    assert meta["url"].startswith("https://")
    assert meta["label"]

"""社区插件索引与商店。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pallas.console.webui.community_plugin_assets import (
    infer_community_plugin_icon,
    resolve_community_plugin_icon,
)
from pallas.console.webui.community_plugin_author import (
    build_index_entry,
    validate_community_plugin_dir,
)
from pallas.console.webui.community_plugin_index import (
    normalize_index_entry,
    parse_index_document,
)
from pallas.console.webui.community_plugin_registry import (
    build_community_plugin_row,
    resolve_community_plugin_avatar,
)


def test_normalize_index_entry() -> None:
    entry = normalize_index_entry(
        {
            "id": "arcana",
            "name": "Arcana",
            "repository": "https://github.com/foo/bar.git",
            "ref": "dev",
            "tags": ["game", ""],
            "icon": "https://example.com/icon.svg",
            "cover": "https://example.com/cover.png",
            "avatar": "https://example.com/avatar.png",
        }
    )
    assert entry is not None
    assert entry["plugin_id"] == "arcana"
    assert entry["repository_url"].endswith(".git")
    assert entry["ref"] == "dev"
    assert entry["tags"] == ["game"]
    assert entry["icon"] == "https://example.com/icon.svg"
    assert entry["cover"] == "https://example.com/cover.png"
    assert entry["avatar"] == "https://example.com/avatar.png"


def test_resolve_community_plugin_avatar_explicit() -> None:
    url = resolve_community_plugin_avatar({"avatar": "https://example.com/avatar.jpg"})
    assert url == "https://example.com/avatar.jpg"


def test_parse_index_document_rejects_invalid() -> None:
    with pytest.raises(Exception, match="plugins"):
        parse_index_document({"version": 1})


def test_resolve_community_plugin_avatar_from_author() -> None:
    url = resolve_community_plugin_avatar({"author": "TogetsuDo"})
    assert url == "https://avatars.githubusercontent.com/TogetsuDo?s=64"


def test_resolve_community_plugin_avatar_from_repository() -> None:
    url = resolve_community_plugin_avatar({
        "repository_url": "https://github.com/TogetsuDo/pallas-community-plugin-niuniu-interact.git",
    })
    assert url == "https://avatars.githubusercontent.com/TogetsuDo?s=64"


def test_build_community_plugin_row_not_installed(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        "pallas.console.webui.community_plugin_install.community_plugins_root",
        lambda: tmp_path / "local" / "plugins",
    )
    monkeypatch.setattr(
        "pallas.console.webui.community_plugin_registry.loaded_extra_plugin_ids",
        lambda _ids: [],
    )
    row = build_community_plugin_row(
        {
            "plugin_id": "demo",
            "name": "Demo",
            "description": "d",
            "repository_url": "https://github.com/a/b.git",
            "ref": "main",
        }
    )
    assert row["status"] == "available"
    assert row["can_install"] is True
    assert row["avatar"] == "https://avatars.githubusercontent.com/a?s=64"


def test_build_community_plugin_row_installed(tmp_path, monkeypatch) -> None:
    root = tmp_path / "local" / "plugins" / "demo"
    root.mkdir(parents=True)
    (root / "__init__.py").write_text("# demo\n", encoding="utf-8")
    monkeypatch.setattr(
        "pallas.console.webui.community_plugin_install.community_plugins_root",
        lambda: tmp_path / "local" / "plugins",
    )
    monkeypatch.setattr(
        "pallas.console.webui.community_plugin_registry.loaded_extra_plugin_ids",
        lambda ids: list(ids),
    )
    row = build_community_plugin_row(
        {
            "plugin_id": "demo",
            "name": "Demo",
            "description": "",
            "repository_url": "https://github.com/a/b.git",
            "ref": "main",
        }
    )
    assert row["status"] == "loaded"
    assert row["can_uninstall"] is True


def test_bundled_index_file_valid() -> None:
    path = Path(__file__).resolve().parents[2] / "config" / "community_plugin_index.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    meta, plugins = parse_index_document(raw)
    assert meta.get("version") == 1
    assert isinstance(plugins, list)


def test_infer_community_plugin_icon_github() -> None:
    url = infer_community_plugin_icon(
        "https://github.com/foo/my_plugin.git",
        "main",
    )
    assert url == "https://raw.githubusercontent.com/foo/my_plugin/main/assets/icon.png"


def test_resolve_community_plugin_icon_infers_when_missing() -> None:
    icon = resolve_community_plugin_icon(
        {"repository_url": "https://github.com/foo/bar.git", "ref": "dev"},
    )
    assert icon == "https://raw.githubusercontent.com/foo/bar/dev/assets/icon.png"


def test_build_community_plugin_row_infers_icon(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        "pallas.console.webui.community_plugin_install.community_plugins_root",
        lambda: tmp_path / "local" / "plugins",
    )
    monkeypatch.setattr(
        "pallas.console.webui.community_plugin_registry.loaded_extra_plugin_ids",
        lambda _ids: [],
    )
    row = build_community_plugin_row(
        {
            "plugin_id": "demo",
            "name": "Demo",
            "description": "d",
            "repository_url": "https://github.com/a/b.git",
            "ref": "main",
        }
    )
    assert row["icon"] == "https://raw.githubusercontent.com/a/b/main/assets/icon.png"


def test_validate_community_plugin_dir_ok(tmp_path: Path) -> None:
    plugin = tmp_path / "my_plugin"
    plugin.mkdir()
    (plugin / "__init__.py").write_text(
        'PLUGIN_ID = "my_plugin"\n__plugin_meta__ = None\n',
        encoding="utf-8",
    )
    (plugin / "assets").mkdir()
    (plugin / "assets" / "icon.png").write_bytes(b"x")
    (plugin / "README.md").write_text("# demo\n", encoding="utf-8")
    errors, warnings = validate_community_plugin_dir(plugin)
    assert errors == []
    assert warnings == []


def test_build_index_entry_auto_icon() -> None:
    entry = build_index_entry(
        plugin_id="demo",
        name="Demo",
        description="test",
        repository="https://github.com/foo/demo.git",
    )
    assert entry["icon"].endswith("/assets/icon.png")


def test_build_community_plugin_row_local_only(tmp_path, monkeypatch) -> None:
    root = tmp_path / "local" / "plugins" / "side_plugin"
    root.mkdir(parents=True)
    (root / "__init__.py").write_text("# side\n", encoding="utf-8")
    monkeypatch.setattr(
        "pallas.console.webui.community_plugin_install.community_plugins_root",
        lambda: tmp_path / "local" / "plugins",
    )
    monkeypatch.setattr(
        "pallas.console.webui.community_plugin_registry.loaded_extra_plugin_ids",
        lambda ids: list(ids),
    )
    row = build_community_plugin_row(
        {
            "plugin_id": "side_plugin",
            "name": "side_plugin",
            "description": "本地安装（未收录于社区索引）",
            "local_only": True,
        },
    )
    assert row["local_only"] is True
    assert row["can_install"] is False
    assert row["can_uninstall"] is True
    assert row["status"] == "loaded"

from __future__ import annotations

from pallas.console.webui.community_plugin_registry import build_community_plugin_store


async def test_build_community_plugin_store_skips_local_only_plugins(monkeypatch) -> None:
    async def fake_index():
        return {
            "plugins": [
                {
                    "plugin_id": "demo",
                    "name": "Demo",
                    "repository_url": "https://github.com/acme/demo",
                }
            ],
            "meta": {},
        }

    monkeypatch.setattr(
        "pallas.console.webui.community_plugin_registry.load_community_plugin_index_safe",
        fake_index,
    )
    monkeypatch.setattr(
        "pallas.console.webui.community_plugin_registry.local_plugin_installed",
        lambda plugin_id: plugin_id == "demo",
    )
    monkeypatch.setattr(
        "pallas.console.webui.community_plugin_registry.loaded_extra_plugin_ids",
        lambda plugin_ids: [],
    )
    monkeypatch.setattr(
        "pallas.console.webui.community_plugin_registry.webui_community_install_enabled",
        lambda: True,
    )
    monkeypatch.setattr(
        "pallas.console.webui.community_plugin_registry.bot_lifecycle_available",
        lambda: True,
    )
    monkeypatch.setattr(
        "pallas.console.webui.community_plugin_registry.extra_plugin_dirs_ready",
        lambda: True,
    )
    monkeypatch.setattr(
        "pallas.console.webui.community_plugin_registry.resolve_community_plugin_icon",
        lambda entry: None,
    )
    monkeypatch.setattr(
        "pallas.console.webui.community_plugin_registry.list_local_community_plugin_ids",
        lambda: ["demo", "local_only_plugin"],
    )

    store = await build_community_plugin_store()

    assert [row["plugin_id"] for row in store["plugins"]] == ["demo"]

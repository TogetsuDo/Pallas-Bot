from __future__ import annotations

from pallas.core.platform.bot_runtime import plugin_loader


def test_load_discovered_plugin_modules_applies_skip_rules(monkeypatch):
    calls: list[tuple[str, str, set[str]]] = []

    def fake_load(module_path: str, *, role_label: str, loaded_short: set[str]) -> bool:
        calls.append((module_path, role_label, set(loaded_short)))
        loaded_short.add(module_path.rsplit(".", 1)[-1])
        return True

    monkeypatch.setattr(plugin_loader, "_load_plugin_module", fake_load)

    loaded_short = {"already"}
    count = plugin_loader._load_discovered_plugin_modules(
        role_label="worker",
        module_paths=[
            "packages.skip_by_path",
            "packages.keep",
            "packages.skip_me",
            "packages.already",
        ],
        skip_short=frozenset({"skip_me"}),
        skip_module_paths=frozenset({"packages.skip_by_path"}),
        loaded_short=loaded_short,
    )

    assert count == 1
    assert calls == [("packages.keep", "worker", {"already"})]
    assert loaded_short == {"already", "keep"}


def test_load_discovered_plugin_modules_skips_canonical_alias(monkeypatch):
    calls: list[str] = []

    def fake_load(module_path: str, *, role_label: str, loaded_short: set[str]) -> bool:
        calls.append(module_path)
        loaded_short.add(plugin_loader._load_slot_key(module_path))
        return True

    monkeypatch.setattr(plugin_loader, "_load_plugin_module", fake_load)

    loaded_short = {"draw"}
    count = plugin_loader._load_discovered_plugin_modules(
        role_label="worker",
        module_paths=["pallas_plugin_draw"],
        skip_short=frozenset(),
        loaded_short=loaded_short,
    )

    assert count == 0
    assert calls == []
    assert loaded_short == {"draw"}


def test_load_discovered_plugin_modules_skips_src_bundled_when_pip_alias_loaded(monkeypatch):
    calls: list[str] = []

    def fake_load(module_path: str, *, role_label: str, loaded_short: set[str]) -> bool:
        calls.append(module_path)
        loaded_short.add(plugin_loader._load_slot_key(module_path))
        return True

    monkeypatch.setattr(plugin_loader, "_load_plugin_module", fake_load)

    loaded_short = {"duel"}
    count = plugin_loader._load_discovered_plugin_modules(
        role_label="worker",
        module_paths=["packages.duel"],
        skip_short=frozenset(),
        loaded_short=loaded_short,
    )

    assert count == 0
    assert calls == []
    assert loaded_short == {"duel"}

from __future__ import annotations

import nonebot
import pytest

from pallas.core.platform.bot_runtime.plugin_loader import (
    _discover_plugin_modules,
    _short_name,
    load_plugins_for_role,
)
from pallas.core.platform.bot_runtime.roles import UNIFIED_SKIP_PLUGIN_NAMES
from pallas.core.platform.shard.registry.config import get_shard_registry_settings


@pytest.fixture(autouse=True)
def clear_shard_settings_cache():
    get_shard_registry_settings.cache_clear()
    yield
    get_shard_registry_settings.cache_clear()


def test_unified_skip_plugin_names():
    assert UNIFIED_SKIP_PLUGIN_NAMES == frozenset({
        "relogin_forward",
        "maa_hub",
    })


def test_discover_plugin_modules_excludes_underscore_packages():
    names = {_short_name(m) for m in _discover_plugin_modules(load_bundled_extra=True)}
    assert "ingress_gate" not in names
    assert "relogin_forward" in names
    assert "maa_hub" in names


def test_discover_plugin_modules_slim_skips_extra():
    names = {_short_name(m) for m in _discover_plugin_modules(load_bundled_extra=False)}
    assert "repeater" in names
    assert "help" in names
    assert "duel" not in names
    assert "draw" not in names
    assert "maa" not in names
    assert "pb_protocol" not in names


def test_discover_plugin_modules_auto_includes_extra_without_pip(monkeypatch):
    monkeypatch.setattr(
        "pallas.core.platform.bot_runtime.plugin_matrix.pip_extra_installed_for_plugin",
        lambda _name: False,
    )
    names = {_short_name(m) for m in _discover_plugin_modules(load_bundled_extra="auto")}
    assert "duel" in names
    assert "draw" not in names  # pip 扩展，不在 packages/


def test_discover_plugin_modules_auto_skips_extra_when_pip_installed(monkeypatch):
    monkeypatch.setattr(
        "pallas.core.platform.bot_runtime.plugin_matrix.pip_extra_installed_for_plugin",
        lambda name: name == "duel",
    )
    names = {_short_name(m) for m in _discover_plugin_modules(load_bundled_extra="auto")}
    assert "duel" not in names


def test_unified_role_skips_shard_only_plugins(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("PALLAS_SHARD_ENABLED", raising=False)
    monkeypatch.delenv("PALLAS_BOT_ROLE", raising=False)
    monkeypatch.setenv("PALLAS_LOAD_BUNDLED_EXTRA", "1")
    get_shard_registry_settings.cache_clear()

    nonebot.init()
    load_plugins_for_role()

    loaded = {p.name for p in nonebot.get_loaded_plugins()}
    assert "relogin_forward" not in loaded
    assert "maa_hub" not in loaded
    assert "relogin_bot" in loaded
    assert "maa" in loaded
    assert "ingress_gate" not in loaded


def test_unified_role_slim_skips_bundled_extra(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("PALLAS_LOAD_BUNDLED_EXTRA", raising=False)
    names = {_short_name(m) for m in _discover_plugin_modules(load_bundled_extra=False)}
    assert "repeater" in names
    assert "duel" not in names
    assert "draw" not in names


def test_worker_role_skips_maa_hub(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PALLAS_SHARD_ENABLED", "true")
    monkeypatch.setenv("PALLAS_BOT_ROLE", "worker")
    monkeypatch.setenv("PALLAS_LOAD_BUNDLED_EXTRA", "1")
    get_shard_registry_settings.cache_clear()

    nonebot.init()
    load_plugins_for_role()

    loaded = {p.name for p in nonebot.get_loaded_plugins()}
    assert "maa_hub" not in loaded
    assert "maa" in loaded


def test_register_worker_console_metrics_only_on_worker(monkeypatch: pytest.MonkeyPatch):
    from pallas.core.platform.shard import worker_console_metrics as wcm

    monkeypatch.setenv("PALLAS_SHARD_ENABLED", "true")
    monkeypatch.setenv("PALLAS_BOT_ROLE", "hub")
    get_shard_registry_settings.cache_clear()
    wcm._registered = False
    wcm.register_worker_console_metrics_startup()
    assert wcm._registered is False

    monkeypatch.setenv("PALLAS_BOT_ROLE", "worker")
    get_shard_registry_settings.cache_clear()
    nonebot.init()
    wcm._registered = False
    wcm.register_worker_console_metrics_startup()
    assert wcm._registered is True

from __future__ import annotations

import nonebot
import pytest

from src.platform.bot_runtime.plugin_loader import (
    _discover_plugin_modules,
    _short_name,
    load_plugins_for_role,
)
from src.platform.bot_runtime.roles import UNIFIED_SKIP_PLUGIN_NAMES
from src.platform.shard.registry.config import get_shard_registry_settings


@pytest.fixture(autouse=True)
def clear_shard_settings_cache():
    get_shard_registry_settings.cache_clear()
    yield
    get_shard_registry_settings.cache_clear()


def test_unified_skip_plugin_names():
    assert UNIFIED_SKIP_PLUGIN_NAMES == frozenset({
        "relogin_forward",
        "maa_hub",
        "pallas_console_metrics",
    })


def test_discover_plugin_modules_excludes_underscore_packages():
    names = {_short_name(m) for m in _discover_plugin_modules()}
    assert "ingress_gate" in names
    assert "relogin_forward" in names
    assert "maa_hub" in names


def test_unified_role_skips_shard_only_plugins(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("PALLAS_SHARD_ENABLED", raising=False)
    monkeypatch.delenv("PALLAS_BOT_ROLE", raising=False)
    get_shard_registry_settings.cache_clear()

    nonebot.init()
    load_plugins_for_role()

    loaded = {p.name for p in nonebot.get_loaded_plugins()}
    assert "relogin_forward" not in loaded
    assert "maa_hub" not in loaded
    assert "pallas_console_metrics" not in loaded
    assert "relogin_bot" in loaded
    assert "maa" in loaded
    assert "ingress_gate" in loaded

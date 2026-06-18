from __future__ import annotations

import pytest

from pallas.core.platform.plugin_runtime.resolve import bundled_or_extra_module_prefix, import_plugin_submodule


def test_bundled_or_extra_module_prefix_falls_back_to_pallas_plugin_draw() -> None:
    prefix = bundled_or_extra_module_prefix("draw")
    pytest.importorskip("pallas_plugin_draw")
    assert prefix == "pallas_plugin_draw"


def test_import_plugin_submodule_draw_config() -> None:
    pytest.importorskip("pallas_plugin_draw")
    mod = import_plugin_submodule("draw", "config")
    assert mod.__name__ == "pallas_plugin_draw.config"
    assert hasattr(mod, "active_image_gen_settings")

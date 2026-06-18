"""按插件槽位 ID 解析 NoneBot 已加载插件包内的子模块。"""

from __future__ import annotations

import importlib
import importlib.util
from typing import TYPE_CHECKING

from nonebot import get_loaded_plugins

if TYPE_CHECKING:
    from types import ModuleType


def loaded_plugin_module_prefix(plugin_id: str) -> str | None:
    target = (plugin_id or "").strip()
    if not target:
        return None
    for plugin in get_loaded_plugins():
        name = str(getattr(plugin, "name", "") or "").strip()
        if name == target:
            mod = getattr(plugin, "module", None)
            module_name = getattr(mod, "__name__", "") if mod is not None else ""
            if module_name:
                return module_name.strip()
        mod = getattr(plugin, "module", None)
        module_name = getattr(mod, "__name__", "") if mod is not None else ""
        if module_name and module_name.rsplit(".", 1)[-1] == target:
            return module_name.strip()
    return None


def import_plugin_submodule(plugin_id: str, submodule: str) -> ModuleType:
    """优先 loaded 插件包；否则回退 bundled ``src.plugins`` 或官方 pip 扩展模块。"""
    sub = (submodule or "").strip().lstrip(".")
    if not sub:
        raise ValueError("submodule must be non-empty")
    prefix = loaded_plugin_module_prefix(plugin_id)
    if prefix is None:
        prefix = bundled_or_extra_module_prefix(plugin_id)
    return importlib.import_module(f"{prefix}.{sub}")


def bundled_or_extra_module_prefix(plugin_id: str) -> str:
    from pallas.core.platform.bot_runtime.plugin_matrix import EXTRA_PACKAGE_MODULES, EXTRA_PLUGIN_PACKAGES
    from pallas.core.platform.bot_runtime.plugin_package_aliases import canonical_plugin_package

    short = canonical_plugin_package((plugin_id or "").strip())
    bundled = f"packages.{short}"
    if importlib.util.find_spec(bundled) is not None:
        return bundled
    pkg = EXTRA_PLUGIN_PACKAGES.get(short)
    if pkg:
        for mod_root in EXTRA_PACKAGE_MODULES.get(pkg, ()):
            if importlib.util.find_spec(mod_root) is not None:
                return mod_root
    return bundled

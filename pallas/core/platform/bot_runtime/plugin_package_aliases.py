"""插件包名别名：遗留名、pip 模块名 → 规范插件 ID。"""

from __future__ import annotations


def _resolve_pip_module_canonical(module_name: str) -> str | None:
    """将 pip 扩展模块名映射到 ``EXTRA_PLUGIN_PACKAGES`` 键（规范插件 ID）。"""
    from pallas.core.platform.bot_runtime.plugin_matrix import EXTRA_PLUGIN_PACKAGES

    key = (module_name or "").strip()
    if not key:
        return None
    if key in EXTRA_PLUGIN_PACKAGES:
        return key
    prefix = "pallas_plugin_"
    if not key.startswith(prefix):
        return None
    suffix = key[len(prefix) :]
    if suffix in EXTRA_PLUGIN_PACKAGES:
        return suffix
    for canonical in EXTRA_PLUGIN_PACKAGES:
        if canonical.startswith("pb_") and canonical[len("pb_") :] == suffix:
            return canonical
    return None


def _build_extra_plugin_aliases() -> dict[str, str]:
    """由 ``EXTRA_PACKAGE_MODULES`` 自动生成 pip 模块 → 规范名。"""
    from pallas.core.platform.bot_runtime.plugin_matrix import EXTRA_PACKAGE_MODULES

    out: dict[str, str] = {}
    for modules in EXTRA_PACKAGE_MODULES.values():
        for mod in modules:
            canonical = _resolve_pip_module_canonical(mod)
            if canonical:
                out[mod] = canonical
    return out


_MANUAL_ALIASES: dict[str, str] = {
    "pallas_webui": "pb_webui",
    "pallas_protocol": "pb_protocol",
    "community_stats": "pb_stats",
    "pallas_plugin_community_stats": "pb_stats",
    "ollama": "llm_chat",
    "pallas_plugin_llm_chat": "llm_chat",
}

PLUGIN_PACKAGE_ALIASES: dict[str, str] = {
    **_MANUAL_ALIASES,
    **_build_extra_plugin_aliases(),
}


def canonical_plugin_package(name: str) -> str:
    key = (name or "").strip()
    if not key:
        return key
    return PLUGIN_PACKAGE_ALIASES.get(key, key)

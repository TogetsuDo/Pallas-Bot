"""帮助菜单：配置未启用的插件不进入总览。"""

from __future__ import annotations

import importlib

_CONFIG_GATED: dict[str, tuple[str, str, str]] = {
    "chat": ("src.plugins.chat.config", "get_chat_config", "chat_enable"),
    "sing": ("src.plugins.sing.config", "get_sing_config", "sing_enable"),
    "ollama": ("src.plugins.ollama.config", "get_ollama_config", "ollama_enable"),
}


def is_plugin_help_available(plugin_name: str) -> bool:
    gate = _CONFIG_GATED.get((plugin_name or "").strip())
    if gate is None:
        return True
    module_path, getter_name, field = gate
    try:
        mod = importlib.import_module(module_path)
        getter = getattr(mod, getter_name)
        cfg = getter()
        return bool(getattr(cfg, field, False))
    except Exception:
        return False

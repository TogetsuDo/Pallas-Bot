"""插件槽位运行时：解析当前 loaded 插件模块。"""

from pallas.core.platform.plugin_runtime.resolve import (
    import_plugin_submodule,
    loaded_plugin_module_prefix,
)

__all__ = [
    "import_plugin_submodule",
    "loaded_plugin_module_prefix",
]

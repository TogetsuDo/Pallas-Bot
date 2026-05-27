"""进程角色：unified / hub / worker。"""

from __future__ import annotations

from src.platform.shard.registry.config import BotRole, get_shard_registry_settings, is_sharding_active

# hub：控制台、协议端、建号/重登；不加载游戏插件（无反向 WS 也可启动）
HUB_PLUGIN_MODULES: tuple[str, ...] = (
    "src.plugins.pallas_webui",
    "src.plugins.pallas_protocol",
    "src.plugins.relogin_bot",
    "src.plugins.callback",
    "src.plugins.maa_hub",
    "src.plugins.blacklist",
    "src.plugins.help",
    "src.plugins.community_stats",
)

# worker：跳过 hub 独占插件
WORKER_SKIP_PLUGIN_NAMES: frozenset[str] = frozenset({
    "pallas_webui",
    "pallas_protocol",
    "relogin_bot",
})

# unified：跳过仅分片 hub/worker 使用的插件（单进程用 relogin_bot、maa，不经 hub 转发）
UNIFIED_SKIP_PLUGIN_NAMES: frozenset[str] = frozenset({
    "relogin_forward",
    "maa_hub",
})

# unified WebUI 插件目录不展示（含未扫描的 _ingress_gate）
UNIFIED_CATALOG_HIDDEN_PLUGIN_NAMES: frozenset[str] = UNIFIED_SKIP_PLUGIN_NAMES | frozenset({
    "_ingress_gate",
})


def bot_role() -> BotRole:
    return get_shard_registry_settings().role


def is_unified_role() -> bool:
    s = get_shard_registry_settings()
    return not s.enabled or s.role == "unified"


def is_hub_role() -> bool:
    return is_sharding_active() and get_shard_registry_settings().role == "hub"


def is_sharded_hub() -> bool:
    return is_hub_role()


def is_sharded_worker() -> bool:
    return is_sharding_active() and get_shard_registry_settings().role == "worker"


def hub_plugin_modules() -> tuple[str, ...]:
    return HUB_PLUGIN_MODULES


def worker_skip_plugin_names() -> frozenset[str]:
    return WORKER_SKIP_PLUGIN_NAMES


def unified_skip_plugin_names() -> frozenset[str]:
    return UNIFIED_SKIP_PLUGIN_NAMES


def unified_catalog_hidden_plugin_names() -> frozenset[str]:
    return UNIFIED_CATALOG_HIDDEN_PLUGIN_NAMES

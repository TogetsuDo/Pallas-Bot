"""按角色加载 NoneBot 插件。"""

from __future__ import annotations

import importlib.util

import nonebot
from nonebot import logger

from src.common.apscheduler_runtime import register_apscheduler_startup_hook
from src.common.bot_runtime.pyproject_plugins import (
    extra_plugin_dirs_for_role,
    parse_nonebot_plugin_config,
)
from src.common.bot_runtime.roles import (
    HUB_PLUGIN_MODULES,
    WORKER_SKIP_PLUGIN_NAMES,
    is_unified_role,
)
from src.common.config.repo_settings import read_bootstrap_extra_plugin_dirs
from src.common.paths import PROJECT_ROOT

_PLUGINS_ROOT = PROJECT_ROOT / "src" / "plugins"
_PYPROJECT = PROJECT_ROOT / "pyproject.toml"
_APSCHEDULER_MODULE = "nonebot_plugin_apscheduler"


def _discover_plugin_modules() -> list[str]:
    names: list[str] = []
    if not _PLUGINS_ROOT.is_dir():
        return names
    for entry in sorted(_PLUGINS_ROOT.iterdir()):
        if not entry.is_dir():
            continue
        if entry.name.startswith("_"):
            continue
        if not (entry / "__init__.py").is_file():
            continue
        names.append(f"src.plugins.{entry.name}")
    return names


def _short_name(module_path: str) -> str:
    return module_path.rsplit(".", 1)[-1]


def _prioritize_scheduler_modules(module_paths: list[str]) -> list[str]:
    """nonebot_plugin_apscheduler 须先于依赖 scheduler 的 src 插件加载。"""
    sched = [m for m in module_paths if _short_name(m) == _APSCHEDULER_MODULE]
    rest = [m for m in module_paths if m not in sched]
    return sched + rest


def load_apscheduler_plugin_first(*, role_label: str, loaded_short: set[str]) -> bool:
    if _short_name(_APSCHEDULER_MODULE) in loaded_short:
        return False
    if _load_plugin_module(_APSCHEDULER_MODULE, role_label=role_label, loaded_short=loaded_short):
        register_apscheduler_startup_hook()
        return True
    return False


def _load_plugin_module(
    module_path: str,
    *,
    role_label: str,
    loaded_short: set[str],
) -> bool:
    short = _short_name(module_path)
    if short in loaded_short:
        return False
    if importlib.util.find_spec(module_path) is None:
        logger.error(
            "bot_runtime: {} skip {} (pip 包未安装，请在仓库根目录执行 uv sync)",
            role_label,
            module_path,
        )
        return False
    try:
        nonebot.load_plugin(module_path)
        loaded_short.add(short)
        return True
    except Exception as e:
        logger.warning("bot_runtime: {} failed to load {}: {}", role_label, module_path, e)
        return False


def _load_toml_module_plugins(
    module_paths: list[str],
    *,
    role_label: str,
    skip_short: frozenset[str],
    loaded_short: set[str],
) -> int:
    count = 0
    for mod in module_paths:
        short = _short_name(mod)
        if short in skip_short or short in loaded_short:
            continue
        if _load_plugin_module(mod, role_label=role_label, loaded_short=loaded_short):
            count += 1
    return count


def _load_toml_extra_plugin_dirs(
    plugin_dirs: list[str],
    *,
    role_label: str,
    loaded_short: set[str],
) -> int:
    count = 0
    for rel_dir in plugin_dirs:
        root = PROJECT_ROOT / rel_dir
        if not root.is_dir():
            logger.warning("bot_runtime: {} plugin_dir missing: {}", role_label, rel_dir)
            continue
        try:
            found = nonebot.load_plugins(rel_dir)
        except Exception as e:
            logger.warning("bot_runtime: {} load_plugins({}) failed: {}", role_label, rel_dir, e)
            continue
        for plugin in found:
            mod = getattr(plugin, "module", None)
            if mod is None:
                continue
            name = getattr(mod, "__name__", "") or ""
            if name:
                loaded_short.add(_short_name(name))
        count += len(found)
        logger.info("bot_runtime: {} load_plugins({}) -> {} plugin(s)", role_label, rel_dir, len(found))
    return count


def _append_bootstrap_plugin_dirs(plugin_dirs: list[str]) -> list[str]:
    out = list(plugin_dirs)
    seen = {d.strip().replace("\\", "/").rstrip("/") for d in out}
    for d in read_bootstrap_extra_plugin_dirs():
        norm = d.strip().replace("\\", "/").rstrip("/")
        if norm and norm not in seen:
            seen.add(norm)
            out.append(d)
    return out


def load_pyproject_extra_plugins(
    *,
    role_label: str,
    skip_short: frozenset[str],
    loaded_short: set[str],
    include_extra_dirs: bool,
    include_bootstrap_dirs: bool = True,
) -> int:
    """加载 pyproject [tool.nonebot.plugins] 与（可选）额外 plugin_dirs。"""
    module_paths, plugin_dirs = parse_nonebot_plugin_config(_PYPROJECT)
    module_paths = _prioritize_scheduler_modules(module_paths)
    total = 0
    if include_extra_dirs:
        extra_dirs = extra_plugin_dirs_for_role(plugin_dirs)
        if include_bootstrap_dirs:
            extra_dirs = _append_bootstrap_plugin_dirs(extra_dirs)
        total += _load_toml_extra_plugin_dirs(extra_dirs, role_label=role_label, loaded_short=loaded_short)
    total += _load_toml_module_plugins(
        module_paths,
        role_label=role_label,
        skip_short=skip_short,
        loaded_short=loaded_short,
    )
    return total


def load_plugins_for_role() -> None:
    if is_unified_role():
        nonebot.load_from_toml("pyproject.toml")
        register_apscheduler_startup_hook()
        bootstrap_dirs = read_bootstrap_extra_plugin_dirs()
        if bootstrap_dirs:
            loaded_short: set[str] = set()
            n = _load_toml_extra_plugin_dirs(
                bootstrap_dirs,
                role_label="unified",
                loaded_short=loaded_short,
            )
            logger.info("bot_runtime: role=unified, bootstrap extra plugin_dirs={} -> {}", bootstrap_dirs, n)
        logger.info("bot_runtime: role=unified, load_from_toml(all plugins)")
        return

    if not _PLUGINS_ROOT.is_dir():
        nonebot.load_from_toml("pyproject.toml")
        return

    from src.common.bot_runtime.roles import is_hub_role

    loaded_short: set[str] = set()

    if is_hub_role():
        load_apscheduler_plugin_first(role_label="hub", loaded_short=loaded_short)
        loaded = 0
        for mod in HUB_PLUGIN_MODULES:
            if _load_plugin_module(mod, role_label="hub", loaded_short=loaded_short):
                loaded += 1
        extra = load_pyproject_extra_plugins(
            role_label="hub",
            skip_short=WORKER_SKIP_PLUGIN_NAMES,
            loaded_short=loaded_short,
            include_extra_dirs=False,
        )
        logger.info(
            "bot_runtime: role=hub, loaded {}/{} hub modules, +{} from pyproject.plugins",
            loaded,
            len(HUB_PLUGIN_MODULES),
            extra,
        )
        return

    load_apscheduler_plugin_first(role_label="worker", loaded_short=loaded_short)

    ingress_gate = "src.plugins._ingress_gate"
    gate_path = _PLUGINS_ROOT / "_ingress_gate"
    if gate_path.is_dir() and (gate_path / "__init__.py").is_file():
        _load_plugin_module(ingress_gate, role_label="worker", loaded_short=loaded_short)

    bootstrap_dirs = read_bootstrap_extra_plugin_dirs()
    bootstrap_loaded = 0
    if bootstrap_dirs:
        bootstrap_loaded = _load_toml_extra_plugin_dirs(
            bootstrap_dirs,
            role_label="worker",
            loaded_short=loaded_short,
        )

    loaded = 0
    for mod in _discover_plugin_modules():
        short = _short_name(mod)
        if short in WORKER_SKIP_PLUGIN_NAMES:
            continue
        if mod == ingress_gate:
            continue
        if short in loaded_short:
            continue
        if _load_plugin_module(mod, role_label="worker", loaded_short=loaded_short):
            loaded += 1

    extra = load_pyproject_extra_plugins(
        role_label="worker",
        skip_short=WORKER_SKIP_PLUGIN_NAMES,
        loaded_short=loaded_short,
        include_extra_dirs=True,
        include_bootstrap_dirs=False,
    )

    from src.common.shard.registry.config import get_shard_registry_settings

    s = get_shard_registry_settings()
    logger.info(
        "bot_runtime: role=worker shard_id={} local_plugins={} src_plugins={} pyproject_extra={} skip={}",
        s.shard_id,
        bootstrap_loaded,
        loaded,
        extra,
        sorted(WORKER_SKIP_PLUGIN_NAMES),
    )

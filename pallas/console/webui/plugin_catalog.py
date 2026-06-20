"""插件目录：磁盘发现与分片角色。"""

from __future__ import annotations

import ast
import importlib
import importlib.util
from pathlib import Path  # noqa: TC003
from typing import Any

from pallas.console.webui.community_plugin_assets import resolve_community_plugin_icon
from pallas.console.webui.community_plugin_index import (
    DEFAULT_INDEX_REL,
    LOCAL_INDEX_REL,
    load_index_from_path,
)
from pallas.console.webui.community_plugin_registry import resolve_community_plugin_avatar
from pallas.console.webui.plugin_registry import official_extension_for_plugin
from pallas.core.foundation.paths import PROJECT_ROOT
from pallas.core.platform.bot_runtime.plugin_matrix import (
    EXTRA_PACKAGE_MODULES,
    extra_package_for_plugin,
    is_core_plugin,
    is_extra_plugin,
)
from pallas.core.platform.plugin_runtime.plugin_identity import canonical_plugin_id

_PLUGINS_ROOT = PROJECT_ROOT / "packages"

PluginSourceKind = str  # "core" | "extra" | "local" | "pip"

_INFRA_NAME_PREFIXES = (
    "nonebot",
    "nonebot_plugin",
    "nonebot-plugin",
    "uniseg",
)

_INFRA_EXACT = frozenset({
    "nonebot_plugin_waiter",
    "nonebot_plugin_apscheduler",
    "nonebot-plugin-apscheduler",
    "nonebot-plugin-alconna",
    "nonebot_plugin_alconna",
})
_BRAND_AVATAR_PATH = "/pallas/assets/brand-avatar.png"


def discover_plugin_packages() -> list[str]:
    if not _PLUGINS_ROOT.is_dir():
        return []
    out: list[str] = []
    for entry in sorted(_PLUGINS_ROOT.iterdir()):
        if not entry.is_dir() or entry.name.startswith("."):
            continue
        if entry.name.startswith("_"):
            continue
        if not (entry / "__init__.py").is_file():
            continue
        out.append(entry.name)
    return out


def discover_pyproject_plugin_modules() -> list[str]:
    """pyproject [tool.nonebot.plugins] 声明的 pip/外部模块。"""
    from pallas.core.platform.bot_runtime.pyproject_plugins import parse_nonebot_plugin_config

    modules, _dirs = parse_nonebot_plugin_config()
    return list(modules)


def discover_extra_plugin_packages() -> dict[str, Path]:
    """站点 ``extra_plugin_dirs`` 下的插件包：目录名 → 包根路径。"""
    from pallas.core.foundation.config.repo_settings import resolve_extra_plugin_dirs

    out: dict[str, Path] = {}
    for rel in resolve_extra_plugin_dirs():
        root = (PROJECT_ROOT / rel).resolve()
        if not root.is_dir():
            continue
        for entry in sorted(root.iterdir()):
            if not entry.is_dir() or entry.name.startswith("."):
                continue
            if not (entry / "__init__.py").is_file():
                continue
            out[entry.name] = entry
    return out


def plugin_source_from_module_path(mod_file: str) -> PluginSourceKind | None:
    if not mod_file:
        return None
    try:
        rel = Path(mod_file).resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError:
        return "pip"
    if rel.startswith("local/"):
        return "local"
    if rel.startswith("packages/"):
        package = rel.removeprefix("packages/").split("/", 1)[0]
        if is_core_plugin(package):
            return "core"
        if is_extra_plugin(package):
            return "extra"
        return "core"
    return "pip"


def module_dir_rel(mod_file: str) -> str | None:
    if not mod_file:
        return None
    try:
        return Path(mod_file).resolve().parent.relative_to(PROJECT_ROOT.resolve()).as_posix()
    except (ValueError, OSError):
        return None


def infer_plugin_source(
    package: str,
    loaded: object | None,
    *,
    extra_pkgs: dict[str, Path],
) -> tuple[PluginSourceKind, str | None]:
    if loaded is not None:
        mod = getattr(loaded, "module", None)
        module_name = getattr(mod, "__name__", "") if mod is not None else ""
        file_path = getattr(mod, "__file__", "") if mod is not None else ""
        src = plugin_source_from_module_path(file_path)
        if src == "local":
            return "local", module_dir_rel(file_path) or _package_dir_posix(extra_pkgs.get(package))
        if src in ("core", "extra"):
            return src, module_dir_rel(file_path) or f"packages/{package}"
        if src == "pip":
            if is_extra_plugin(package):
                bundled_root = _PLUGINS_ROOT / package
                bundled_dir = f"packages/{package}" if (bundled_root / "__init__.py").is_file() else None
                return "extra", bundled_dir
            return "pip", None
        if module_name.startswith("packages."):
            if is_extra_plugin(package):
                return "extra", f"packages/{package}"
            return "core", f"packages/{package}"
        if extra_pkgs.get(package) is not None:
            return "local", _package_dir_posix(extra_pkgs.get(package))
    local_root = extra_pkgs.get(package)
    if local_root is not None:
        return "local", _package_dir_posix(local_root)
    if (_PLUGINS_ROOT / package / "__init__.py").is_file():
        if is_extra_plugin(package):
            return "extra", f"packages/{package}"
        return "core", f"packages/{package}"
    return "pip", None


def _package_dir_posix(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _parse_plugin_metadata_stub(init_path: Path) -> dict[str, Any] | None:
    def literalish(node: ast.AST) -> Any:
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.List):
            return [literalish(item) for item in node.elts]
        if isinstance(node, ast.Tuple):
            return [literalish(item) for item in node.elts]
        if isinstance(node, ast.Set):
            return [literalish(item) for item in node.elts]
        if isinstance(node, ast.Dict):
            out: dict[str, Any] = {}
            for key_node, val_node in zip(node.keys, node.values, strict=False):
                if key_node is None:
                    continue
                key = literalish(key_node)
                if not isinstance(key, str):
                    continue
                out[key] = literalish(val_node)
            return out
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            value = literalish(node.operand)
            if isinstance(value, (int, float)):
                return -value
        return None

    try:
        text = init_path.read_text(encoding="utf-8")
    except OSError:
        return None
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return None
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if not isinstance(target, ast.Name) or target.id != "__plugin_meta__":
                continue
            if not isinstance(node.value, ast.Call):
                continue
            meta: dict[str, Any] = {}
            for kw in node.value.keywords:
                key = kw.arg
                if not key or key in ("supported_adapters", "homepage"):
                    continue
                if key in ("name", "description", "usage", "type"):
                    val = literalish(kw.value)
                    if isinstance(val, str):
                        meta[key] = val
                    continue
                if key == "extra":
                    extra = literalish(kw.value)
                    if isinstance(extra, dict) and extra:
                        menu_data = extra.get("menu_data")
                        if isinstance(menu_data, list):
                            extra = {"menu_data": menu_data}
                        else:
                            extra = {}
                        if extra:
                            meta["extra"] = extra
            if meta.get("name"):
                return meta
    return None


def package_load_role(package: str) -> str:
    from pallas.core.platform.bot_runtime.roles import (
        HUB_PLUGIN_MODULES,
        WORKER_SKIP_PLUGIN_NAMES,
        is_sharding_active,
        is_unified_role,
    )

    if package == "ingress_gate":
        if is_unified_role() or not is_sharding_active():
            return "both"
        return "worker"
    if package == "relogin_forward":
        return "worker"
    if package == "maa_hub":
        return "hub"
    if is_unified_role() or not is_sharding_active():
        return "both"
    if package.startswith("_"):
        return "internal"
    hub_short = {m.rsplit(".", 1)[-1] for m in HUB_PLUGIN_MODULES}
    if package in WORKER_SKIP_PLUGIN_NAMES:
        return "hub"
    if package in hub_short:
        return "hub"
    return "worker"


def is_infrastructure_plugin_name(name: str, module_name: str) -> bool:
    n = (name or "").strip().lower()
    m = (module_name or "").strip().lower()
    if n in _INFRA_EXACT or m in _INFRA_EXACT:
        return True
    return any(n.startswith(p) or m.startswith(p) for p in _INFRA_NAME_PREFIXES)


def package_has_config_module(package: str, *, package_root: Path | None = None) -> bool:
    root = package_root if package_root is not None else (_PLUGINS_ROOT / package)
    return (root / "config.py").is_file()


def module_has_config_module(module_name: str) -> bool:
    if not module_name:
        return False
    try:
        spec = importlib.util.find_spec(f"{module_name}.config")
    except (ImportError, ModuleNotFoundError, ValueError):
        return False
    return spec is not None


def _loaded_plugin_index() -> tuple[dict[str, Any], dict[str, Any]]:
    from nonebot import get_loaded_plugins

    by_nb_name: dict[str, Any] = {}
    by_package: dict[str, Any] = {}
    for p in get_loaded_plugins():
        nb = str(getattr(p, "name", "") or "").strip()
        if nb:
            by_nb_name[nb] = p
        mod = getattr(p, "module", None)
        module_name = getattr(mod, "__name__", "") if mod is not None else ""
        if not module_name:
            module_name = str(getattr(p, "module_name", "") or "")
        short = module_name.rsplit(".", 1)[-1] if module_name else ""
        if short:
            by_package[short] = p
            resolved = canonical_plugin_id(short)
            if resolved:
                by_package.setdefault(resolved, p)
        if nb:
            by_package.setdefault(nb, p)
            resolved = canonical_plugin_id(nb)
            if resolved:
                by_package.setdefault(resolved, p)
    return by_nb_name, by_package


def _module_short_name(module_path: str) -> str:
    return (module_path or "").rsplit(".", 1)[-1]


def resolved_plugin_identity(raw_name: str, module_name: str = "") -> str:
    for candidate in (raw_name, module_name, _module_short_name(module_name)):
        resolved = canonical_plugin_id((candidate or "").strip())
        if resolved:
            return resolved
    return (raw_name or "").strip()


def _pip_plugin_metadata_stub(module_path: str) -> dict[str, Any] | None:
    """未加载时从已安装包 __init__.py 解析 __plugin_meta__。"""
    try:
        spec = importlib.util.find_spec(module_path)
    except (ImportError, ModuleNotFoundError, ValueError):
        return None
    if spec is None:
        return None
    origin = getattr(spec, "origin", None) or ""
    if not origin or origin.endswith("__init__.py"):
        init_path = Path(origin) if origin else None
    else:
        init_path = Path(origin).parent / "__init__.py"
    if init_path is None or not init_path.is_file():
        sub = getattr(spec, "submodule_search_locations", None)
        if sub:
            init_path = Path(sub[0]) / "__init__.py"
    if init_path is None or not init_path.is_file():
        return None
    return _parse_plugin_metadata_stub(init_path)


def resolve_catalog_process_role() -> str:
    """当前响应插件目录的 NoneBot 进程角色。"""
    from pallas.core.platform.bot_runtime.roles import is_sharded_hub, is_sharded_worker, is_unified_role

    if is_unified_role():
        return "unified"
    if is_sharded_hub():
        return "hub"
    if is_sharded_worker():
        return "worker"
    return "unified"


def expected_loaded_in_catalog_process(load_role: str, catalog_role: str) -> bool:
    """该插件是否应在 catalog_process_role 对应进程中加载。"""
    role = (load_role or "").strip()
    if catalog_role == "unified":
        return role in ("both", "infra")
    if catalog_role == "hub":
        return role in ("hub", "infra", "both")
    if catalog_role == "worker":
        return role in ("worker", "internal")
    return True


def should_show_in_plugin_catalog(package: str) -> bool:
    """单进程 unified 下不展示分片专用、本进程未加载的插件。"""
    from pallas.core.platform.bot_runtime.roles import (
        is_unified_role,
        unified_catalog_hidden_plugin_names,
    )

    if is_unified_role() and package in unified_catalog_hidden_plugin_names():
        return False
    return True


def metadata_to_dict(meta: object | None) -> dict[str, Any] | None:
    if meta is None:
        return None
    d: dict[str, Any] = {
        "name": getattr(meta, "name", None),
        "description": (getattr(meta, "description", None) or "")[:2000],
        "usage": (getattr(meta, "usage", None) or "")[:4000],
    }
    ex = getattr(meta, "extra", None)
    if ex:
        d["extra"] = dict(ex) if isinstance(ex, dict) else ex
    typ = getattr(meta, "type", None)
    if typ is not None:
        d["type"] = str(typ)
    return d


def community_plugin_row_for_plugin(plugin_id: str) -> dict[str, Any] | None:
    from pallas.console.webui.community_plugin_install import community_plugins_root

    pid = (plugin_id or "").strip()
    if not pid:
        return None
    root = community_plugins_root()
    plugin_dir = root / pid
    if not plugin_dir.is_dir():
        return None
    for rel in (LOCAL_INDEX_REL, DEFAULT_INDEX_REL):
        try:
            _source, _meta, plugins = load_index_from_path(rel)
        except Exception:
            continue
        for entry in plugins:
            if str(entry.get("plugin_id") or "").strip() == pid:
                return entry
    return None


def resolve_catalog_visuals(
    *,
    plugin_id: str,
    plugin_source: PluginSourceKind,
) -> dict[str, str | None]:
    community = community_plugin_row_for_plugin(plugin_id)
    if community is not None:
        return {
            "avatar": resolve_community_plugin_avatar(community),
            "icon": resolve_community_plugin_icon(community),
            "cover": community.get("cover"),
        }

    official = official_extension_for_plugin(plugin_id)
    if official is not None:
        cover = str(official.get("cover") or "").strip() or None
        icon = cover or (str(official.get("icon") or "").strip() or None)
        return {
            "avatar": None,
            "icon": icon,
            "cover": cover,
        }

    if is_core_plugin(plugin_id) or plugin_source == "core":
        return {"avatar": None, "icon": _BRAND_AVATAR_PATH, "cover": None}

    return {"avatar": None, "icon": None, "cover": None}


def build_plugin_catalog_rows(
    *,
    ignored: set[str] | None = None,
    hidden: set[str] | None = None,
    globally_disabled: set[str] | None = None,
    global_disable_protected: set[str] | None = None,
) -> list[dict[str, Any]]:
    """合并磁盘插件与当前进程已加载插件。"""
    ignored = ignored or set()
    hidden = hidden or set()
    globally_disabled = globally_disabled or set()
    global_disable_protected = global_disable_protected or set()
    _, by_package = _loaded_plugin_index()
    extra_pkgs = discover_extra_plugin_packages()
    rows: list[dict[str, Any]] = []
    seen_packages: set[str] = set()

    def _help_flags(nb_name: str, package: str) -> tuple[bool, bool, bool]:
        ids = {nb_name, package, f"packages.{package}"}
        ign = any(x in ignored for x in ids if x)
        hid = any(x in hidden for x in ids if x)
        visible = not ign and not hid
        return visible, ign, hid

    def _append_row(
        *,
        package: str,
        module_name: str,
        nb_name: str,
        meta: dict[str, Any] | None,
        loaded: bool,
        role: str,
        plugin_source: PluginSourceKind,
        plugin_source_dir: str | None,
        has_config: bool,
    ) -> None:
        resolved_plugin_id = resolved_plugin_identity(package, module_name or nb_name)
        visible, ign, hid = _help_flags(nb_name, resolved_plugin_id)
        ids = {nb_name, package, resolved_plugin_id, f"packages.{resolved_plugin_id}"}
        g_disabled = any(x in globally_disabled for x in ids if x)
        g_protected = any(x in global_disable_protected for x in ids if x)
        visuals = resolve_catalog_visuals(plugin_id=resolved_plugin_id, plugin_source=plugin_source)
        rows.append({
            "name": resolved_plugin_id,
            "nb_plugin_name": nb_name,
            "module": module_name,
            "resolved_plugin_id": resolved_plugin_id,
            "resolved_module": module_name,
            "metadata": meta,
            "load_role": role,
            "loaded_in_process": loaded,
            "has_config": has_config,
            "configurable": has_config,
            "help_visible": visible,
            "help_ignored": ign,
            "help_hidden": hid,
            "globally_disabled": g_disabled,
            "global_disable_protected": g_protected,
            "plugin_source": plugin_source,
            "plugin_source_dir": plugin_source_dir,
            "extra_package": extra_package_for_plugin(resolved_plugin_id),
            "avatar": visuals["avatar"],
            "icon": visuals["icon"],
            "cover": visuals["cover"],
        })

    all_packages = sorted(set(discover_plugin_packages()) | set(extra_pkgs.keys()))
    for package in all_packages:
        if not should_show_in_plugin_catalog(package):
            continue
        seen_packages.add(package)
        local_root = extra_pkgs.get(package)
        main_root = _PLUGINS_ROOT / package
        disk_root = local_root if local_root is not None else main_root
        if not (disk_root / "__init__.py").is_file():
            continue
        init_path = disk_root / "__init__.py"
        stub = _parse_plugin_metadata_stub(init_path)
        loaded = package in by_package
        p = by_package.get(package)
        nb_name = str(getattr(p, "name", "") or "") if p is not None else package
        module_name = f"packages.{package}"
        if p is not None:
            mod = getattr(p, "module", None)
            module_name = getattr(mod, "__name__", "") or module_name
        meta = stub
        if p is not None and getattr(p, "metadata", None) is not None:
            meta = metadata_to_dict(p.metadata) or stub
        elif stub:
            meta = stub
        role = package_load_role(package)
        plugin_source, plugin_source_dir = infer_plugin_source(package, p, extra_pkgs=extra_pkgs)
        _append_row(
            package=package,
            module_name=module_name,
            nb_name=nb_name,
            meta=meta,
            loaded=loaded,
            role=role,
            plugin_source=plugin_source,
            plugin_source_dir=plugin_source_dir,
            has_config=package_has_config_module(package, package_root=disk_root),
        )

    for module_path in discover_pyproject_plugin_modules():
        package = _module_short_name(module_path)
        if not package or package in seen_packages:
            continue
        seen_packages.add(package)
        p = by_package.get(package)
        loaded = p is not None
        nb_name = str(getattr(p, "name", "") or "") if p is not None else package
        module_name = module_path
        if p is not None:
            mod = getattr(p, "module", None)
            module_name = getattr(mod, "__name__", "") or module_name
        meta = metadata_to_dict(getattr(p, "metadata", None)) if p is not None else None
        if meta is None:
            meta = _pip_plugin_metadata_stub(module_path)
        _append_row(
            package=package,
            module_name=module_name,
            nb_name=nb_name,
            meta=meta,
            loaded=loaded,
            role="infra",
            plugin_source="pip",
            plugin_source_dir=None,
            has_config=module_has_config_module(module_name),
        )

    for module_paths in EXTRA_PACKAGE_MODULES.values():
        for module_path in module_paths:
            package = _module_short_name(module_path)
            resolved_plugin_id = canonical_plugin_id(package)
            if not resolved_plugin_id or resolved_plugin_id in seen_packages:
                continue
            if not should_show_in_plugin_catalog(resolved_plugin_id):
                continue
            seen_packages.add(resolved_plugin_id)
            p = by_package.get(resolved_plugin_id) or by_package.get(package)
            loaded = p is not None
            nb_name = str(getattr(p, "name", "") or "") if p is not None else resolved_plugin_id
            module_name = module_path
            if p is not None:
                mod = getattr(p, "module", None)
                module_name = getattr(mod, "__name__", "") or module_name
            meta = metadata_to_dict(getattr(p, "metadata", None)) if p is not None else None
            if meta is None:
                meta = _pip_plugin_metadata_stub(module_path)
            if meta is None:
                continue
            _append_row(
                package=resolved_plugin_id,
                module_name=module_name,
                nb_name=nb_name,
                meta=meta,
                loaded=loaded,
                role=package_load_role(resolved_plugin_id),
                plugin_source="extra" if len(module_paths) == 1 else "pip",
                plugin_source_dir=None,
                has_config=module_has_config_module(module_name),
            )

    from nonebot import get_loaded_plugins

    for p in get_loaded_plugins():
        nb_name = str(getattr(p, "name", "") or "").strip()
        if not nb_name:
            continue
        mod = getattr(p, "module", None)
        module_name = getattr(mod, "__name__", "") if mod is not None else ""
        short = module_name.rsplit(".", 1)[-1] if module_name else ""
        if short in seen_packages:
            continue
        if not is_infrastructure_plugin_name(nb_name, module_name):
            continue
        pkg_key = short or nb_name
        seen_packages.add(pkg_key)
        _append_row(
            package=pkg_key,
            module_name=module_name,
            nb_name=nb_name,
            meta=metadata_to_dict(getattr(p, "metadata", None)),
            loaded=True,
            role="infra",
            plugin_source="pip",
            plugin_source_dir=None,
            has_config=module_has_config_module(module_name),
        )

    catalog_role = resolve_catalog_process_role()
    for row in rows:
        row["catalog_process_role"] = catalog_role
        row["expected_in_catalog_process"] = expected_loaded_in_catalog_process(
            str(row.get("load_role") or ""),
            catalog_role,
        )

    rows.sort(key=lambda x: (x.get("load_role") != "infra", (x.get("metadata") or {}).get("name") or x["name"]))
    return rows


def _package_dir_to_module_id(package_root: Path) -> str:
    rel = package_root.resolve().relative_to(PROJECT_ROOT.resolve())
    return rel.as_posix().replace("/", ".")


def resolve_catalog_plugin_module(plugin_name: str) -> str | None:
    """按目录名或 NoneBot 插件名解析插件模块路径。"""
    from packages.help.plugin_legacy_names import canonical_plugin_name

    target = canonical_plugin_name((plugin_name or "").strip())
    if not target:
        return None
    _, by_package = _loaded_plugin_index()
    p = by_package.get(target)
    if p is not None:
        mod = getattr(p, "module", None)
        return getattr(mod, "__name__", "") if mod is not None else None
    extra_pkgs = discover_extra_plugin_packages()
    if target in extra_pkgs:
        return _package_dir_to_module_id(extra_pkgs[target])
    if (_PLUGINS_ROOT / target / "__init__.py").is_file():
        return f"packages.{target}"
    return None


def load_config_class_for_package(package: str) -> type | None:
    module_name = resolve_catalog_plugin_module(package)
    if not module_name:
        return None
    cfg_mod_name = f"{module_name}.config" if not module_name.endswith(".config") else module_name
    try:
        cfg_mod = importlib.import_module(cfg_mod_name)
    except Exception:
        return None
    cfg_cls = getattr(cfg_mod, "Config", None)
    if cfg_cls is None or not isinstance(cfg_cls, type):
        return None
    return cfg_cls

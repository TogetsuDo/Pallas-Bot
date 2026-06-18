"""社区插件作者工具：目录校验与索引条目生成。"""

from __future__ import annotations

import ast
import json
import re
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from pallas.console.webui.community_plugin_assets import infer_community_plugin_icon, parse_git_host_repo
from pallas.console.webui.community_plugin_index import normalize_index_entry, parse_index_document
from pallas.console.webui.community_plugin_install import PLUGIN_ID_RE

if TYPE_CHECKING:
    from pathlib import Path

ICON_ASSET_PATHS = (
    "assets/icon.png",
    "assets/icon.webp",
    "assets/icon.svg",
    "assets/avatar.png",
    "assets/avatar.jpg",
)

# ---- import 规则（L1 社区插件） ----
FORBIDDEN_PREFIXES_L1 = (
    "pallas.core.",
    "pallas.console.",
    "pallas.product.",
    "src.",
)

ALLOWED_API_PREFIX = "pallas.api."


def _module_names_from_import(node: ast.AST) -> list[str]:
    names: list[str] = []
    if isinstance(node, ast.Import):
        for alias in node.names:
            names.append(alias.name)
    elif isinstance(node, ast.ImportFrom):
        if node.module:
            names.append(node.module)
    return names


def _check_file_imports(path: Path) -> list[str]:
    """检查单文件 import 是否符合 L1 规则。返回错误消息列表。"""
    errors: list[str] = []
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as exc:
        return [f"{path.name}: 语法错误 {exc}"]
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        for mod in _module_names_from_import(node):
            if mod.startswith(FORBIDDEN_PREFIXES_L1):
                errors.append(
                    f"禁止 import `{mod}`（社区插件仅允许 `pallas.api.*`）"
                )
                continue
            if mod.startswith("pallas.") and not mod.startswith(ALLOWED_API_PREFIX):
                errors.append(
                    f"仅允许 `pallas.api.*`，发现 `{mod}`"
                )
    return errors


def _validate_plugin_imports(plugin_dir: Path) -> list[str]:
    """扫描插件目录所有 .py 文件的 import 是否符合 L1 规则。"""
    errors: list[str] = []
    for py_file in sorted(plugin_dir.rglob("*.py")):
        if not py_file.is_file():
            continue
        file_errors = _check_file_imports(py_file)
        for err in file_errors:
            errors.append(f"{py_file.name}: {err}")
    return errors


def read_plugin_metadata_from_init(init_path: Path) -> dict[str, str]:
    """从 __init__.py 提取 PLUGIN_ID 与 PluginMetadata 常见字段（best-effort）。"""
    text = init_path.read_text(encoding="utf-8")
    out: dict[str, str] = {}

    pid_match = re.search(r'^\s*PLUGIN_ID\s*=\s*["\']([^"\']+)["\']', text, flags=re.MULTILINE)
    if pid_match:
        out["plugin_id"] = pid_match.group(1).strip()

    try:
        tree = ast.parse(text)
    except SyntaxError:
        return out

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = ""
        if isinstance(func, ast.Name):
            name = func.id
        elif isinstance(func, ast.Attribute):
            name = func.attr
        if name != "PluginMetadata":
            continue
        for keyword in node.keywords:
            if keyword.arg in {"name", "description", "homepage"} and isinstance(keyword.value, ast.Constant):
                if isinstance(keyword.value.value, str):
                    out[keyword.arg] = keyword.value.value.strip()
        break
    return out


def validate_community_plugin_dir(plugin_dir: Path) -> tuple[list[str], list[str]]:
    """返回 (errors, warnings)。"""
    errors: list[str] = []
    warnings: list[str] = []
    if not plugin_dir.is_dir():
        errors.append(f"目录不存在：{plugin_dir}")
        return errors, warnings

    init_path = plugin_dir / "__init__.py"
    if not init_path.is_file():
        errors.append("缺少 __init__.py")
        return errors, warnings

    text = init_path.read_text(encoding="utf-8")
    if "__plugin_meta__" not in text and "PluginMetadata" not in text:
        warnings.append("未找到 __plugin_meta__ / PluginMetadata，NoneBot 可能无法识别插件元数据")

    plugin_id = plugin_dir.name
    meta = read_plugin_metadata_from_init(init_path)
    if meta.get("plugin_id"):
        plugin_id = meta["plugin_id"]
    if not PLUGIN_ID_RE.fullmatch(plugin_id):
        errors.append(
            f"插件 ID「{plugin_id}」不符合规范（小写字母开头，仅字母数字下划线，最长 64）",
        )
    elif plugin_dir.name != plugin_id:
        warnings.append(
            f"目录名「{plugin_dir.name}」与 PLUGIN_ID「{plugin_id}」不一致，"
            f"安装到 local/plugins/ 时目录须为 {plugin_id}/",
        )

    if not any((plugin_dir / rel).is_file() for rel in ICON_ASSET_PATHS):
        warnings.append(
            "未找到 assets/icon.png 等图标文件；索引可省略 icon，Bot 会尝试推断 GitHub/Gitee raw URL",
        )

    readme_names = ("README.md", "readme.md", "Readme.md")
    if not any((plugin_dir / name).is_file() for name in readme_names):
        warnings.append("建议提供 README.md，便于商店详情页展示")

    # L1 import 检查（社区插件仅允许 pallas.api.*）
    import_errors = _validate_plugin_imports(plugin_dir)
    for err in import_errors:
        errors.append(f"L1 import 违规: {err}")

    return errors, warnings


def suggest_plugin_id_from_repo(repository_url: str) -> str | None:
    parsed = parse_git_host_repo(repository_url)
    if parsed is None:
        return None
    _, _, repo = parsed
    candidate = re.sub(r"[^a-z0-9_]", "_", repo.lower())
    candidate = re.sub(r"_+", "_", candidate).strip("_")
    if candidate and PLUGIN_ID_RE.fullmatch(candidate):
        return candidate
    if candidate:
        trimmed = candidate[:64]
        if PLUGIN_ID_RE.fullmatch(trimmed):
            return trimmed
    return None


def build_index_entry(
    *,
    plugin_id: str,
    name: str,
    description: str,
    repository: str,
    ref: str = "main",
    author: str = "",
    tags: list[str] | None = None,
    min_pallas_version: str = "4.0.0",
    icon: str | None = None,
    homepage: str | None = None,
) -> dict[str, Any]:
    pid = plugin_id.strip()
    repo = repository.strip()
    entry: dict[str, Any] = {
        "id": pid,
        "name": (name or pid).strip() or pid,
        "description": (description or "").strip(),
        "repository": repo,
        "ref": (ref or "main").strip() or "main",
        "author": (author or "").strip(),
        "tags": [str(t).strip() for t in (tags or []) if str(t).strip()],
        "min_pallas_version": (min_pallas_version or "").strip() or "4.0.0",
    }
    resolved_icon = (icon or "").strip() or infer_community_plugin_icon(repo, entry["ref"])
    if resolved_icon:
        entry["icon"] = resolved_icon
    if homepage and str(homepage).strip():
        entry["homepage"] = str(homepage).strip()
    return entry


def build_index_entry_from_dir(
    plugin_dir: Path,
    *,
    repository: str,
    ref: str = "main",
    author: str = "",
    tags: list[str] | None = None,
) -> dict[str, Any]:
    init_path = plugin_dir / "__init__.py"
    meta = read_plugin_metadata_from_init(init_path) if init_path.is_file() else {}
    plugin_id = meta.get("plugin_id") or plugin_dir.name
    return build_index_entry(
        plugin_id=plugin_id,
        name=meta.get("name") or plugin_id,
        description=meta.get("description") or "",
        repository=repository,
        ref=ref,
        author=author,
        tags=tags,
        homepage=meta.get("homepage"),
    )


def format_index_entry_json(entry: dict[str, Any], *, indent: int = 2) -> str:
    return json.dumps(entry, ensure_ascii=False, indent=indent) + "\n"


def validate_index_file(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]], list[str]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    meta, plugins = parse_index_document(raw)
    issues: list[str] = []
    for entry in plugins:
        pid = entry["plugin_id"]
        repo = entry.get("repository_url") or ""
        if not entry.get("icon") and parse_git_host_repo(str(repo)):
            issues.append(
                f"{pid}: 未设置 icon，将自动推断 {ICON_ASSET_PATHS[0]}（请确保仓库中存在该文件）",
            )
        normalized = normalize_index_entry(
            {
                "id": pid,
                "repository": repo,
                **{k: v for k, v in entry.items() if k not in {"plugin_id", "repository_url"}},
            },
        )
        if normalized is None:
            issues.append(f"{pid}: 条目无效")
    return meta, plugins, issues


def today_index_updated_at() -> str:
    return datetime.now(UTC).date().isoformat()

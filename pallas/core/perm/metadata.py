"""从 PluginMetadata.extra / 插件元数据桩解析 command_permissions 声明。"""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .registry import VALID_LEVELS

if TYPE_CHECKING:
    from pathlib import Path

    from nonebot.plugin import PluginMetadata


class CommandPermissionDecl(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    default: str = Field(min_length=1)


def parse_command_permission_decl(raw: dict[str, Any]) -> CommandPermissionDecl | None:
    try:
        item = dict(raw)
        if "id" not in item and "command_id" in item:
            item["id"] = item.pop("command_id")
        if "label" not in item and "name" in item:
            item["label"] = item.pop("name")
        if "default" not in item and "default_level" in item:
            item["default"] = item.pop("default_level")
        item["default"] = str(item.get("default") or "everyone").strip().lower()
        if item["default"] not in VALID_LEVELS:
            item["default"] = "everyone"
        return CommandPermissionDecl.model_validate(item)
    except (ValidationError, TypeError, ValueError):
        return None


def command_permissions_from_metadata(meta: PluginMetadata | None) -> list[CommandPermissionDecl]:
    if meta is None or not meta.extra:
        return []
    raw_list = meta.extra.get("command_permissions")
    if not isinstance(raw_list, list):
        return []
    out: list[CommandPermissionDecl] = []
    for raw in raw_list:
        if not isinstance(raw, dict):
            continue
        decl = parse_command_permission_decl(raw)
        if decl is not None:
            out.append(decl)
    return out


def parse_command_permissions_stub(init_path: Path) -> dict[str, Any] | None:
    """从插件 ``__init__.py`` 的 ``__plugin_meta__`` 字面量里提取名称与 command_permissions。"""
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
        if not any(isinstance(target, ast.Name) and target.id == "__plugin_meta__" for target in node.targets):
            continue
        if not isinstance(node.value, ast.Call):
            continue
        plugin_name = ""
        decls: list[CommandPermissionDecl] = []
        for kw in node.value.keywords:
            if kw.arg == "name" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                plugin_name = kw.value.value
            if kw.arg != "extra" or not isinstance(kw.value, ast.Dict):
                continue
            for key_node, value_node in zip(kw.value.keys, kw.value.values, strict=False):
                if not isinstance(key_node, ast.Constant) or key_node.value != "command_permissions":
                    continue
                if not isinstance(value_node, ast.List):
                    continue
                for item in value_node.elts:
                    if not isinstance(item, ast.Dict):
                        continue
                    raw: dict[str, Any] = {}
                    for ikey, ival in zip(item.keys, item.values, strict=False):
                        if not isinstance(ikey, ast.Constant) or not isinstance(ikey.value, str):
                            continue
                        if isinstance(ival, ast.Constant):
                            raw[ikey.value] = ival.value
                    decl = parse_command_permission_decl(raw)
                    if decl is not None:
                        decls.append(decl)
        if plugin_name or decls:
            return {"name": plugin_name, "command_permissions": decls}
    return None

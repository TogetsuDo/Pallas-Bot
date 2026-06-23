"""LLM tool 注册与执行。"""

from __future__ import annotations

import inspect
import operator
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from pallas.product.arknights_kb.config import get_arknights_kb_config
from pallas.product.llm.config import get_llm_config
from pallas.product.llm.tools.overrides import load_tool_description_overrides
from pallas.product.llm.tools.select import infer_tool_domains

if TYPE_CHECKING:
    from pallas.product.llm.tools.context import ToolInvokeContext

ToolHandler = Callable[..., dict[str, Any] | Awaitable[dict[str, Any]]]


class LlmToolSource(StrEnum):
    BUILTIN = "builtin"
    PLUGIN_COMMAND = "plugin_command"


@dataclass(frozen=True)
class LlmToolResult:
    ok: bool
    result: dict[str, Any] | None = None
    error: str = ""


@dataclass(frozen=True)
class LlmToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]
    domains: frozenset[str]
    handler: ToolHandler
    source: LlmToolSource = LlmToolSource.BUILTIN
    command_id: str | None = None
    visible_in_ui: bool = True


_REGISTRY: list[LlmToolSpec] = []
_REGISTERED_NAMES: set[str] = set()


def ensure_tools_loaded() -> None:
    from pallas.product.llm.tools.bootstrap import ensure_llm_tools_bootstrapped

    ensure_llm_tools_bootstrapped()


def clear_tool_registry() -> None:
    _REGISTRY.clear()
    _REGISTERED_NAMES.clear()


def register_tool(spec: LlmToolSpec) -> None:
    if spec.name in _REGISTERED_NAMES:
        return
    _REGISTRY.append(spec)
    _REGISTERED_NAMES.add(spec.name)


def iter_registered_tools(
    *,
    domains: frozenset[str] | None = None,
    source: LlmToolSource | None = None,
) -> tuple[LlmToolSpec, ...]:
    ensure_tools_loaded()
    items = tuple(_REGISTRY)
    if domains is not None:
        items = tuple(spec for spec in items if spec.domains.intersection(domains))
    if source is not None:
        items = tuple(spec for spec in items if spec.source == source)
    return items


def list_registered_tools() -> tuple[LlmToolSpec, ...]:
    return iter_registered_tools()


def trim_tool_description(description: str, *, max_len: int) -> str:
    text = (description or "").strip()
    if max_len <= 0 or len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


def normalize_tool_result(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        if "ok" in raw:
            return raw
        return {"ok": True, "result": raw}
    return {"ok": True, "result": {"value": raw}}


def tool_openai_schemas(*, domains: frozenset[str] | None = None) -> list[dict[str, Any]]:
    cfg = get_llm_config()
    if not cfg.llm_tools_enabled:
        return []
    ensure_tools_loaded()
    kb = get_arknights_kb_config()
    allowed = domains
    blacklist = {item.strip().lower() for item in cfg.llm_tools_blacklist if item.strip()}
    overrides = load_tool_description_overrides()
    out: list[dict[str, Any]] = []
    for spec in iter_registered_tools(domains=allowed):
        if blacklist:
            if spec.name.lower() in blacklist:
                continue
            if spec.domains.intersection(blacklist):
                continue
        if "arknights" in spec.domains and not kb.arknights_kb_enabled:
            continue
        description = trim_tool_description(spec.description, max_len=cfg.llm_tools_desc_max_len)
        override = overrides.get(spec.name)
        if isinstance(override, dict):
            custom = str(override.get("description") or "").strip()
            if custom:
                description = trim_tool_description(custom, max_len=cfg.llm_tools_desc_max_len)
        out.append({
            "type": "function",
            "function": {
                "name": spec.name,
                "description": description,
                "parameters": spec.parameters,
            },
        })
    return out


async def execute_tool_async(
    name: str,
    arguments: dict[str, Any] | None,
    *,
    context: ToolInvokeContext | None = None,
) -> dict[str, Any]:
    ensure_tools_loaded()
    args = arguments if isinstance(arguments, dict) else {}
    for spec in _REGISTRY:
        if spec.name != name:
            continue
        try:
            result = spec.handler(args, context)
            if inspect.isawaitable(result):
                result = await result
            return normalize_tool_result(result)
        except Exception as exc:
            return {"ok": False, "error": str(exc)}
    return {"ok": False, "error": f"unknown tool: {name}"}


def execute_tool(name: str, arguments: dict[str, Any] | None) -> dict[str, Any]:
    """同步入口（无群上下文）；命令类 tool 需走 execute_tool_async。"""
    import asyncio

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(execute_tool_async(name, arguments, context=None))
    msg = "execute_tool cannot run async command tools inside event loop; use execute_tool_async"
    raise RuntimeError(msg)


_NO_TOOL_TASKS = frozenset({"repeater_fallback", "repeater_polish", "repeater_polish_lite", "repeater_select", "drunk"})


def tool_metadata_for_chat(*, task: str | None = None, user_text: str = "") -> dict[str, Any]:
    """写入 AI 仓 metadata：tools_enabled + tool_schemas。"""
    normalized = str(task or "").strip().lower()
    if normalized in _NO_TOOL_TASKS:
        return {}
    cfg = get_llm_config()
    domains: frozenset[str] | None = None
    if cfg.llm_tools_selective:
        inferred = infer_tool_domains(user_text)
        if not inferred:
            return {}
        domains = inferred
    schemas = tool_openai_schemas(domains=domains)
    if not schemas:
        return {}
    return {"tools_enabled": True, "tool_schemas": schemas}


def build_tools_ui_rows() -> list[dict[str, Any]]:
    ensure_tools_loaded()
    rows = [
        {
            "name": spec.name,
            "description": spec.description,
            "domains": sorted(spec.domains),
            "command_id": spec.command_id,
            "source": spec.source.value,
        }
        for spec in iter_registered_tools()
        if spec.visible_in_ui
    ]
    rows.sort(key=operator.itemgetter("name"))
    return rows

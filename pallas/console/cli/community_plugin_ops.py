"""社区插件安装与可选重启。"""

from __future__ import annotations

from pallas.console.cli.bot_process import bot_lifecycle_available, schedule_bot_restart
from pallas.console.webui.community_plugin_install import (
    CommunityPluginInstallError,
    install_community_plugin,
    uninstall_community_plugin,
    update_community_plugin,
)


def append_restart_note(message: str, *, scheduled: bool) -> str:
    base = (message or "").strip()
    if scheduled:
        suffix = "已安排 Bot 重启。"
        return f"{base} {suffix}".strip() if base else suffix
    if base:
        return base
    return "请重启 Bot 后生效。"


async def install_community_plugin_with_options(
    plugin_id: str,
    *,
    repository_url: str,
    ref: str = "main",
    restart: bool = False,
) -> dict[str, str | bool]:
    result = await install_community_plugin(
        plugin_id,
        repository_url=repository_url,
        ref=ref,
    )
    scheduled = False
    if restart and bot_lifecycle_available():
        scheduled = schedule_bot_restart()
    result = dict(result)
    result["restart_scheduled"] = scheduled
    if restart or result.get("needs_restart"):
        result["message"] = append_restart_note(str(result.get("message") or ""), scheduled=scheduled)
    return result


async def update_community_plugin_with_options(
    plugin_id: str,
    *,
    ref: str = "main",
    restart: bool = False,
) -> dict[str, str | bool]:
    result = await update_community_plugin(plugin_id, ref=ref)
    scheduled = False
    if restart and bot_lifecycle_available():
        scheduled = schedule_bot_restart()
    result = dict(result)
    result["restart_scheduled"] = scheduled
    if restart or result.get("needs_restart"):
        result["message"] = append_restart_note(str(result.get("message") or ""), scheduled=scheduled)
    return result


async def uninstall_community_plugin_with_options(
    plugin_id: str,
    *,
    restart: bool = False,
) -> dict[str, str | bool]:
    result = await uninstall_community_plugin(plugin_id)
    scheduled = False
    if restart and bot_lifecycle_available():
        scheduled = schedule_bot_restart()
    result = dict(result)
    result["restart_scheduled"] = scheduled
    if restart or result.get("needs_restart"):
        result["message"] = append_restart_note(str(result.get("message") or ""), scheduled=scheduled)
    return result


__all__ = [
    "CommunityPluginInstallError",
    "install_community_plugin_with_options",
    "uninstall_community_plugin_with_options",
    "update_community_plugin_with_options",
]

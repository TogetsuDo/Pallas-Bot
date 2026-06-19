"""官方扩展安装与可选重启。"""

from __future__ import annotations

from pallas.console.cli.extension_activation import append_activation_note, append_activation_result
from pallas.console.webui.extension_install import (
    ExtensionInstallError,
    install_official_extension,
    uninstall_official_extension,
    update_official_extension,
)


async def install_official_extension_with_options(
    package: str,
    *,
    restart: bool = False,
) -> dict[str, str | bool]:
    result = await install_official_extension(package)
    result = append_activation_result(result, restart=restart)
    if restart or result.get("needs_restart"):
        result["message"] = append_activation_note(str(result.get("message") or ""), result)
    return result


async def update_official_extension_with_options(
    package: str,
    *,
    restart: bool = False,
) -> dict[str, str | bool]:
    result = await update_official_extension(package)
    result = append_activation_result(result, restart=restart)
    if restart or result.get("needs_restart"):
        result["message"] = append_activation_note(str(result.get("message") or ""), result)
    return result


async def uninstall_official_extension_with_options(
    package: str,
    *,
    restart: bool = False,
) -> dict[str, str | bool]:
    result = await uninstall_official_extension(package)
    result = append_activation_result(result, restart=restart)
    if restart or result.get("needs_restart"):
        result["message"] = append_activation_note(str(result.get("message") or ""), result)
    return result


__all__ = [
    "ExtensionInstallError",
    "install_official_extension_with_options",
    "uninstall_official_extension_with_options",
    "update_official_extension_with_options",
]

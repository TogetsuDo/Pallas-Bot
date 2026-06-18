import logging

from nonebot import get_app, get_driver, logger

from pallas.console.web import public_base_url
from pallas.console.webui.console_login import prime_shared_console_login

from .config import get_pallas_protocol_config, plugin_config, resolve_protocol_webui_base_path
from .data_dir import pb_protocol_data_dir
from .service import PallasProtocolService
from .web import register_pallas_protocol_routes

_registered = False
app = None
driver = None
manager: PallasProtocolService | None = None


def ensure_registered() -> None:
    global _registered, app, driver, manager
    if _registered:
        return
    app = get_app()
    driver = get_driver()
    manager = PallasProtocolService(pb_protocol_data_dir(), get_pallas_protocol_config())
    register_pallas_protocol_routes(app, manager=manager, plugin_config=plugin_config)
    driver.on_startup(pb_protocol_prime_console_login)
    driver.on_startup(pb_protocol_startup)
    driver.on_shutdown(pb_protocol_shutdown)
    _registered = True


async def pb_protocol_prime_console_login() -> None:
    prime_shared_console_login()


async def pb_protocol_startup() -> None:
    ensure_registered()
    if not plugin_config.pallas_protocol_enabled:
        return
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    assert manager is not None
    await manager.initialize()
    if plugin_config.pallas_protocol_webui_enabled:
        dconf = get_driver().config
        base_u = public_base_url(
            host=getattr(dconf, "host", None),
            port=getattr(dconf, "port", None),
        )
        path = resolve_protocol_webui_base_path(plugin_config)
        logger.info("协议端：{}{}/", base_u, path)
    profile = manager.runtime_profile()
    if bool(profile.get("follow_bot_lifecycle", True)):
        await manager.start_all_enabled_accounts()


async def pb_protocol_shutdown() -> None:
    ensure_registered()
    if not plugin_config.pallas_protocol_enabled:
        return
    assert manager is not None
    profile = manager.runtime_profile()
    if not bool(profile.get("follow_bot_lifecycle", True)):
        return
    await manager.stop_all_enabled_accounts()

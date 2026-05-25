"""Pallas-Bot 控制台 JSON API 前缀（如 /pallas/api）；健康检查等轻量路由可在此注册或再拆子路由。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from nonebot import __version__ as _nb_ver

from src.common.bot_version import get_pallas_bot_version_for_health

from .console_meta_store import get_console_meta, merge_console_version_from_disk


def register_api(
    app,
    *,
    api_base: str,
    extra_meta: dict[str, Any] | None = None,
) -> None:
    """api_base 为完整前缀，例如 /pallas/api 。"""
    x = (api_base or "/pallas/api").strip()
    if not x.startswith("/"):
        x = "/" + x
    x = x.rstrip("/")  # /pallas/api

    router = APIRouter(tags=["Pallas-Bot 控制台"])

    console_meta = dict(extra_meta or {})
    static_root = Path(str(console_meta.get("static_root", "")).strip()) if console_meta.get("static_root") else None
    merge_console_version_from_disk(console_meta, static_root)

    pallas_ver = get_pallas_bot_version_for_health()

    @router.get(f"{x}/health", include_in_schema=True)
    async def _health() -> JSONResponse:  # pragma: no cover - 路由注册
        # 每次请求重读 dist 内 console-version.json，避免 WebUI 在线更新后仍返回启动时快照
        live_console = {**console_meta, **get_console_meta()}
        merge_console_version_from_disk(live_console, static_root)
        return JSONResponse(
            {
                "ok": True,
                "nonebot2": str(_nb_ver),
                "pallas_bot": pallas_ver,
                "console": live_console,
            },
            status_code=status.HTTP_200_OK,
        )

    app.include_router(router)

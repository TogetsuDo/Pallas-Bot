from __future__ import annotations

import time
from typing import Any

import httpx
from nonebot import logger

from .types import ServiceProbeResult


def clamp_timeout_sec(timeout_sec: float, *, floor: float = 5.0, cap: float = 30.0) -> float:
    return min(cap, max(floor, timeout_sec))


async def probe_http_get(
    client: httpx.AsyncClient,
    *,
    category: str,
    site: str,
    url: str,
    headers: dict[str, str] | None = None,
    timeout_sec: float = 15.0,
) -> ServiceProbeResult:
    timeout = clamp_timeout_sec(timeout_sec)
    started = time.perf_counter()
    try:
        r = await client.get(
            url,
            headers=headers or {},
            timeout=httpx.Timeout(timeout, connect=min(15.0, timeout)),
        )
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        ok = 200 <= r.status_code < 300
        return ServiceProbeResult(
            category=category,
            site=site,
            ok=ok,
            latency_ms=elapsed_ms,
            status_code=r.status_code,
            error=None if ok else None,
        )
    except httpx.TimeoutException:
        return ServiceProbeResult(category, site, False, None, None, "超时")
    except httpx.ConnectError:
        return ServiceProbeResult(category, site, False, None, None, "连接失败")
    except Exception as e:  # noqa: BLE001
        logger.debug("service_probe GET {} {}: {}", category, site, e)
        return ServiceProbeResult(category, site, False, None, None, str(e)[:120])


async def probe_http_post_json(
    client: httpx.AsyncClient,
    *,
    category: str,
    site: str,
    url: str,
    json_body: dict[str, Any],
    headers: dict[str, str] | None = None,
    timeout_sec: float = 15.0,
) -> ServiceProbeResult:
    timeout = clamp_timeout_sec(timeout_sec)
    hdrs = {"Content-Type": "application/json", **(headers or {})}
    started = time.perf_counter()
    try:
        r = await client.post(
            url,
            json=json_body,
            headers=hdrs,
            timeout=httpx.Timeout(timeout, connect=min(15.0, timeout)),
        )
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        ok = 200 <= r.status_code < 300
        return ServiceProbeResult(
            category=category,
            site=site,
            ok=ok,
            latency_ms=elapsed_ms,
            status_code=r.status_code,
            error=None,
        )
    except httpx.TimeoutException:
        return ServiceProbeResult(category, site, False, None, None, "超时")
    except httpx.ConnectError:
        return ServiceProbeResult(category, site, False, None, None, "连接失败")
    except Exception as e:  # noqa: BLE001
        logger.debug("service_probe POST {} {}: {}", category, site, e)
        return ServiceProbeResult(category, site, False, None, None, str(e)[:120])

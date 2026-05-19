from __future__ import annotations

import asyncio
from typing import Any
from urllib.parse import urljoin

import httpx

from src.common.service_probe import ServiceProbeResult, probe_http_get, probe_http_post_json
from src.common.webui.gateway_fields import (
    ALL_GATEWAY_FIELDS,
    MAA_GATEWAY_FIELDS,
    PALLAS_IMAGE_GATEWAY_FIELDS,
    SING_GATEWAY_FIELDS,
)
from src.plugins.maa.config import Config as MaaConfig
from src.plugins.maa.config import get_maa_config
from src.plugins.maa.endpoints import resolve_maa_http_endpoints
from src.plugins.pallas_image.gateway_probe import image_gen_settings_from_draft, probe_all_backends
from src.plugins.sing.config import Config as SingConfig
from src.plugins.sing.config import get_sing_config, sing_server_url

MAA_CATEGORY = "MAA远控"
SING_CATEGORY = "唱歌"


async def probe_maa_endpoints(
    *,
    cfg: MaaConfig | None = None,
    timeout_sec: float = 15.0,
) -> list[ServiceProbeResult]:
    ep = resolve_maa_http_endpoints(cfg)
    probe_body = {"user": "", "device": ""}
    report_body = {"user": "", "device": "", "task": "", "status": "", "payload": ""}
    async with httpx.AsyncClient() as client:
        get_r, report_r = await asyncio.gather(
            probe_http_post_json(
                client,
                category=MAA_CATEGORY,
                site="获取任务",
                url=ep.get_task_url,
                json_body=probe_body,
                timeout_sec=timeout_sec,
            ),
            probe_http_post_json(
                client,
                category=MAA_CATEGORY,
                site="汇报任务",
                url=ep.report_status_url,
                json_body=report_body,
                timeout_sec=timeout_sec,
            ),
        )
    return [get_r, report_r]


def sing_probe_urls(base: str, request_endpoint: str) -> list[tuple[str, str]]:
    root = base.rstrip("/")
    req_path = (request_endpoint or "").strip()
    if not req_path.startswith("/"):
        req_path = f"/{req_path}" if req_path else "/"
    seen: set[str] = set()
    out: list[tuple[str, str]] = []
    for site, path in (("根路径", ""), ("请求接口", req_path)):
        url = urljoin(f"{root}/", path.lstrip("/")) if path else root
        if url not in seen:
            seen.add(url)
            out.append((site, url))
    return out


async def probe_sing_server(
    *,
    cfg: SingConfig | None = None,
    timeout_sec: float = 15.0,
) -> list[ServiceProbeResult]:
    cfg = cfg or get_sing_config()
    if not cfg.sing_enable:
        return [
            ServiceProbeResult(
                category=SING_CATEGORY,
                site="服务",
                ok=False,
                latency_ms=None,
                status_code=None,
                error="未启用 sing_enable",
            ),
        ]
    base = sing_server_url(cfg)
    urls = sing_probe_urls(base, cfg.request_endpoint)
    async with httpx.AsyncClient() as client:
        for site, url in urls:
            result = await probe_http_get(
                client,
                category=SING_CATEGORY,
                site=site,
                url=url,
                timeout_sec=timeout_sec,
            )
            if result.ok:
                return [result]
        if urls:
            site, url = urls[-1]
            return [
                await probe_http_get(
                    client,
                    category=SING_CATEGORY,
                    site=site,
                    url=url,
                    timeout_sec=timeout_sec,
                ),
            ]
    return [
        ServiceProbeResult(
            category=SING_CATEGORY,
            site="服务",
            ok=False,
            latency_ms=None,
            status_code=None,
            error="未配置",
        ),
    ]


async def probe_all_connectivity(*, timeout_sec: float = 15.0) -> list[ServiceProbeResult]:
    image_task = probe_all_backends()
    maa_task = probe_maa_endpoints(timeout_sec=timeout_sec)
    sing_task = probe_sing_server(timeout_sec=timeout_sec)
    image_results, maa_results, sing_results = await asyncio.gather(image_task, maa_task, sing_task)
    return [*image_results, *maa_results, *sing_results]


def _draft_subset(values: dict[str, Any], keys: frozenset[str]) -> dict[str, Any]:
    return {k: v for k, v in values.items() if k in keys}


def _pallas_image_draft(values: dict[str, Any]) -> dict[str, Any]:
    from src.plugins.pallas_image.config import get_pallas_image_config

    base = get_pallas_image_config().model_dump(mode="python")
    base.update(_draft_subset(values, PALLAS_IMAGE_GATEWAY_FIELDS))
    return base


def _maa_cfg_from_draft(values: dict[str, Any]) -> MaaConfig:
    base = get_maa_config().model_dump(mode="python")
    base.update(_draft_subset(values, MAA_GATEWAY_FIELDS))
    return MaaConfig.model_validate(base)


def _sing_cfg_from_draft(values: dict[str, Any]) -> SingConfig:
    base = get_sing_config().model_dump(mode="python")
    base.update(_draft_subset(values, SING_GATEWAY_FIELDS))
    return SingConfig.model_validate(base)


async def probe_all_connectivity_from_draft(
    values: dict[str, Any] | None = None,
    *,
    timeout_sec: float = 15.0,
) -> list[ServiceProbeResult]:
    raw = values or {}
    if not raw:
        return await probe_all_connectivity(timeout_sec=timeout_sec)
    unknown = set(raw.keys()) - ALL_GATEWAY_FIELDS
    if unknown:
        raise ValueError(f"未知配置项: {', '.join(sorted(unknown))}")
    image_task = probe_all_backends(image_gen_settings_from_draft(_pallas_image_draft(raw)))
    maa_task = probe_maa_endpoints(cfg=_maa_cfg_from_draft(raw), timeout_sec=timeout_sec)
    sing_task = probe_sing_server(cfg=_sing_cfg_from_draft(raw), timeout_sec=timeout_sec)
    image_results, maa_results, sing_results = await asyncio.gather(image_task, maa_task, sing_task)
    return [*image_results, *maa_results, *sing_results]

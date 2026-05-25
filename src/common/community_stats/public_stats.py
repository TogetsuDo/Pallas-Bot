"""拉取社区统计中心公开聚合指标（供控制台代理）。"""

from __future__ import annotations

from typing import Any

import httpx
from nonebot import logger

from src.common.community_stats.config import get_community_stats_config
from src.common.community_stats.endpoints import monitor_overview_urls_for_config, stats_urls_for_config
from src.common.message_scrub.quiet_http_loggers import scrub_http_log_noise

_HTTP_TIMEOUT_SEC = 12.0
_REQUIRED_KEYS = ("deployments_total", "deployments_online", "bots_online_sum")
_CORPUS_KEYS = (
    "contexts_total",
    "answers_total",
    "enrollments_total",
    "contribute_enabled_total",
    "answer_hits_sum",
    "enrollments_online",
    "enrollments_recent_24h",
    "read_enabled_total",
)
_DEPLOYMENT_EXTRA_KEYS = (
    "catalog_bots_online_sum",
    "active_recent_24h",
)


def _parse_corpus_block(corpus_raw: Any) -> dict[str, int] | None:
    if not isinstance(corpus_raw, dict):
        return None
    corpus_out: dict[str, int] = {}
    for key in _CORPUS_KEYS:
        if key in corpus_raw:
            corpus_out[key] = int(corpus_raw[key])
    return corpus_out or None


def _parse_stats_body(body: Any, stats_url: str) -> dict[str, Any]:
    if not isinstance(body, dict):
        raise ValueError("stats response is not a JSON object")

    deployments_raw = body.get("deployments") if isinstance(body.get("deployments"), dict) else body
    if not isinstance(deployments_raw, dict):
        raise ValueError("stats response missing deployments block")

    missing = [k for k in _REQUIRED_KEYS if k not in deployments_raw]
    if missing:
        raise ValueError(f"stats response missing fields: {', '.join(missing)}")

    out: dict[str, Any] = {
        "deployments_total": int(deployments_raw["deployments_total"]),
        "deployments_online": int(deployments_raw["deployments_online"]),
        "bots_online_sum": int(deployments_raw["bots_online_sum"]),
        "stats_url": stats_url,
    }
    ttl = body.get("online_ttl_sec", deployments_raw.get("online_ttl_sec"))
    if ttl is not None:
        out["online_ttl_sec"] = int(ttl)
    as_of = body.get("as_of")
    if isinstance(as_of, str):
        out["as_of"] = as_of
    for key in ("deployments_online_sharded", "shard_workers_online_sum"):
        if key in deployments_raw:
            out[key] = int(deployments_raw[key])
    for key in _DEPLOYMENT_EXTRA_KEYS:
        if key in deployments_raw:
            out[key] = int(deployments_raw[key])
    versions = deployments_raw.get("online_versions")
    if isinstance(versions, list):
        out["online_versions"] = [
            {"version": str(item["version"]), "count": int(item["count"])}
            for item in versions
            if isinstance(item, dict) and "version" in item and "count" in item
        ]
    corpus_raw = body.get("corpus")
    corpus_out = _parse_corpus_block(corpus_raw)
    if corpus_out:
        out["corpus"] = corpus_out
    if "corpus_enabled" in body:
        out["corpus_enabled"] = bool(body["corpus_enabled"])
    return out


async def _fetch_from_urls(urls: list[str]) -> dict[str, Any]:
    scrub_http_log_noise()
    last_err: Exception | None = None
    async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT_SEC) as client:
        for stats_url in urls:
            try:
                resp = await client.get(stats_url)
                resp.raise_for_status()
                return _parse_stats_body(resp.json(), stats_url)
            except (httpx.HTTPError, ValueError) as e:
                last_err = e
                logger.debug("community_stats: fetch stats failed url={}: {}", stats_url, e)
    if last_err is not None:
        raise last_err
    raise ValueError("community stats fetch failed")


async def fetch_community_public_stats() -> dict[str, Any]:
    cfg = get_community_stats_config()
    monitor_urls = monitor_overview_urls_for_config(cfg)
    stats_urls = stats_urls_for_config(cfg)
    if not monitor_urls and not stats_urls:
        raise ValueError("no community stats URL configured")
    try:
        data = await _fetch_from_urls(monitor_urls)
    except Exception as monitor_err:
        if not stats_urls:
            raise monitor_err
        logger.debug("community_stats: monitor overview unavailable, fallback to /v1/stats: {}", monitor_err)
        data = await _fetch_from_urls(stats_urls)
    logger.debug(
        "community stats fetched: total={} online={} bots_sum={} url={}",
        data["deployments_total"],
        data["deployments_online"],
        data["bots_online_sum"],
        data.get("stats_url"),
    )
    return data

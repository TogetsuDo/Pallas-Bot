"""拉取社区统计中心公开聚合指标（供控制台代理）。"""

from __future__ import annotations

from typing import Any

import httpx
from nonebot import logger

from src.common.community_stats.config import get_community_stats_config
from src.common.community_stats.endpoints import stats_urls_for_config
from src.common.community_stats.history_store import record_stats_snapshot
from src.common.message_scrub.quiet_http_loggers import scrub_http_log_noise

_HTTP_TIMEOUT_SEC = 12.0
_REQUIRED_KEYS = ("deployments_total", "deployments_online", "bots_online_sum")


def _parse_stats_body(body: Any, stats_url: str) -> dict[str, Any]:
    if not isinstance(body, dict):
        raise ValueError("stats response is not a JSON object")
    missing = [k for k in _REQUIRED_KEYS if k not in body]
    if missing:
        raise ValueError(f"stats response missing fields: {', '.join(missing)}")
    out: dict[str, Any] = {
        "deployments_total": int(body["deployments_total"]),
        "deployments_online": int(body["deployments_online"]),
        "bots_online_sum": int(body["bots_online_sum"]),
        "stats_url": stats_url,
    }
    if "online_ttl_sec" in body:
        out["online_ttl_sec"] = int(body["online_ttl_sec"])
    if isinstance(body.get("as_of"), str):
        out["as_of"] = body["as_of"]
    for key in ("deployments_online_sharded", "shard_workers_online_sum"):
        if key in body:
            out[key] = int(body[key])
    corpus_raw = body.get("corpus")
    if isinstance(corpus_raw, dict):
        corpus_out: dict[str, int] = {}
        for key in (
            "contexts_total",
            "answers_total",
            "enrollments_total",
            "contribute_enabled_total",
        ):
            if key in corpus_raw:
                corpus_out[key] = int(corpus_raw[key])
        if corpus_out:
            out["corpus"] = corpus_out
    return out


async def fetch_community_public_stats() -> dict[str, Any]:
    cfg = get_community_stats_config()
    urls = stats_urls_for_config(cfg)
    if not urls:
        raise ValueError("no community stats URL configured")
    scrub_http_log_noise()
    last_err: Exception | None = None
    async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT_SEC) as client:
        for stats_url in urls:
            try:
                resp = await client.get(stats_url)
                resp.raise_for_status()
                data = _parse_stats_body(resp.json(), stats_url)
                logger.debug(
                    "community stats fetched: total={} online={} bots_sum={} url={}",
                    data["deployments_total"],
                    data["deployments_online"],
                    data["bots_online_sum"],
                    stats_url,
                )
                record_stats_snapshot(data)
                return data
            except (httpx.HTTPError, ValueError) as e:
                last_err = e
                logger.debug("community_stats: fetch stats failed url={}: {}", stats_url, e)
    if last_err is not None:
        raise last_err
    raise ValueError("community stats fetch failed")

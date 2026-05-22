"""组装心跳负载并 POST 至社区统计中心。"""

from __future__ import annotations

import time

import httpx
from nonebot import logger

from src.common.bot_runtime.roles import is_sharded_worker
from src.common.cmd_perm.metadata_defaults import PLUGIN_EXTRA_VERSION
from src.common.community_stats.config import CommunityStatsConfig, get_community_stats_config
from src.common.community_stats.store import load_or_create_deployment_id
from src.common.message_scrub.quiet_http_loggers import scrub_http_log_noise
from src.common.multi_bot.fleet import get_fleet_bot_ids
from src.common.shard.registry.config import is_sharding_active
from src.common.shard.registry.store import get_shard_registry, is_test_shard_record

_HTTP_TIMEOUT_SEC = 15.0


def should_run_community_stats_reporter() -> bool:
    if is_sharded_worker():
        return False
    return get_community_stats_config().enabled


def build_heartbeat_payload() -> dict[str, object]:
    from src.common.shard.presence import count_connected_bots_for_reporting

    online_bots = count_connected_bots_for_reporting()
    catalog_bots = len(get_fleet_bot_ids())
    sharded = is_sharding_active()
    shard_workers = 0
    if sharded:
        reg = get_shard_registry()
        shard_workers = len([s for s in reg.shards if not is_test_shard_record(s, reg)])
    return {
        "deployment_id": load_or_create_deployment_id(),
        "ts": int(time.time()),
        "version": PLUGIN_EXTRA_VERSION,
        "online_bots": online_bots,
        "catalog_bots": catalog_bots,
        "sharded": sharded,
        "shard_workers": shard_workers if sharded else None,
    }


def _headers(cfg: CommunityStatsConfig) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    token = (cfg.token or "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


async def send_community_stats_heartbeat() -> bool:
    cfg = get_community_stats_config()
    endpoint = (cfg.endpoint or "").strip()
    if not endpoint:
        logger.warning("community_stats: endpoint 为空，跳过上报")
        return False
    payload = build_heartbeat_payload()
    try:
        async with scrub_http_log_noise():
            async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT_SEC) as client:
                resp = await client.post(endpoint, json=payload, headers=_headers(cfg))
        if resp.status_code == 200:
            logger.debug("community_stats: heartbeat ok deployment_id={}", payload["deployment_id"])
            return True
        if resp.status_code == 429:
            logger.warning("community_stats: heartbeat rate limited (429)")
        else:
            logger.warning(
                "community_stats: heartbeat HTTP {} body={}",
                resp.status_code,
                (resp.text or "")[:200],
            )
    except httpx.HTTPError as e:
        logger.warning(f"community_stats: heartbeat failed: {e}")
    return False

"""启动时注册社区统计周期心跳。"""

from __future__ import annotations

from nonebot import logger
from nonebot_plugin_apscheduler import scheduler

from src.common.community_stats.config import get_community_stats_config
from src.common.community_stats.reporter import send_community_stats_heartbeat, should_run_community_stats_reporter

_JOB_ID = "community_stats_heartbeat"


async def start_community_stats_reporter() -> None:
    if not should_run_community_stats_reporter():
        return
    cfg = get_community_stats_config()
    if scheduler.get_job(_JOB_ID):
        scheduler.remove_job(_JOB_ID)
    await send_community_stats_heartbeat()
    scheduler.add_job(
        send_community_stats_heartbeat,
        trigger="interval",
        seconds=max(60, int(cfg.interval_sec)),
        id=_JOB_ID,
        replace_existing=True,
        coalesce=True,
        max_instances=1,
        misfire_grace_time=120,
    )
    logger.info(
        "community_stats: 已启用周期上报 interval_sec={} endpoint={}",
        cfg.interval_sec,
        (cfg.endpoint or "").strip(),
    )

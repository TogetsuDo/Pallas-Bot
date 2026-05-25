"""启动时注册社区统计周期心跳。"""

from __future__ import annotations

from datetime import datetime, timedelta

from nonebot import logger
from nonebot_plugin_apscheduler import scheduler

from src.common.community_stats.config import get_community_stats_config
from src.common.community_stats.reporter import send_community_stats_heartbeat, should_run_community_stats_reporter

_JOB_ID = "community_stats_heartbeat"
# 启动瞬间牛牛常未写入 presence/get_bots，推迟首包避免中心长期显示 online_bots=0
_FIRST_HEARTBEAT_DELAY_SEC = 60


async def start_community_stats_reporter() -> None:
    if not should_run_community_stats_reporter():
        return
    cfg = get_community_stats_config()
    if scheduler.get_job(_JOB_ID):
        scheduler.remove_job(_JOB_ID)
    interval_sec = max(60, int(cfg.interval_sec))
    scheduler.add_job(
        send_community_stats_heartbeat,
        trigger="interval",
        seconds=interval_sec,
        id=_JOB_ID,
        replace_existing=True,
        coalesce=True,
        max_instances=1,
        misfire_grace_time=120,
        next_run_time=datetime.now() + timedelta(seconds=_FIRST_HEARTBEAT_DELAY_SEC),
    )
    logger.info(
        "community_stats: 已启用周期上报 interval_sec={} first_after_sec={} endpoint={}",
        interval_sec,
        _FIRST_HEARTBEAT_DELAY_SEC,
        (cfg.endpoint or "").strip(),
    )


async def reload_community_stats_reporter() -> None:
    from src.common.community_stats.config import clear_community_stats_config_cache

    clear_community_stats_config_cache()
    if scheduler.get_job(_JOB_ID):
        scheduler.remove_job(_JOB_ID)
    if should_run_community_stats_reporter():
        await start_community_stats_reporter()
    else:
        logger.info("community_stats: 已关闭周期上报（配置热重载）")


def schedule_reload_community_stats_reporter() -> None:
    import asyncio

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(reload_community_stats_reporter())
    except RuntimeError:
        import asyncio as aio

        aio.run(reload_community_stats_reporter())

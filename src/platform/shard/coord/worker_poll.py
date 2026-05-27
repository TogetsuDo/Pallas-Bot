"""分片 worker：统一轮询 coord 目录（QTE、代发动作等）。"""

from __future__ import annotations

import asyncio

from nonebot import logger

from src.platform.shard.registry.config import get_shard_registry_settings, is_sharding_active

_WATCH_SEC = 0.28
_PRUNE_EVERY = 8
_started = False


def coord_dirs_have_pending_json() -> bool:
    """存在待处理 coord 请求时再做 QTE/代发轮询，降低空转。"""
    from pathlib import Path

    from src.foundation.paths import plugin_data_dir

    root = Path(plugin_data_dir("pallas_shard", create=False)) / "coord"
    if not root.is_dir():
        return False
    for sub in ("bot_action", "duel_qte", "repeater_buffer"):
        d = root / sub
        if d.is_dir() and any(d.glob("*.json")):
            return True
    return False


async def shard_coord_worker_poll_loop() -> None:
    from nonebot import get_bots

    from src.platform.shard.coord.bot_action import poll_bot_action_pending, prune_stale_bot_action_files
    from src.platform.shard.coord.bot_count import prune_stale_bot_count_files
    from src.platform.shard.coord.cage_duel import prune_stale_cage_duel_files
    from src.platform.shard.coord.duel_group import prune_stale_duel_group_files
    from src.platform.shard.coord.duel_qte import poll_duel_qte_pending, prune_stale_duel_qte_files
    from src.platform.shard.coord.maa_pending_registry import prune_stale_maa_pending_files
    from src.platform.shard.coord.maa_seen_registry import prune_stale_maa_seen_files
    from src.platform.shard.coord.repeater_buffer import (
        poll_repeater_buffer_pending,
        prune_stale_repeater_buffer_files,
    )

    tick = 0
    while True:
        try:
            if is_sharding_active():
                local_ids = frozenset(get_bots().keys())
                if local_ids:
                    await poll_bot_action_pending(local_ids)
                    try:
                        await poll_repeater_buffer_pending()
                    except Exception as buf_err:
                        logger.debug(f"shard_coord repeater_buffer poll: {buf_err}")
                    if coord_dirs_have_pending_json():
                        await poll_duel_qte_pending(local_ids)
                tick += 1
                if tick >= _PRUNE_EVERY:
                    tick = 0
                    await prune_stale_duel_qte_files()
                    await prune_stale_bot_action_files()
                    await prune_stale_repeater_buffer_files()
                    await prune_stale_cage_duel_files()
                    await prune_stale_bot_count_files()
                    await prune_stale_duel_group_files()
                    await prune_stale_maa_seen_files()
                    await prune_stale_maa_pending_files()
        except Exception as err:
            logger.debug(f"shard_coord worker poll: {err}")
        await asyncio.sleep(_WATCH_SEC)


def start_shard_coord_worker_watcher() -> None:
    global _started
    if _started or not is_sharding_active():
        return
    if get_shard_registry_settings().role != "worker":
        return
    from src.platform.shard.coord.repeater_buffer import start_repeater_buffer_redis_listener

    _started = True
    start_repeater_buffer_redis_listener()
    asyncio.create_task(shard_coord_worker_poll_loop())


def start_duel_qte_coord_watcher() -> None:
    """兼容旧入口。"""
    start_shard_coord_worker_watcher()

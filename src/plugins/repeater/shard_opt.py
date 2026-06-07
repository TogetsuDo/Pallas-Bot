"""分片 worker 下复读插件的运行时优化（代表牛、fanout 条件）。"""

from __future__ import annotations


def repeater_worker_handles_message(bot_id: int) -> bool:
    """群消息入口统一放开到本 worker 本地牛，由后续去重/claim 收敛到单牛或 fanout。"""
    from src.platform.shard.registry.config import is_sharding_active

    if not is_sharding_active():
        return True
    return True


def repeater_scheduler_runs_on_worker() -> bool:
    """主动发言定时任务：分片时仅代表牛所在 worker 执行，减少重复扫描。"""
    from src.platform.shard.registry.config import is_sharding_active

    if not is_sharding_active():
        return True
    from src.platform.shard.local_representative import local_worker_representative_bot_id

    return local_worker_representative_bot_id() is not None

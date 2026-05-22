#!/usr/bin/env python3
"""一次性清理 coord 陈旧 JSON（bot_action / duel_qte 等）。分片运行时可在 hub 或运维机执行。"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def prune_all_done_bot_action() -> int:
    from src.common.shard.coord.bot_action import _coord_dir, _read

    removed = 0
    for path in _coord_dir().glob("*.json"):
        if ".lock" in path.name:
            continue
        row = _read(path)
        if isinstance(row, dict) and row.get("done"):
            try:
                path.unlink(missing_ok=True)
                removed += 1
            except OSError:
                pass
    return removed


async def main() -> int:
    parser = argparse.ArgumentParser(description="清理 data/pallas_shard/coord 陈旧 JSON")
    parser.add_argument(
        "--purge-done",
        action="store_true",
        help="删除全部 bot_action done 文件（运维一次性减压，不影响进行中的 open）",
    )
    args = parser.parse_args()
    from src.common.shard.coord.bot_action import prune_stale_bot_action_files
    from src.common.shard.coord.cage_duel import prune_stale_cage_duel_files
    from src.common.shard.coord.duel_qte import prune_stale_duel_qte_files
    from src.common.shard.coord.repeater_buffer import prune_stale_repeater_buffer_files
    from src.common.shard.coord_pending import coord_pending_snapshot_sync

    before = coord_pending_snapshot_sync()
    purged_done = prune_all_done_bot_action() if args.purge_done else 0
    bot_stats = await prune_stale_bot_action_files()
    if purged_done:
        bot_stats["purged_all_done"] = purged_done
    await prune_stale_duel_qte_files()
    await prune_stale_repeater_buffer_files()
    await prune_stale_cage_duel_files()
    after = coord_pending_snapshot_sync()
    out = {"before": before, "bot_action": bot_stats, "after": after}
    json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

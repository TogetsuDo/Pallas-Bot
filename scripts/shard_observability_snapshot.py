#!/usr/bin/env python3
"""打印分片可观测快照（ingress 命中率、coord 积压、PG 池粗算）。Hub 或运维机执行。"""

from __future__ import annotations

import json
import sys

from src.common.shard.observability import aggregate_shard_observability


def main() -> int:
    data = aggregate_shard_observability()
    json.dump(data, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

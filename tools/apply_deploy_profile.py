#!/usr/bin/env python3
"""应用 ``deploy/`` 下的可选部署模板（合并配置片段并记录落盘标记）。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.foundation.config.repo_settings import repo_config_path  # noqa: E402
from src.foundation.deploy_profile import (  # noqa: E402
    DEPLOY_PROFILES,
    merge_profile_env_into_webui,
    read_profile_env_fragment,
    record_deploy_profile,
    uv_sync_hint_for_profile,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "profile",
        choices=sorted(DEPLOY_PROFILES.keys()),
        help="部署模板 id",
    )
    parser.add_argument("--dry-run", action="store_true", help="只打印将写入的 env 键与 uv 命令")
    args = parser.parse_args()

    if args.profile == "default":
        print("default 模板无需应用；直接使用 uv sync 与 bot.py 即可。")
        return 0

    if not repo_config_path().is_file():
        print(
            "未找到 config/pallas.toml。请先: cp config/pallas.example.toml config/pallas.toml",
            file=sys.stderr,
        )
        return 1

    env_patch = read_profile_env_fragment(args.profile)
    if not env_patch:
        print(f"模板 {args.profile!r} 无 env 片段可合并。", file=sys.stderr)
        return 1

    hint = uv_sync_hint_for_profile(args.profile)
    print(f"建议依赖: {hint}")
    print(f"将合并 {len(env_patch)} 个 env 键到 data/pallas_config/webui.json")

    if args.dry_run:
        for k in sorted(env_patch):
            print(f"  {k}={env_patch[k]!r}")
        return 0

    webui_path = merge_profile_env_into_webui(env_patch)
    marker = record_deploy_profile(args.profile)
    print(f"已写入 {webui_path.relative_to(REPO_ROOT)}")
    print(f"已记录 {marker['profiles']}（extras: {marker['extras']}）")

    if args.profile == "shard":
        print("下一步: ./scripts/run_sharded_bot.sh start")
    elif args.profile == "message-scrub":
        print("下一步: 重启 Bot；在 WebUI「通用配置 → 消息审查」填写词表或审查 API。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env bash
# PostgreSQL 逻辑备份（委托 backup_pg.py，使用仓库 PG_* / pallas.toml 配置）
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
if command -v uv >/dev/null 2>&1; then
  exec uv run python tools/scripts/backup_pg.py "$@"
fi
exec python tools/scripts/backup_pg.py "$@"

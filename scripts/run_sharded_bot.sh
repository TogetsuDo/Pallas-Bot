#!/usr/bin/env bash
# Pallas-Bot 分片一键启停：1 个控制台 (hub) + 多个牛牛进程 (worker)
#
#   ./scripts/run_sharded_bot.sh start
#   ./scripts/run_sharded_bot.sh status
#   ./scripts/run_sharded_bot.sh stop
#   ./scripts/run_sharded_bot.sh restart

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

RUN_DIR="${REPO_ROOT}/data/pallas_shard/run"
LOG_DIR="${REPO_ROOT}/data/pallas_shard/logs"
PID_HUB="${RUN_DIR}/hub.pid"
ACCOUNTS_JSON="${REPO_ROOT}/data/pallas_protocol/accounts.json"
REGISTRY_JSON="${REPO_ROOT}/data/pallas_shard/registry.json"

BOTS_PER_SHARD="${PALLAS_SHARD_BOTS_PER:-5}"
HUB_PORT="${PALLAS_SHARD_HUB_PORT:-${PORT:-8088}}"
WORKER_BASE_PORT="${PALLAS_SHARD_WORKER_BASE_PORT:-8090}"
WORKER_COUNT_OVERRIDE=""
DRY_RUN=0
SKIP_PORT_SYNC=0
SKIP_OCCUPIED_PORTS=1
START_CMD=(uv run python)
SYNC_PORTS_SCRIPT="${SCRIPT_DIR}/sync_shard_protocol_ports.py"
ALLOC_PORTS_SCRIPT="${SCRIPT_DIR}/apply_shard_worker_ports.py"
STARTUP_PORTS_SCRIPT="${SCRIPT_DIR}/shard_startup_ports.py"
WAIT_PORTS_SCRIPT="${SCRIPT_DIR}/wait_shard_worker_ports.py"
SHARD_TEST_SCRIPT="${SCRIPT_DIR}/shard_test_worker.py"
DETECT_REDIS_SCRIPT="${SCRIPT_DIR}/detect_shard_redis.py"
PORT_RELEASE_TIMEOUT="${PALLAS_SHARD_PORT_RELEASE_TIMEOUT:-60}"
PID_WORKER_TEST="${RUN_DIR}/worker-test.pid"
TEST_SHARD_ID="${PALLAS_SHARD_TEST_ID:-99}"

print_rule() {
  echo "────────────────────────────────────────────────────────"
}

print_title() {
  echo ""
  echo "  $*"
  print_rule
}

usage() {
  cat <<EOF

用法:  ./scripts/run_sharded_bot.sh <命令> [选项]

命令:
  start     启动控制台与全部牛牛 worker（后台运行）
  stop      停止全部分片进程
  status    查看各进程是否在运行、对应端口
  restart   先 stop 再 start

测试 worker（手动迁入账号，不参与自动负载）:
  test init              在 registry 中启用 test 分片并分配端口
  test add <QQ>          将 QQ 迁入测试分片（可加 --sync-ws）
  test remove <QQ>       从测试分片移除
  test list              列出测试分片账号
  test sync-ws           同步测试账号协议端 ws_url
  test start|stop|status|restart   仅启停测试 worker 进程（worker-test）

常用示例:
  ./scripts/run_sharded_bot.sh start
  ./scripts/run_sharded_bot.sh status
  ./scripts/run_sharded_bot.sh restart
  ./scripts/run_sharded_bot.sh test init
  ./scripts/run_sharded_bot.sh test add 123456789 --sync-ws
  ./scripts/run_sharded_bot.sh test start

选项:
  --workers N          指定 worker 数量（默认按已启用牛牛账号自动计算）
  --bots-per-shard N   每个 worker 承载的牛牛数量（默认 5）
  --hub-port PORT      控制台 HTTP 端口（默认读 .env 的 PORT，否则 8088）
  --worker-base PORT   第一个 worker 的 WS 端口（默认 8090，依次为 8091、8092…）
  --skip-port-sync     启动前不自动改写协议端里的反向 WS 地址
  --no-skip-occupied-ports
                       worker 严格使用 起点+N，不自动避开已占用端口
  --dry-run            只显示将要执行的命令，不真正启动
  -h, --help           显示本帮助

启动后可在浏览器打开（将 PORT 换成你的 hub 端口）:
  WebUI    http://127.0.0.1:PORT/pallas/
  协议端   http://127.0.0.1:PORT/protocol/console/

运行日志目录: data/pallas_shard/logs/  （WebUI 日志页可查看各 worker）

EOF
}

load_shard_redis_env() {
  # 与 Pallas-Bot-AI 共用 REDIS_URL 时自动启用跨进程 claim（不可达则回退文件）
  if [[ ! -f "${DETECT_REDIS_SCRIPT}" ]]; then
    return 0
  fi
  while IFS= read -r line; do
    [[ -n "${line}" ]] || continue
    export "${line?}"
  done < <("${START_CMD[@]}" "${DETECT_REDIS_SCRIPT}" 2>/dev/null || true)
}

shard_coord_backend_hint() {
  if [[ "${PALLAS_COORD_REDIS_ENABLED:-}" == "true" && -n "${PALLAS_COORD_REDIS_URL:-}" ]]; then
    echo "跨进程 claim：Redis"
  else
    echo "跨进程 claim：共享 data/ 文件"
  fi
}

read_dotenv_port() {
  local key="$1" default="$2"
  if [[ -f "${REPO_ROOT}/.env" ]]; then
    local line val
    line="$(grep -m1 "^${key}=" "${REPO_ROOT}/.env" 2>/dev/null || true)"
    if [[ -n "${line}" ]]; then
      val="${line#*=}"
      val="${val%%#*}"
      val="$(echo "${val}" | tr -d ' "'"'")"
      if [[ -n "${val}" ]]; then
        echo "${val}"
        return
      fi
    fi
  fi
  echo "${default}"
}

calc_worker_count() {
  python3 - "${REPO_ROOT}" "${BOTS_PER_SHARD}" "${ACCOUNTS_JSON}" "${REGISTRY_JSON}" <<'PY'
import json
import math
import sys
from pathlib import Path

root = Path(sys.argv[1])
bots_per = max(1, int(sys.argv[2]))
accounts_path = Path(sys.argv[3])
registry_path = Path(sys.argv[4])
need = 1

if accounts_path.is_file():
    try:
        raw = json.loads(accounts_path.read_text(encoding="utf-8"))
        items = raw.values() if isinstance(raw, dict) else raw
        enabled = 0
        for v in items:
            if isinstance(v, dict) and v.get("enabled", True):
                enabled += 1
        if enabled > 0:
            need = max(need, math.ceil(enabled / bots_per))
    except (json.JSONDecodeError, OSError, TypeError):
        pass

if registry_path.is_file():
    try:
        reg = json.loads(registry_path.read_text(encoding="utf-8"))
        assigns = reg.get("assignments") or {}
        test_cfg = reg.get("test") or {}
        test_sid = int(test_cfg.get("shard_id", 99))
        if assigns:
            normal_vals = [int(x) for x in assigns.values() if int(x) != test_sid]
            if normal_vals:
                max_sid = max(normal_vals)
                need = max(need, max_sid + 1, math.ceil(len(normal_vals) / bots_per))
    except (json.JSONDecodeError, OSError, ValueError, TypeError):
        pass

print(need)
PY
}

is_running() {
  local pidfile="$1"
  [[ -f "${pidfile}" ]] || return 1
  local pid
  pid="$(cat "${pidfile}" 2>/dev/null || true)"
  [[ -n "${pid}" ]] && kill -0 "${pid}" 2>/dev/null
}

start_one() {
  local name="$1"
  local label="$2"
  shift 2
  local pidfile="${RUN_DIR}/${name}.pid"
  local logfile="${LOG_DIR}/${name}.log"
  local bootstrap="${LOG_DIR}/${name}.bootstrap.log"

  if is_running "${pidfile}"; then
    echo "  · ${label}：已在运行（无需重复启动）"
    return 0
  fi

  if [[ "${DRY_RUN}" -eq 1 ]]; then
    echo "  · ${label}：将执行启动（预览）"
    return 0
  fi

  mkdir -p "${RUN_DIR}" "${LOG_DIR}"
  # 主日志由进程内 loguru 写入 ${logfile}（轮转）；bootstrap 仅捕获 init 前/崩溃输出
  nohup "$@" >>"${bootstrap}" 2>&1 &
  local pid=$!
  echo "${pid}" >"${pidfile}"
  echo "  · ${label}：已启动（日志 ${logfile}，启动期 ${bootstrap}）"
}

stop_one() {
  local name="$1"
  local label="$2"
  local pidfile="${RUN_DIR}/${name}.pid"
  if ! is_running "${pidfile}"; then
    rm -f "${pidfile}"
    echo "  · ${label}：未在运行"
    return 0
  fi
  local pid
  pid="$(cat "${pidfile}")"
  kill -TERM "${pid}" 2>/dev/null || true
  local i=0
  while kill -0 "${pid}" 2>/dev/null && [[ "${i}" -lt 30 ]]; do
    sleep 0.5
    i=$((i + 1))
  done
  if kill -0 "${pid}" 2>/dev/null; then
    kill -KILL "${pid}" 2>/dev/null || true
  fi
  rm -f "${pidfile}"
  echo "  · ${label}：已停止"
}

# 清理无 pid 文件的孤儿进程（重复 start 或手工杀父进程后残留）
stop_orphan_shard_processes() {
  local pat
  for pat in "${REPO_ROOT}/.venv/bin/python3 bot_hub.py" "${REPO_ROOT}/.venv/bin/python3 bot_worker.py"; do
    pkill -TERM -f "${pat}" 2>/dev/null || true
  done
  sleep 1
  for pat in "${REPO_ROOT}/.venv/bin/python3 bot_hub.py" "${REPO_ROOT}/.venv/bin/python3 bot_worker.py"; do
    pkill -KILL -f "${pat}" 2>/dev/null || true
  done
}

wait_worker_ports_released() {
  local workers="$1"
  if [[ "${DRY_RUN}" -eq 1 ]]; then
    echo "  · worker 端口：将等待释放后再启动（预览）"
    return 0
  fi
  if [[ ! -f "${WAIT_PORTS_SCRIPT}" ]]; then
    echo "  · 未找到 wait_shard_worker_ports.py，等待 2s 后继续" >&2
    sleep 2
    return 0
  fi
  echo "  等待 worker 端口释放（登记见 registry.json，超时 ${PORT_RELEASE_TIMEOUT}s）…"
  if uv run python "${WAIT_PORTS_SCRIPT}" \
    --workers "${workers}" \
    --registry "${REGISTRY_JSON}" \
    --timeout "${PORT_RELEASE_TIMEOUT}" 2>&1 | sed 's/^/    /'; then
    return 0
  fi
  echo "  · 部分端口仍未释放，继续启动可能失败；可加大 PALLAS_SHARD_PORT_RELEASE_TIMEOUT 或检查占用" >&2
  return 1
}

registry_port_for_shard() {
  local sid="$1"
  python3 - "${REGISTRY_JSON}" "${sid}" "${WORKER_BASE_PORT}" <<'PY' 2>/dev/null || echo "$((WORKER_BASE_PORT + sid))"
import json
import sys
from pathlib import Path

path, sid, base = Path(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
if not path.is_file():
    print(base + sid)
    raise SystemExit
raw = json.loads(path.read_text(encoding="utf-8"))
for row in raw.get("shards") or []:
    if int(row.get("id", -1)) == sid:
        print(int(row.get("port", base + sid)))
        raise SystemExit
print(base + sid)
PY
}

prepare_shard_ports() {
  local workers="$1"
  if [[ "${DRY_RUN}" -eq 1 ]]; then
    echo "  · worker/协议端端口：将评估并按需更新（预览）"
    return 0
  fi
  if [[ ! -f "${STARTUP_PORTS_SCRIPT}" ]]; then
    echo "  · 未找到 shard_startup_ports.py，回退为仅分配 worker 端口" >&2
    allocate_worker_ports "${workers}" || return 1
    sync_shard_protocol_ports_legacy || true
    return 0
  fi
  mkdir -p "${RUN_DIR}"
  local backup="${RUN_DIR}/accounts.json.pre_sync"
  local prep_args=(
    --workers "${workers}"
    --base "${WORKER_BASE_PORT}"
    --env "${REPO_ROOT}/.env"
    --accounts "${ACCOUNTS_JSON}"
    --backup "${backup}"
  )
  if [[ "${SKIP_OCCUPIED_PORTS}" -eq 0 ]]; then
    prep_args+=(--no-skip-occupied)
  fi
  if [[ "${SKIP_PORT_SYNC}" -eq 1 ]]; then
    prep_args+=(--skip-protocol-sync)
  fi
  local out rc=0
  out="$(uv run python "${STARTUP_PORTS_SCRIPT}" "${prep_args[@]}" 2>&1)" || rc=$?
  if [[ "${rc}" -ne 0 ]]; then
    echo "  · 分片端口准备失败" >&2
    [[ -n "${out}" ]] && echo "${out}" | sed 's/^/    /' >&2
    return "${rc}"
  fi
  local ports_line
  ports_line="$(echo "${out}" | grep -E '^[0-9]+(,[0-9]+)*$' | tail -1)"
  if [[ -z "${ports_line}" ]]; then
    echo "  · 分片端口准备失败：无有效端口列表" >&2
    return 1
  fi
  WORKER_PORTS_CSV="${ports_line}"
  export WORKER_PORTS_CSV
  echo "${out}" | grep -v -E '^[0-9]+(,[0-9]+)*$' | grep -v -E '^skip_' | sed 's/^/    /' || true
}

allocate_worker_ports() {
  local workers="$1"
  local alloc_args=(--workers "${workers}" --base "${WORKER_BASE_PORT}" --env "${REPO_ROOT}/.env")
  if [[ "${SKIP_OCCUPIED_PORTS}" -eq 0 ]]; then
    alloc_args+=(--no-skip-occupied)
  fi
  local out rc=0
  out="$(uv run python "${ALLOC_PORTS_SCRIPT}" "${alloc_args[@]}" 2>&1)" || rc=$?
  if [[ "${rc}" -ne 0 ]]; then
    return "${rc}"
  fi
  WORKER_PORTS_CSV="$(echo "${out}" | grep -E '^[0-9]+(,[0-9]+)*$' | tail -1)"
  export WORKER_PORTS_CSV
}

sync_shard_protocol_ports_legacy() {
  if [[ "${SKIP_PORT_SYNC}" -eq 1 || ! -f "${ACCOUNTS_JSON}" ]]; then
    return 0
  fi
  uv run python "${SYNC_PORTS_SCRIPT}" \
    --accounts "${ACCOUNTS_JSON}" \
    --env "${REPO_ROOT}/.env" \
    --backup "${RUN_DIR}/accounts.json.pre_sync" >/dev/null 2>&1 || true
}

registry_test_enabled() {
  python3 - "${REGISTRY_JSON}" <<'PY' 2>/dev/null
import json, sys
from pathlib import Path
p = Path(sys.argv[1])
if not p.is_file():
    raise SystemExit(1)
raw = json.loads(p.read_text(encoding="utf-8"))
test = raw.get("test") or {}
raise SystemExit(0 if test.get("enabled") else 1)
PY
}

registry_test_port() {
  python3 - "${REGISTRY_JSON}" "${TEST_SHARD_ID}" "${WORKER_BASE_PORT}" <<'PY'
import json, sys
from pathlib import Path
path, test_sid, base = Path(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
if not path.is_file():
    print(base + 100)
    raise SystemExit
raw = json.loads(path.read_text(encoding="utf-8"))
test = raw.get("test") or {}
sid = int(test.get("shard_id", test_sid))
port = int(test.get("port", 0))
if port > 0:
    print(port)
    raise SystemExit
for row in raw.get("shards") or []:
    if int(row.get("id", -1)) == sid:
        print(int(row.get("port", base + sid)))
        raise SystemExit
normal = [int(r.get("port", 0)) for r in (raw.get("shards") or []) if int(r.get("id", -1)) != sid]
print(max(normal or [base - 1]) + 1)
PY
}

registry_test_shard_id() {
  python3 - "${REGISTRY_JSON}" "${TEST_SHARD_ID}" <<'PY' 2>/dev/null
import json, sys
from pathlib import Path
raw = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
test = raw.get("test") or {}
print(int(test.get("shard_id", int(sys.argv[2]))))
PY
}

run_shard_test_cli() {
  uv run python "${SHARD_TEST_SCRIPT}" --env "${REPO_ROOT}/.env" --accounts "${ACCOUNTS_JSON}" "$@"
}

cmd_test_start() {
  if ! registry_test_enabled; then
    echo "  测试分片未启用。请先执行: ./scripts/run_sharded_bot.sh test init" >&2
    return 1
  fi
  local tsid tport
  tsid="$(registry_test_shard_id)"
  tport="$(registry_test_port)"
  print_title "Pallas-Bot 测试 worker · 启动"
  echo "  测试分片 id=${tsid}，WS 端口 ${tport}"
  load_shard_redis_env
  echo "  $(shard_coord_backend_hint)"
  echo ""
  local common=(
    PALLAS_SHARD_ENABLED=true
    PALLAS_SHARD_BOTS_PER="${BOTS_PER_SHARD}"
    PALLAS_SHARD_HUB_PORT="${HUB_PORT}"
    PALLAS_SHARD_WORKER_BASE_PORT="${WORKER_BASE_PORT}"
  )
  start_one "worker-test" "测试 worker-test（WS 端口 ${tport}）" env \
    "${common[@]}" \
    PALLAS_BOT_ROLE=worker \
    PALLAS_SHARD_ID="${tsid}" \
    PORT="${tport}" \
    "${START_CMD[@]}" bot_worker.py
  if [[ "${DRY_RUN}" -eq 1 ]]; then
    return 0
  fi
  if is_running "${PID_WORKER_TEST}"; then
    echo ""
    echo "  测试 worker 已就绪。日志: ${LOG_DIR}/worker-test.log"
  else
    echo ""
    echo "  测试 worker 启动后已退出，请查看: ${LOG_DIR}/worker-test.log"
    return 1
  fi
}

cmd_test_stop() {
  print_title "Pallas-Bot 测试 worker · 停止"
  stop_one "worker-test" "测试 worker-test"
}

cmd_test_status() {
  print_title "Pallas-Bot 测试 worker · 状态"
  if ! registry_test_enabled; then
    echo "  registry.test：未启用（test init 后可用）"
    return 0
  fi
  local tsid tport
  tsid="$(registry_test_shard_id)"
  tport="$(registry_test_port)"
  echo "  分片 id=${tsid}，WS 端口 ${tport}"
  run_shard_test_cli list 2>/dev/null | sed 's/^/    /' || true
  echo ""
  if is_running "${PID_WORKER_TEST}"; then
    echo "  进程：运行中（worker-test）"
    echo "  日志：${LOG_DIR}/worker-test.log"
  else
    echo "  进程：未运行"
    echo "  启动：./scripts/run_sharded_bot.sh test start"
  fi
}

cmd_test_restart() {
  cmd_test_stop
  echo ""
  cmd_test_start
}

dispatch_test_subcmd() {
  local sub="${1:-}"
  shift || true
  case "${sub}" in
    init)
      print_title "注册表 · 启用 test 分片"
      run_shard_test_cli init "$@"
      ;;
    add)
      if [[ $# -lt 1 ]]; then
        echo "用法: test add <QQ> [--sync-ws]" >&2
        return 1
      fi
      local qq="$1" sync_flag=()
      shift
      if [[ "${1:-}" == "--sync-ws" ]]; then
        sync_flag=(--sync-ws)
        shift
      fi
      print_title "注册表 · 迁入测试分片 ${qq}"
      run_shard_test_cli add "${qq}" "${sync_flag[@]}"
      ;;
    remove)
      if [[ $# -lt 1 ]]; then
        echo "用法: test remove <QQ>" >&2
        return 1
      fi
      print_title "注册表 · 移出测试分片 $1"
      run_shard_test_cli remove "$1"
      ;;
    list)
      run_shard_test_cli list
      ;;
    sync|sync-ws)
      print_title "协议端 · 同步测试分片 ws_url"
      run_shard_test_cli sync-ws "$@"
      ;;
    start) cmd_test_start ;;
    stop) cmd_test_stop ;;
    status) cmd_test_status ;;
    restart) cmd_test_restart ;;
    "")
      echo "用法: test <init|add|remove|list|sync-ws|start|stop|status|restart> ..." >&2
      return 1
      ;;
    *)
      echo "未知 test 子命令: ${sub}" >&2
      return 1
      ;;
  esac
}

cmd_start() {
  local workers="${WORKER_COUNT_OVERRIDE:-$(calc_worker_count)}"
  local hub_url="http://127.0.0.1:${HUB_PORT}"

  print_title "Pallas-Bot 分片模式 · 启动"
  echo "  配置：控制台端口 ${HUB_PORT}，worker ${workers} 个，每片约 ${BOTS_PER_SHARD} 头牛"
  echo "        worker 起点端口 ${WORKER_BASE_PORT}$(
    [[ "${SKIP_OCCUPIED_PORTS}" -eq 1 ]] && echo "（自动跳过占用）" || echo "（严格 起点+分片号）"
  )"
  load_shard_redis_env
  echo "        $(shard_coord_backend_hint)"
  if [[ "${PALLAS_COORD_REDIS_ENABLED:-}" == "true" ]]; then
    if ! uv run python -c "import redis" 2>/dev/null; then
      echo "        提示：请执行 uv sync --extra coord-redis 以安装 redis 客户端" >&2
    fi
  fi
  echo ""

  wait_worker_ports_released "${workers}" || true
  echo ""
  prepare_shard_ports "${workers}" || return 1
  if [[ -n "${WORKER_PORTS_CSV:-}" ]]; then
    echo "        实际端口：${WORKER_PORTS_CSV}"
  fi
  echo ""
  echo "  正在启动进程…"

  local common=(
    PALLAS_SHARD_ENABLED=true
    PALLAS_SHARD_BOTS_PER="${BOTS_PER_SHARD}"
    PALLAS_SHARD_HUB_PORT="${HUB_PORT}"
    PALLAS_SHARD_WORKER_BASE_PORT="${WORKER_BASE_PORT}"
  )

  start_one hub "控制台 (hub)" env \
    "${common[@]}" \
    PALLAS_BOT_ROLE=hub \
    PORT="${HUB_PORT}" \
    "${START_CMD[@]}" bot_hub.py

  if [[ "${DRY_RUN}" -eq 0 ]]; then
    sleep 1
  fi

  local sid=0
  IFS=',' read -r -a _worker_ports <<< "${WORKER_PORTS_CSV:-}"
  while [[ "${sid}" -lt "${workers}" ]]; do
    local wport=$((WORKER_BASE_PORT + sid))
    if [[ "${#_worker_ports[@]}" -gt "${sid}" && -n "${_worker_ports[sid]}" ]]; then
      wport="${_worker_ports[sid]}"
    fi
    start_one "worker-${sid}" "牛牛 worker-${sid}（WS 端口 ${wport}）" env \
      "${common[@]}" \
      PALLAS_BOT_ROLE=worker \
      PALLAS_SHARD_ID="${sid}" \
      PORT="${wport}" \
      "${START_CMD[@]}" bot_worker.py
    sid=$((sid + 1))
  done

  if [[ "${DRY_RUN}" -eq 1 ]]; then
    echo ""
    echo "  （预览模式，未实际启动进程）"
    return 0
  fi

  echo ""
  echo "  正在确认进程是否就绪…"
  local hub_ok=0 worker_running=0 worker_fail=0
  if is_running "${PID_HUB}"; then
    hub_ok=1
  else
    echo "  · 控制台 hub 未在运行，请查看日志: ${LOG_DIR}/hub.log"
  fi
  local f
  for f in "${RUN_DIR}"/worker-*.pid; do
    [[ -e "${f}" ]] || continue
    [[ "$(basename "${f}" .pid)" == "worker-test" ]] && continue
    if is_running "${f}"; then
      worker_running=$((worker_running + 1))
    else
      worker_fail=$((worker_fail + 1))
      local wname
      wname="$(basename "${f}" .pid)"
      echo "  · ${wname} 启动后已退出，请查看: ${LOG_DIR}/${wname}.log"
    fi
  done

  print_title "启动完成"
  if [[ "${hub_ok}" -eq 1 ]]; then
    echo "  在浏览器打开："
    echo "    WebUI   ${hub_url}/pallas/"
    echo "    协议端  ${hub_url}/protocol/console/"
  fi
  echo ""
  echo "  常用命令："
  echo "    ./scripts/run_sharded_bot.sh status   查看运行状态"
  echo "    ./scripts/run_sharded_bot.sh stop     停止全部分片"
  echo "    ./scripts/run_sharded_bot.sh test start   仅启测试 worker"
  echo "    tail -f ${LOG_DIR}/worker-0.log       查看某 worker 日志"
  if [[ "${worker_fail}" -gt 0 ]]; then
    echo ""
    echo "  部分 worker 未保持运行，多为端口占用或配置错误；修复后执行 restart。"
  elif [[ "${hub_ok}" -eq 1 ]] && [[ "${worker_running}" -eq "${workers}" ]]; then
    echo ""
    echo "  全部进程已就绪。"
  fi
}

cmd_stop() {
  print_title "Pallas-Bot 分片模式 · 停止"
  stop_one "worker-test" "测试 worker-test"
  local f
  for f in "${RUN_DIR}"/worker-*.pid; do
    [[ -e "${f}" ]] || continue
    [[ "$(basename "${f}" .pid)" == "worker-test" ]] && continue
    local sid=""
    if [[ "$(basename "${f}" .pid)" =~ worker-([0-9]+) ]]; then
      sid="${BASH_REMATCH[1]}"
    fi
    stop_one "$(basename "${f}" .pid)" "牛牛 worker-${sid}"
  done
  stop_one hub "控制台 (hub)"
  stop_orphan_shard_processes
  echo ""
  echo "  全部分片进程已处理完毕。"
}

cmd_status() {
  local workers=0
  local running_workers=0
  local stale_workers=0
  local hub_url="http://127.0.0.1:${HUB_PORT}"

  print_title "Pallas-Bot 分片模式 · 运行状态"

  if is_running "${PID_HUB}"; then
    echo "  控制台 (hub)     运行中"
    echo "                   ${hub_url}/pallas/"
    echo "                   ${hub_url}/protocol/console/"
  else
    if [[ -f "${PID_HUB}" ]]; then
      echo "  控制台 (hub)     未运行（残留 pid 文件，可执行 start 清理并拉起）"
    else
      echo "  控制台 (hub)     未运行"
    fi
  fi

  echo ""
  echo "  牛牛 worker："
  local f
  for f in "${RUN_DIR}"/worker-*.pid; do
    [[ -e "${f}" ]] || continue
    [[ "$(basename "${f}" .pid)" == "worker-test" ]] && continue
    workers=$((workers + 1))
    local name pid port
    name="$(basename "${f}" .pid)"
    port=""
    if [[ "${name}" =~ worker-([0-9]+) ]]; then
      port="$(registry_port_for_shard "${BASH_REMATCH[1]}")"
    fi
    if is_running "${f}"; then
      running_workers=$((running_workers + 1))
      echo "    ${name}   运行中   反向 WS 端口 ${port}"
    else
      stale_workers=$((stale_workers + 1))
      echo "    ${name}   未运行   （进程已退出，日志 ${LOG_DIR}/${name}.log）"
    fi
  done
  if [[ "${workers}" -eq 0 ]]; then
    echo "    （尚无生产 worker 记录，请先 start）"
  fi

  echo ""
  echo "  测试 worker-test："
  if registry_test_enabled; then
    local tsid tport
    tsid="$(registry_test_shard_id)"
    tport="$(registry_test_port)"
    if is_running "${PID_WORKER_TEST}"; then
      echo "    运行中   分片 ${tsid}，WS 端口 ${tport}"
    else
      echo "    未运行   分片 ${tsid}，WS 端口 ${tport}（test start 拉起）"
    fi
  else
    echo "    未配置（test init 启用）"
  fi

  echo ""
  echo "  日志目录：${LOG_DIR}/"
  echo "  （WebUI「日志」页可汇总查看 hub + 各 worker）"

  if [[ "${stale_workers}" -gt 0 ]]; then
    echo ""
    echo "  提示：有 ${stale_workers} 个 worker 未在运行，可执行："
    echo "    ./scripts/run_sharded_bot.sh restart"
  elif [[ "${running_workers}" -eq 0 ]] && ! is_running "${PID_HUB}"; then
    echo ""
    echo "  当前无运行中的分片进程。启动请执行："
    echo "    ./scripts/run_sharded_bot.sh start"
  fi
}

cmd_restart() {
  local workers="${WORKER_COUNT_OVERRIDE:-$(calc_worker_count)}"
  cmd_stop
  echo ""
  wait_worker_ports_released "${workers}" || true
  echo ""
  cmd_start
}

# --- parse ---
ACTION=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    start|stop|status|restart)
      ACTION="$1"
      shift
      ;;
    test)
      ACTION="test"
      shift
      TEST_ARGS=("$@")
      break
      ;;
    test-init|test-add|test-remove|test-list|test-sync|test-sync-ws|test-start|test-stop|test-status|test-restart)
      ACTION="test"
      sub="${1#test-}"
      if [[ "${sub}" == "sync" ]]; then
        sub="sync-ws"
      fi
      TEST_ARGS=("${sub}" "${@:2}")
      break
      ;;
    --workdir)
      REPO_ROOT="$(cd "$2" && pwd)"
      cd "${REPO_ROOT}"
      RUN_DIR="${REPO_ROOT}/data/pallas_shard/run"
      LOG_DIR="${REPO_ROOT}/data/pallas_shard/logs"
      PID_HUB="${RUN_DIR}/hub.pid"
      ACCOUNTS_JSON="${REPO_ROOT}/data/pallas_protocol/accounts.json"
      REGISTRY_JSON="${REPO_ROOT}/data/pallas_shard/registry.json"
      shift 2
      ;;
    --workers)
      WORKER_COUNT_OVERRIDE="$2"
      shift 2
      ;;
    --bots-per-shard)
      BOTS_PER_SHARD="$2"
      shift 2
      ;;
    --hub-port)
      HUB_PORT="$2"
      shift 2
      ;;
    --worker-base)
      WORKER_BASE_PORT="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --skip-port-sync)
      SKIP_PORT_SYNC=1
      shift
      ;;
    --no-skip-occupied-ports)
      SKIP_OCCUPIED_PORTS=0
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "未知参数: $1（使用 -h 查看帮助）" >&2
      usage >&2
      exit 1
      ;;
  esac
done

HUB_PORT="${PALLAS_SHARD_HUB_PORT:-$(read_dotenv_port PORT "${HUB_PORT}")}"
WORKER_BASE_PORT="${PALLAS_SHARD_WORKER_BASE_PORT:-$(read_dotenv_port PALLAS_SHARD_WORKER_BASE_PORT "${WORKER_BASE_PORT}")}"

if [[ -z "${ACTION}" ]]; then
  usage >&2
  exit 1
fi

case "${ACTION}" in
  start) cmd_start ;;
  stop) cmd_stop ;;
  status) cmd_status ;;
  restart) cmd_restart ;;
  test) dispatch_test_subcmd "${TEST_ARGS[@]}" ;;
esac

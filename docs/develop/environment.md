# 本地开发环境

## 前置条件

- **Python 3.12+**
- **[uv](https://docs.astral.sh/uv/)**（依赖与虚拟环境）
- 可选：**Docker**（数据库、协议端、镜像构建校验）
- 可选：**Node.js**（仅开发 [Pallas-Bot-WebUI](https://github.com/PallasBot/Pallas-Bot-WebUI) 前端时）

## 克隆与安装依赖

```bash
git clone https://github.com/PallasBot/Pallas-Bot.git
cd Pallas-Bot
uv sync --dev
```

需要分片协调 Redis 时：

```bash
uv sync --dev --extra coord-redis
```

`uv sync` 会在虚拟环境中注册 **`pallas`** 命令（见下文「统一运维 CLI」）。

## 统一运维 CLI（`pallas`）

Bot 仓库内置统一运维入口，推荐在**仓库根目录或任意子目录**使用（CLI 会向上查找含 `pyproject.toml` 的 Pallas-Bot 根目录）：

```bash
uv run pallas --help
uv run pallas doctor          # 环境检查（uv、配置、启停脚本、分片 Redis）
```

激活虚拟环境后也可直接：

```bash
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pallas status --mode shard
```

### 启停 Bot

| 场景 | 命令 |
| --- | --- |
| 单进程启动 | `uv run pallas run unified` |
| 分片启动（hub + worker） | `uv run pallas run shard` |
| 分片：仅 hub | `uv run pallas run shard --hub-only` |
| 分片：仅补缺失 worker | `uv run pallas run shard --workers-only` |
| 查看状态 | `uv run pallas status --mode auto` |
| 停止 | `uv run pallas stop --mode auto` |
| 重启 | `uv run pallas restart --mode auto` |
| 分片：仅重启 worker | `uv run pallas restart --mode shard --workers-only` |

`--mode auto` 会根据 pid 文件与环境变量推断单进程或分片；分片部署建议显式写 `--mode shard`。

**注意**：若 worker 已全部在运行，再次 `pallas run shard` 会**跳过** worker 启动与端口重分配，避免误改 registry；需要全量重启 worker 时用 `restart --workers-only`。

### 其它常用子命令

```bash
uv run pallas sync              # 包装 uv sync
uv run pallas update bot        # git 更新本体（可加 --restart）
uv run pallas update webui      # 下载 WebUI dist
uv run pallas ext list          # 官方扩展
uv run pallas plugin …          # 插件运维
uv run pallas deploy shard      # 应用 deploy 分片模板
```

`./scripts/pallas` 与 `./scripts/run_*_bot.sh` 仍为兼容入口，内部由上述 CLI 调用。脚本索引见 [`scripts/README.md`](../../scripts/README.md)。

## 运行配置

**不要**再依赖根目录 `.env` 作为唯一配置源。

1. 复制主配置：

```bash
cp config/pallas.example.toml config/pallas.toml
```

2. 编辑 `config/pallas.toml`：**至少**改 `superusers` 与数据库段（见示例内「最少配置」）。

最少示例：

```toml
[bootstrap]
host = "0.0.0.0"
port = 8088
superusers = ["你的QQ号"]
db_backend = "mongodb"

[bootstrap.mongo]
host = "127.0.0.1"
port = 27017
db = "PallasBot"
```

3. 其余插件与通用项在 Web 控制台保存，落盘 **`data/pallas_config/webui.json`**。

合并顺序与读取 API 见 [配置存储](../architecture/settings-storage.md)。从旧 `.env` 一次性迁移：

```bash
uv run python tools/migrate_env_to_pallas.py
```

`.env` 仍可保留 **NoneBot / pip 插件**相关项（见 `.env.example`），避免与 `webui.json` 同名键重复。

## 启动 Bot

除下述 `nb run` 与脚本外，**日常启停优先用 [统一运维 CLI](#统一运维-cli-pallas)**（`uv run pallas run unified` / `run shard`）。

单进程（最常见本地调试）：

```bash
uv run nb run
```

或使用专用启停脚本（对照测试、协议端口同步）：

```bash
./scripts/run_unified_bot.sh start
./scripts/run_unified_bot.sh status
./scripts/run_unified_bot.sh stop
```

等价 CLI：

```bash
uv run pallas run unified
uv run pallas status --mode unified
uv run pallas stop --mode unified
```

浏览器打开 `http://127.0.0.1:8088/pallas/`，使用启动日志中的口令登录。

### 分片模式（可选）

生产或多进程场景见 [多进程分片](../architecture/bot_process_sharding.md)。本地若需验证分片：

- 在 `pallas.toml` 的 `[env]` 配置 `REDIS_URL`（需 `uv sync --extra coord-redis`）
- 使用 `uv run pallas run shard`（会探测 Redis；worker 已运行时跳过重复启动）

```bash
uv run pallas run shard
uv run pallas status --mode shard
uv run pallas stop --mode shard
```

测试 worker（`test` / `test2` 子命令）等高级选项仍见 `./scripts/run_sharded_bot.sh -h`。

### 站点自有插件

在 `local/plugins/<name>/` 放置插件，并在 `pallas.toml` 中设置：

```toml
[bootstrap]
extra_plugin_dirs = ["local/plugins"]
```

详见 [站点定制与更新](../architecture/site-customization-and-updates.md)。

## 质量检查（与 CI 一致）

```bash
uv run ruff check pallas/ packages/
uv run ruff format --check pallas/ packages/
```

自动修复：

```bash
uv run ruff check --fix pallas/ packages/
uv run ruff format pallas/ packages/
```

运行测试：

```bash
uv run pytest
```

可选（与 CI 对齐，不阻断合并）：

```bash
uv run pip-audit
docker build -t test-build .
```

## pre-commit（推荐）

```bash
uv run pre-commit install
uv run pre-commit run -a
```

策略说明：**全仓**做 YAML/TOML、尾随空格等基础检查；**Ruff 仅作用于 `pallas/`、`packages/`**；`.env` 被排除以免误改本地密钥。

## 日志习惯

项目使用 **loguru 风格**的 `logger`（NoneBot 提供）。占位符用 `{}` 或 f-string，避免 `logger.debug("msg %s", x)` 导致消息里仍显示 `%s`。

## 下一步

- 准备提 PR：[贡献与提交流程](workflow.md)
- 写新功能：[插件开发入门](../developer/plugin-development/getting-started.md)

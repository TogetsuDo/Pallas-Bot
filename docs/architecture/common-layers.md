# src 内核分层（3.x 历史 · 4.0 起见 [pallas-package-layout](pallas-package-layout.md)）

> **4.0 起**：`src/` 已移除；内核包名为 `pallas/`；内置插件在 `packages/`；社区作者入口为 `pallas.api.*`。

`src/` 下除 `plugins/` 外按职责分为六层（**4.0 已移除，下表为历史对照**）：

| 层 | 路径 | 内容 |
| --- | --- | --- |
| foundation | `src/foundation/` | `config`、`paths`、`logging`、`db`；`bot_version`、`command_prefix`、`apscheduler_runtime` |
| platform | `src/platform/` | `shard`、`multi_bot`（含 **bot_filter** / connected_roster）、`ingress`（含 **gate** 预处理器、dispatch、route_index）、`bot_runtime`（含 `kernel_runtime`）、`coord`、`federate`、`ai_callback` |
| features | `src/features/` | `cmd_perm`、`command_limits`、`message_scrub`、`community_stats`、`corpus`、`control_plane`、`ban_gate`、`persona`、`llm`、`service_gateways`（连通探测 +「牛牛连通」口令） |
| console | `src/console/` | `webui`、`web`、`cli` |
| domain | `src/domain/` | `arknights` 等域共享（游戏数据见 [arknights-knowledge-mcp.md](arknights-knowledge-mcp.md)） |
| shared | `src/shared/` | `utils`、`adapters`、`service_probe` |

## 依赖方向（建议）

- `shared`、`foundation`：不依赖 `platform` / `features`
- `platform`：可依赖 `foundation`、`shared`
- `features`：可依赖 `foundation`、`shared`、`platform`（尽量少）
- `console`：可依赖各层（面向 WebUI 聚合配置）
- `domain`：尽量只依赖 `foundation`、`shared`

## 导入示例（4.0 现行）

```python
# 社区插件作者（仅 pallas.api.*）：
from pallas.api.commands import group_command, PluginHandlerContext
from pallas.api.config import install_hot_reload_config
from pallas.api.perm import group_message_permission_for_command
from pallas.api.limits import is_command_cooldown_ready
from pallas.api.metadata import usage_line, SCENE_GROUP
from pallas.api.paths import plugin_data_dir
from pallas.api.storage import GroupPluginStorage

# 内置插件 / 内核（允许 pallas.core.*、pallas.product.*）：
from pallas.core.foundation.config.repo_settings import repo_env_raw_value
from pallas.core.runtime import register_ingress_dispatch_runtime
from pallas.core.platform.multi_bot.dedup import should_skip_group_message
```

### 3.x 历史（已移除）

```python
from src.foundation.config.repo_settings import repo_env_raw_value
from src.platform.bot_runtime import register_ingress_dispatch_runtime
from src.platform.multi_bot.dedup import should_skip_group_message
from src.features.cmd_perm import check_command_permission
```

旧路径 `src.common.*` 已移除，请使用上表中的分层路径。

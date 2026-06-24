# pallas.api Cookbook（扩展作者）

> 稳定入口一览。实现细节在 `pallas.core` / `pallas.product`，**社区与官方扩展只应 import `pallas.api.*`**（及模板约定的包内模块）。

## 安装 pallas-core

**全仓开发**（推荐）：在 Pallas-Bot 根目录 `uv sync`，`pallas` 由主仓提供，无需单独安装。

**独立扩展仓库**（预发布阶段）：

```bash
# 在主仓构建 wheel
./scripts/build_core.sh
uv pip install build/pallas-core/dist/pallas_core-*.whl

# PyPI 正式发布后
uv add "pallas-core>=4.0.0,<5.0.0"
```

扩展模板 `templates/pallas-plugin-extension/pyproject.toml` 已声明 `pallas-core` 依赖。

## 命令与 handler

```python
from pallas.api.commands import (
    PluginCommand,
    PluginHandlerContext,
    bind_alias_handlers,
    group_command,
    message_command,
    private_command,
)
```

## 配置与 WebUI 热载

```python
from pallas.api.config import install_hot_reload_config
```

## 权限与冷却

```python
from pallas.api.perm import (
    DEFAULT_COMMAND_PERMISSIONS,
    VALID_LEVELS,
    group_message_permission_for_command,
    satisfies_command_permission,
)
from pallas.api.limits import is_command_cooldown_ready, refresh_command_cooldown
```

## 帮助元数据

```python
from pallas.api.metadata import join_usage, usage_line, SCENE_GROUP
```

## 路径与存储

```python
from pallas.api.paths import plugin_data_dir, resource_dir
from pallas.api.storage import get_plugin_storage, set_plugin_storage
```

## 用户可见错误（脱敏）

```python
from pallas.api.messages import sanitize_user_visible_message, user_failure_reply
```

## 连通探测（WebUI 健康）

```python
from pallas.api.probe import ServiceProbeResult, format_probe_lines
```

## 参考图 / 媒体（画图类）

```python
from pallas.api.media import resolve_reference_inline_urls, bytes_from_reference_token
```

## 消息审查

```python
from pallas.api.safety import is_message_scrub_blocked_async
```

## AI 运行时健康（只读）

插件侧熔断/降级应读 AI `/health` 缓存，勿自建 parallel circuit：

```python
from pallas.api.ai_runtime_health import image_runtime_circuit_is_open
```

## 平台协作（官方扩展 / 内置）

`pallas.api.platform` 暴露多 Bot 舰队、分片、callback 等钩子；**社区插件默认不依赖**。需要时查阅模块 `__all__` 与 maintainer 文档。

## 禁止 import

| 区域 | 原因 |
| --- | --- |
| `pallas.core.*`（除 api re-export） | 内部实现 |
| `pallas.product.*` | 产品域 |
| `pallas.console.*` | WebUI 维护者向 |
| `pallas.product.llm.client` 直调 | 应走 capability 信封 / AI 仓 |

CI：`tools/check_plugin_imports.py` 与 `community_plugin_author check` 会对齐上述边界。

## 相关

- [插件开发入门](getting-started.md)
- [Golden Plugin](golden-plugin.md)
- [包布局与 api 白名单](../../architecture/internal/pallas-package-layout.md)

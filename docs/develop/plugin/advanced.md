# 插件进阶能力

在掌握 [入门](getting-started.md) 与 [结构约定](structure.md) 后，按需接入下列横切能力。分章说明见 [插件开发 Skill](../../skills/pallas-plugin-development/SKILL.md)。

## 命令权限（cmd_perm）

将命令鉴权抽象为可配置等级；默认在代码声明，运行中可由环境变量或 WebUI「通用配置 → 命令权限」覆盖。帮助图根据 metadata **动态**展示「何人可用」。

### 接入步骤

1. 在 `PluginMetadata.extra["command_permissions"]` 声明命令 ID 与默认等级
2. Matcher 使用 `permission_for_command("my_plugin.action")`
3. 群消息 / 私聊限定使用合并 helper（**禁止** `Permission & Permission`）：

```python
from pallas.api.perm import (
    group_message_permission_for_command,
    private_message_permission_for_command,
)

on_command("群内", permission=group_message_permission_for_command("my_plugin.in_group"))
```

4. 消息流中手动判断：

```python
from pallas.api.perm import satisfies_command_permission

await satisfies_command_permission(bot, event, "my_plugin.action")
```

### 文案禁忌

- `usage`、`trigger_condition` **不写死**「仅群管」「默认群主」等
- 与发送者权限无关的条件（如「本 Bot 须为 QQ 群管」）写在 `detail_des` 或插件 README

完整字段与自检清单：[cmd_perm 接入说明](../../common/cmd_perm/README.md)

## 命令冷却（command_limits）

高频命令在 `cmd_perm` 通过后，用统一 helper 做群级 / 私聊级 CD，存储 key 为 `cmd_limit:{command_id}`：

```python
from pallas.api.limits import is_command_cooldown_ready, refresh_command_cooldown

if not await is_command_cooldown_ready(event, "my_plugin.demo", 10):
    return
await refresh_command_cooldown(event, "my_plugin.demo", 10)
```

可在 `PluginMetadata.extra["command_limits"]` 声明默认 CD（与 `command_permissions` 并列）。详见 [command_limits](../../common/command_limits/README.md)。

## WebUI 配置热重载

控制台通过 `data/pallas_config/webui.json` 统一读写插件配置。

```python
from pydantic import BaseModel, Field
from pallas.api.config import install_hot_reload_config

class Config(BaseModel, extra="ignore"):
    threshold: int = Field(default=3, description="触发阈值。")

plugin_webui = install_hot_reload_config(Config, config_module=__name__)
get_config = plugin_webui.get
```

- 业务代码始终 `get_config()`，保存后自动 reload，**无需重启**
- 复杂解析：传入 `parse_env_value`（参考 `draw/config.py`）
- 除 Config 外还有运行时单例：传入 `on_reload`
- 已有自定义缓存逻辑：登记 `plugin_webui_registry`

详见 [WebUI 插件配置](../../common/webui/README.md)

### 元数据级与 `reload_policy`

配置热重载只覆盖 `config.py`。若插件会改 `PluginMetadata.extra` 里的 help、ingress、`command_permissions` 等，且希望 **WebUI 保存后不必重启**：

```python
extra={
    ...
    "reload_policy": "metadata",
}
```

| 场景 | 建议 |
| --- | --- |
| 只调开关、阈值 | 默认即可（`config_only` 或不写） |
| 改 help / ingress / 权限默认声明 | `metadata` |
| 改 Python handler / 业务逻辑 | 重启；`full` 暂同 metadata，代码热载未落地 |

分级说明：[热重载分级](../../architecture/hot-reload-tiers.md)。与声明式 `plugin_storage` 无关，但可一并写在 `extra` 供能力总览展示。

## 消息审查（message_scrub）

复读、做梦等插件的入站消息可先经统一审查过滤（广告、风控等）。插件侧按 [message_scrub](../../common/message_scrub/README.md) 登记 hook，避免在各插件重复实现。

## 跨插件与内核层

可复用能力优先沉淀到 `pallas/` 内核层（见 [common-layers](../../architecture/common-layers.md)）：

| 层 | 路径 | 典型用途 |
| --- | --- | --- |
| api | `pallas.api.commands` | 口令注册、PluginHandlerContext |
| api | `pallas.api.config` | 控制台配置热重载 |
| api | `pallas.api.perm` | 命令权限 |
| api | `pallas.api.limits` | 命令冷却 |
| api | `pallas.api.storage` | 群/用户级声明式存储 |
| api | `pallas.api.paths` | `data/`、`resource/` 路径 |
| api | `pallas.api.metadata` | 帮助文案、菜单模板 |
| core | `pallas.core.foundation.config` | 群/用户/Bot 级配置 |
| core | `pallas.core.foundation.db` | 数据库 repository |
| core | `pallas.core.platform.shard` | 分片 presence、协调 |
| product | `pallas.product.message_scrub` | 入站审查（内置专用） |

> **社区 / pip 扩展**：仅用 `pallas.api.*`（L1）。**内置 `packages/`**：可用 `pallas.api.*` + `pallas.product.*`（L2）。引入内核层时保持**语义单一**，避免把某一插件的业务泄漏到内核。

## 站点自有插件与覆盖

| 场景 | 做法 |
| --- | --- |
| 私有功能、不提交主仓 | `local/plugins/<name>/` + `extra_plugin_dirs` |
| 整包替换主仓同名插件 | `local/plugins/<原名>/`（加载优先于 `packages/`） |
| 只改主仓少量核心文件 | `local/patches/*.patch` 或提 PR |

见 [站点定制与更新](../../architecture/site-customization-and-updates.md)

## 分片部署注意

- hub / worker 共用 `data/` 卷时，WebUI 配置与各插件 `data/<name>/` 一致
- worker 侧 `get_*_config()` 可按磁盘 mtime 拾取新配置
- 涉及 Bot 连接、presence 时使用 `pallas.core.platform.shard` 提供的 API，勿假设单进程内存全局状态

见 [多进程分片](../../architecture/bot_process_sharding.md)、[中央入站调度](../../architecture/central-ingress-dispatch.md)

## 日志

使用 NoneBot / loguru 风格 `logger`，占位符用 `{}` 或 f-string：

```python
logger.info(f"bot [{bot_id}] action in group [{group_id}]")
```

## AI 与外部服务

- 对话 / 唱歌 / TTS 等扩展见 [Pallas-Bot-AI](https://github.com/PallasBot/Pallas-Bot-AI) 与文档站「AI 扩展」
- 画画、MAA 等网关字段见 WebUI「服务网关」与 `pallas/console/webui/service_gateways_section.py`

## 测试与排障

- 单元测试：`tests/plugins/<name>/`，必要时 mock `Bot` / 数据库
- 本地配置：勿提交 `config/pallas.toml`、`data/`
- 部署问题：[FAQ](../../FAQ.md)

## 相关文档

- [插件开发入门](getting-started.md)
- [插件结构与约定](structure.md)
- [插件开发 Skill](../../skills/pallas-plugin-development/SKILL.md)
- [贡献与提交流程](../workflow.md)

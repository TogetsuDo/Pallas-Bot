# 热重载分级（配置 / 元数据 / 代码）

> **现状**：配置级已成熟；元数据级 WebUI 保存与 `pallas plugin reload` / `POST /plugins/{name}/reload` 可触发索引重建；代码级 `full` 策略尝试 `importlib.reload`，失败则提示重启。

## 三级对照

| 级别 | 名称 | 变更内容 | 生效方式 | 现状 |
| --- | --- | --- | --- | --- |
| **配置** | 配置 | `config.py` 字段 → `webui.json` | `install_hot_reload_config` 保存后立即 reload | ✅ 默认路径 |
| **元数据** | 元数据 | `PluginMetadata.extra`、help 索引、ingress route | 保存后重读声明 / 重建索引（**不**卸载 matcher） | ✅ `reload_plugin_metadata_index()`；WebUI 插件配置保存对 `metadata`/`full` 策略触发 |
| **代码** | 插件代码 | Python 模块变更 | 受控 reload 或提示进程重启 | ❌ 默认需重启 |

## 明确不做

- NoneBot matcher 级热卸载/重载**不作为默认运维路径**。
- 扩展 pip 包**更新**已加载模块：不支持运行时热更，须重启（PoC 仅覆盖**首次安装**后加载）。
- 社区插件 **git 更新/卸载**：同上，不支持代码级热更；**首次安装**在 unified + `extra_plugin_dirs` 就绪时可热加载。

## 社区插件激活策略

社区插件（`local/plugins/<id>/`）经 `community_plugin_ops` → `append_community_activation_result` 生效，与官方扩展共用 `activation_action` / `restart_scheduled` 字段。

| 操作 | activation_policy | unified（不勾重启） | shard（勾重启） |
| --- | --- | --- | --- |
| **首次安装** | `hot-reloadable` | `hot_load_extra_dir_plugin()` → `hot-reload` | 提示待重启；勾重启则 **workers-only** |
| **git 更新** | `workers-restart` | 提示待重启（诚实说明不支持热更） | 勾重启 → **workers-only** |
| **卸载** | `full-restart` | 提示待重启 | 勾重启 → **workers-only** |

前提：`config/pallas.toml` 的 `[bootstrap].extra_plugin_dirs` 含 `"local/plugins"`，否则安装后无法热加载。

## 官方扩展激活策略（activation_policy）

这是站点运维视角的“安装后如何生效”分级，独立于作者在 metadata 中声明的 `reload_policy`：

| 值 | 含义 | 典型场景 |
| --- | --- | --- |
| `hot-reloadable` | 优先尝试运行时热加载 | 纯命令型、无 hub 路由 / 后台任务的扩展 |
| `workers-restart` | 分片优先 `workers-only`；单进程整进程重启 | 主要影响 worker 命令处理、共享协调状态但不改 hub 挂载 |
| `full-restart` | 需要全栈重启 | hub 路由、协议端管理、跨角色挂载、副作用较重 |

当前建议分级：

| 官方扩展 | activation_policy |
| --- | --- |
| `pallas-plugin-draw` | `hot-reloadable` |
| `pallas-plugin-bot-status` | `hot-reloadable` |
| `pallas-plugin-duel` | `workers-restart` |
| `pallas-plugin-who-is-spy` | `workers-restart` |
| `pallas-plugin-dream` | `workers-restart` |
| `pallas-plugin-ai-media` | `workers-restart` |
| `pallas-plugin-protocol` | `full-restart` |
| `pallas-plugin-maa` | `full-restart` |

## `reload_policy`（extra 可选键）

在 `PluginMetadata.extra` 声明插件作者期望的重载粒度（供能力总览与未来 CLI 读取）：

| 值 | 含义 |
| --- | --- |
| `config_only` | 仅配置级（**默认**；与现网一致） |
| `metadata` | 元数据级：允许重读 extra / help / ingress，不卸载 matcher |
| `full` | 代码级：尝试重载模块；失败则提示重启 |

解析 API：`src.features.plugin_reload.reload_policy_from_metadata()`。

示例：

```python
extra={
    ...
    "reload_policy": "config_only",
}
```

## 运维入口

| 场景 | 推荐 |
| --- | --- |
| 改插件开关/阈值 | WebUI **插件** 页保存（配置级） |
| 改命令权限 / CD | WebUI **命令权限** / **命令冷却**（配置级） |
| 改 help / ingress 声明 | 插件 `reload_policy: metadata` 时 WebUI 保存可触发元数据索引重建；或 `pallas plugin reload <name>` / 控制台 API |
| 改 Python 代码 | 重启 Bot；`reload_policy: full` 可尝试 `pallas plugin reload`（失败则重启）；群内 **牛牛重启** 或 `pallas restart` |
| 安装官方扩展 | WebUI 插件商店；勾选「安装并重启」或手动重启 |
| 安装社区插件 | WebUI 社区商店 / git 安装；单机 unified 首次安装可热加载；**更新须重启** |
| 更新社区插件 | 商店「更新并重启」；分片优先 workers-only |

## 相关文档

- [插件热重载与分级无痛重启 — 实现计划](plugin-hot-reload-implementation.md)
- [WebUI 配置与热重载](../common/webui/README.md)
- [settings-storage.md](settings-storage.md)
- [热重载前检查清单](../maintainer/operate/hot-reload-pre-reload-checklist.md)
- [开发者侧插件治理概览](../developer/architecture/plugin-governance.md)

# 插件热重载与分级无痛重启 — 实现计划

> 状态：初稿（2026-06-23）  
> 关联任务：落地插件热重载与分级无痛重启  
> 前置评估：[热重载分级](hot-reload-tiers.md)、Notion「评估官方扩展安装后的热生效路径」（Done）

## 背景

两套独立语义：

| 维度 | `reload_policy` | `activation_policy` |
| --- | --- | --- |
| 对象 | 已加载插件的配置/元数据/代码变更 | pip 安装/更新/卸载后的进程级生效 |
| 入口 | WebUI 插件配置保存 | WebUI 插件商店 / CLI |
| 现状 | 配置级 ✅；元数据级 ✅；代码级 ❌ | CLI 已分级；WebUI 仍一律 `needs_restart: true` |

CLI 侧 `append_activation_result()` 已实现（`pallas/console/cli/extension_activation.py`），WebUI `extension_install.py` 未接线。

## 目标

1. WebUI 安装/更新/卸载结果与 CLI 激活语义对齐
2. 分片场景支持 **workers-only** 重启
3. 落地 `pallas plugin reload`（读 `reload_policy`）
4. `hot-reloadable` 官方扩展 PoC（unified 模式运行时加载）
5. 控制台提供 **重启 Bot** 入口（见独立 Feature 任务）

## 非目标

- NoneBot matcher 级热卸载/重载作为默认运维路径
- 社区 pip 插件任意热插拔（受 NoneBot 扫描限制）
- 安装后自动无提示全进程重启（须权限确认）

## 激活流水线（官方扩展）

### 现状（CLI）

```
pip install/update/uninstall
  → append_activation_result(restart=?)
      → hot-reloadable + unified → _hot_load_package_modules()
      → workers-restart + shard   → schedule_bot_restart(workers_only=true)
      → else                      → schedule_bot_restart(workers_only=false)
```

返回字段：`activation_policy`、`activation_action`、`needs_restart`、`restart_scheduled`。

### 目标（WebUI 对齐）

`extension_install.py` 在安装/更新/卸载成功后：

1. 构造与 CLI 相同结构的 result dict
2. 调用共享模块 `append_activation_result()`（从 CLI 抽到 `pallas/console/webui/` 或 `pallas/features/` 复用）
3. 用 `append_activation_note()` 生成 `message`
4. 前端按 `activation_action` 展示差异化 UI，并可选「立即重启」按钮

| activation_action | 用户提示（诚实） |
| --- | --- |
| `hot-reload` | 已在当前进程加载，无需重启 |
| `workers-restart` | 已安排仅重启 worker（或引导点重启） |
| `full-restart` | 需要重启 Bot 后生效 |
| `none` | 按策略说明是否仍需手动重启 |

`hot-reloadable` 在 WebUI 热加载失败时 fallback 全进程重启，文案须说明 fallback。

## 分阶段实施

### Phase 1 — WebUI 展示与返回语义

**范围**：`extension_install.py`、插件商店前端、测试  
**不做**：新 REST 重启 API（可复用已有 lifecycle）

1. 抽取 `append_activation_result` 为 WebUI/CLI 共用
2. 安装 API 返回 `activation_policy`、`activation_action`、`restart_scheduled`
3. 前端替换单一「请重启」文案
4. 子任务：按 activation_policy 展示官方扩展安装后的生效路径

**验收**：三类 policy 反馈不同；与 CLI 同包同语义。

### Phase 2 — WebUI 重启入口 + workers 调度

**范围**：`pb_webui` API、WebUI 运维区、分片 hub

1. 暴露受权 `POST /pallas/api/.../restart`（superuser），语义对齐 `pallas restart`
2. 参数：`workers_only`（分片 + workers-restart 场景）
3. 安装结果页、首页运维区放「重启 Bot」按钮（二次确认、loading、窄屏可用）
4. 子任务：WebUI 添加重启 Bot 入口

**验收**：维护者可从 WebUI 完成全进程重启；无权限不可调用。

### Phase 3 — `pallas plugin reload`

**范围**：CLI、`reload_policy_from_metadata()`、元数据索引

1. `pallas plugin reload <name>` 读取 `reload_policy`
2. `config_only`：提示已支持 WebUI 热载
3. `metadata` / `full`：调用 `reload_plugin_metadata_index()`；`full` 尝试模块重载，失败提示重启
4. 文档更新 `hot-reload-tiers.md` 运维表

### Phase 4 — hot-reloadable PoC

**范围**：draw、bot-status；unified 模式

1. 验证 `_hot_load_package_modules` 在 WebUI 安装路径下可复用
2. 记录 NoneBot 限制与失败模式（卸载旧 matcher 不可行等）
3. 失败时文档化阻塞原因，不夸大能力

**现状（2026-06-23）**

- WebUI / CLI 安装路径经 `extension_ops` → `append_activation_result` 复用 `_hot_load_package_modules`。
- **unified 模式**：`hot-reloadable` 扩展（`pallas-plugin-draw`、`pallas-plugin-bot-status`）在 pip 安装成功后**即尝试**运行时加载，无需勾选「安装并重启」；成功则 `activation_action=hot-reload`。
- **热加载失败 + 用户勾选重启**：fallback 全进程重启，返回 `hot_load_fallback` 与诚实文案。
- **分片模式**：`hot-reloadable` 仍走 pending 提示 + 全进程/worker 重启，不在 worker 内做 pip 热插拔。

**已知限制（不夸大能力）**

| 限制 | 说明 |
| --- | --- |
| 无 matcher 卸载 | NoneBot 不支持卸载已注册 matcher；**更新**已加载扩展可能重复注册或行为异常，PoC 仅覆盖**首次安装后加载** |
| 同名槽位已占用 | `_load_plugin_module` 见 `loaded_short` 已有时跳过，热加载返回失败 |
| 模块未发现 | pip 成功但 `importlib.find_spec` 失败时热加载失败 |
| 分片 / hub 角色 | 不在 worker 进程内对 hub-only 扩展做热加载 |
| 卸载 | pip uninstall 后已加载 matcher 仍在内存，须重启 |

**验收**

- unified + draw/bot-status 安装成功后可 `hot-reload`（或 honest fallback）
- 测试覆盖：无 restart 热加载成功、热加载失败 fallback 重启

## API 草案（Phase 2）

```
POST /pallas/api/system/restart
Body: { "workers_only": false }
Auth: superuser / 维护者
Response: { "scheduled": true, "mode": "full-restart" | "workers-restart" }
```

具体路径与权限与现有 `pb_webui` 路由风格对齐；实现前 grep `schedule_bot_restart` 复用点。

## 测试要点

- `extension_install` 返回字段与 CLI 一致（mock `schedule_bot_restart`）
- draw / duel 等包对应 `activation_policy` 快照
- 分片 workers_only 分支
- WebUI 重启 API 权限拒绝

## 风险

| 风险 | 缓解 |
| --- | --- |
| 热加载后 matcher 重复注册 | PoC 阶段仅 unified + 明确扩展名单 |
| WebUI 误触全进程重启 | 二次确认 + 权限 |
| 声明与执行长期不一致 | Phase 1 先诚实文案，Phase 4 再收窄 gap |

## 参考代码

- `pallas/console/cli/extension_activation.py`
- `pallas/console/webui/extension_install.py`
- `pallas/core/platform/bot_runtime/plugin_matrix.py`
- `pallas/core/plugin_reload/metadata_index.py`

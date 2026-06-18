# 插件目录约定

> **4.0 起**：内置插件在 `packages/`；`src/` 已移除。社区 API 入口为 `pallas.api.*`。本文档约束 `packages/*` 下的插件组织方式。

## 最小插件结构

每个插件至少包含：

- `__init__.py`：插件注册与 metadata（**core 保持薄**，目标 ≤120 行）
- `config.py`：插件配置项定义（无插件页配置时可 re-export `features/` 层）

按需：`handlers.py`（口令逻辑）、`startup.py`（启动/HTTP）。参照 `pb_core`、`pb_stats`；细则见 [内核插件统一化](core-plugin-unification-design.md)。

## 推荐扩展结构（按需）

当插件复杂度上升时，优先按功能拆分文件；仅在逻辑边界已经清晰且持续增长时，再引入通用分层目录：

- 功能分层（首选）：按业务能力拆分，例如 `plugin_manager.py`、`renderer.py`、`ban_manager.py`、`speaker.py`
- `handlers.py`: 事件/命令处理逻辑（按需）
- `models.py`: 领域模型或数据结构（按需）
- `services/`: 业务服务层（可选，适用于复杂逻辑持续增长）
- `repositories.py`: 持久化访问封装（可选，适用于数据访问复杂度上升）

> 不要求一次性改造历史插件；优先对新增插件和正在修改的插件执行。

## 代码组织原则

1. `__init__.py` 尽量保持轻量，避免堆积大量业务实现
2. 配置读取与默认值统一放在 `config.py`
3. 优先采用“按功能分层”的文件组织方式，命名直接体现业务能力
4. 当某类逻辑边界清晰、可复用且持续增长时，再引入 `services/`、`repositories.py` 等通用分层
5. 插件内部私有能力优先放插件目录；跨插件复用后再提取到 `pallas/`
6. 避免”超大单文件”，单文件过长时按职责拆分

## 插件路径约定

- 持久化数据使用 `data/<plugin_name>/...`。
- 资源文件使用全局目录 `resource/...`。
- 插件代码中优先通过 `pallas.api.paths` 的统一 helper 获取路径，不直接硬编码相对路径字符串。

说明：这样做可以避免运行目录变化导致路径漂移，也能统一备份与清理策略。

项目内实际示例：

- `packages/greeting/` 使用 `plugin_data_dir(“greeting”)` 作为插件数据目录入口。
- `packages/greeting/voice.py` 使用 `resource_dir(“voices”)` 读取语音资源目录。
- `packages/help/renderer.py` 与 `packages/help/plugin_manager.py` 使用 `plugin_data_dir(“help”)` 管理缓存目录。
- `packages/request_handler/` 使用 `plugin_data_dir(“request_handler”)` 管理申请缓存目录。
- `pallas/api/paths/` 提供统一路径 helper，作为插件路径访问的推荐入口。

## 命名建议

- 文件名优先使用语义名：`handlers.py`、`speaker.py`、`ban_manager.py`
- 同层目录命名保持一致风格（小写 + 下划线）
- 避免缩写命名，除非是领域内通用缩写

## WebUI 配置与命令权限

- **插件页治理与社区 L1/L2 画像**：[plugin-governance-community-roadmap.md](plugin-governance-community-roadmap.md)
- **`PluginMetadata.extra` 键名表**（`command_permissions`、`plugin_storage`、`ingress_route` 等）：见 [core-devx-roadmap.md · 内核键名约定](core-devx-roadmap.md#内核键名约定)。
- **新内核插件包名**：`pb_<role>`（如 `pb_core`、`pb_webui`、`pb_protocol`、`pb_stats`）。历史名经 `plugin_package_aliases.py` 别名兼容。
- 需在 WebUI 保存 **`webui.json`** 后立即生效的插件配置：插件页用 `install_hot_reload_config`（`pallas.api.config`）；横切项在 `env_sections.py` 注册（见 [WebUI 插件配置](../common/webui/README.md)）。
- **元数据热载**：`extra["reload_policy"]: "metadata"` 时保存插件配置可重建 help/ingress 索引（见 [hot-reload-tiers.md](hot-reload-tiers.md)）。
- 可配置命令权限：在 `PluginMetadata.extra` 声明 `command_permissions`，matcher 使用 `pallas.api.perm.group_message_permission_for_command`（见 [cmd_perm](../common/cmd_perm/README.md)）。
- 命令冷却：在 handler 内使用 `pallas.api.limits`（见 [command_limits](../common/command_limits/README.md)）；可在 `extra["command_limits"]` 声明默认 CD 供文档与后续扩展。
- **插件存储键**：在 `extra["plugin_storage"]` 声明群/用户/牛级数据键；读写使用 `pallas.api.storage.GroupPluginStorage` 或 `get/set_plugin_storage`（见 [develop/plugin/structure.md](../develop/plugin/structure.md)）。

### 命令权限与帮助文案（cmd_perm）

新增或修改**可独立配置权限**的命令时：

- 在 `PluginMetadata.extra["command_permissions"]` 和/或 `pallas/core/perm/registry.py` 声明默认等级；Matcher 使用 `permission_for_command` / `group_message_permission_for_command` 等同 ID。
- **`usage`、`menu_data.trigger_condition` 不写死「群管/群主」等**；帮助二级/三级图的「何人可用」由 `command_permission(s)` 与运行中覆盖动态生成。
- `usage` 末行可统一指向牛牛帮助（见 [cmd_perm 接入说明](../common/cmd_perm/README.md)）。
- 与发送者权限无关的额外条件（如本 Bot 须为 QQ 群管）写在 `detail_des` 或 `docs/plugins/<name>/README.md`。

## 站点覆盖与内核 import

`local/plugins` 整包覆盖同名插件时，NoneBot 只加载 local 槽位；内核层（AI callback、WebUI、probe）若仍 hardcode `src.plugins.<名>`，会出现命令与收尾分裂。  
约定与收敛进度见 **[AI 终态架构 §6](pallas-final-ai-shape.md)** 与 **[AI 实施 §4](pallas-ai-implementation.md)**。

## 测试配套约定

- 插件测试放在 `tests/plugins/<plugin_name>/`
- 新增行为优先附带最小可验证测试
- 历史问题应在 PR 说明中标注为“历史问题”或“本次引入问题”

## 迁移策略（建议）

1. 先新增约定，不直接重排历史目录
2. 先从高频改动插件开始（如 `greeting`、`repeater`）
3. 每次仅做一类整理：要么拆文件，要么迁文档，要么补测试

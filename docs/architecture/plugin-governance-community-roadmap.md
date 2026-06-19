# 插件治理与社区生态路线

> **状态**：拟定 · **分支**：`dev`  
> **现行总纲**：见 [Pallas 核心契约](pallas-core-contract.md)。  
> **背景**：社区插件商店与 `local/plugins` 已起步；站长希望在 WebUI **点进单个插件** 即可查看全部指令，并集中管理启停、权限、CD 等。参考 [GsUID Core](https://github.com/Genshin-bots/gsuid_core)、[绪山真寻 Bot](https://github.com/zhenxun-org/zhenxun_bot) 的「声明即帮助/即治理」，**不**照搬其运行时框架（AmiyaBot 仅参考商店交互，见 [pallas-4.0-slim](pallas-4.0-slim.md)）。  
> **与现有路线关系**：本方案是 [core-devx-roadmap](core-devx-roadmap.md)（SDK + extra 键表）与 [社区插件开发者指南](../guide/community-plugin-author.md) 的 **WebUI/治理落地**；core 插件 golden 仍见 [core-plugin-unification-design](core-plugin-unification-design.md)。

## 目标

| 维度 | 目标 | 验收信号 |
| --- | --- | --- |
| 站长可观测 | 插件页展示该插件全部口令与能力声明 | 与群内「牛牛帮助」条目一致、可对照 command_id |
| 站长可治理 | 常用启停/权限/CD 在插件页完成，少跳通用配置 | 保存后热生效或文档标明需重启的项 |
| 作者可预期 | 社区插件有 **L1/L2 画像**，非 core 目录也能接入 | `community_plugin_author.py check` 与索引策展引用同一规则 |
| 内核不膨胀 | 复用 `cmd_perm`、`command_limits`、`help/plugin_manager` | 不新增与 extra 双源的 per-plugin pm 整数体系 |
| 生态低门槛 | 示例插件 + 稳定 `features/*` 公开面 | 第三方仅依赖文档白名单模块 |

## 非目标

- 替换 NoneBot matcher 或实现 AmiyaBot 式 **代码级** `install/uninstall` 热载（仍重启改 Python，见 [hot-reload-tiers](hot-reload-tiers.md)）
- 运行时修改 matcher `priority`（ingress 软排序留作远期可选）
- 真寻/ZXPM 式 **整数权限等级** 与插件级 `plugin2cd.yaml` 第二套 CD 源
- 强制社区作者采用 `pb_*` 包名或 core golden 目录（`handlers.py` + ≤120 行 `__init__.py`）

---

## 现状摘要

### 已有（不必重造）

| 能力 | 实现 | WebUI 入口 |
| --- | --- | --- |
| 命令权限声明与覆盖 | `extra.command_permissions` + `cmd_perm` | 通用配置 → 命令权限 |
| 命令 CD 声明与覆盖 | `extra.command_limits` + `command_limits` | 通用配置 → 命令冷却 |
| 插件启停（多层） | `help/plugin_manager` + DB `disabled_plugins` | 插件页运行控制、实例页、群社交配置 |
| 全实例禁用 + 群白名单 | `global_disable`、`group_fleet_whitelist` | 插件页 |
| 能力聚合 API | `build_plugin_capabilities_ui()` | 插件页「能力总览」仅 **计数**，未绑定选中插件 |
| 帮助/menu 元数据 | `menu_data`、`usage` 在 `GET /plugins` | 插件页未展示指令列表 |
| 社区安装链 | 索引、`local/plugins`、Git 安装 | 插件商店 |
| 作者 CLI | `tools/community_plugin_author.py check` | 仅结构/ID/图标/README |

### 短板

1. **治理 UI 分散**：权限/CD 在通用配置全站矩阵；插件页只有业务 `config` 与部分运行控制。
2. **指令不可见**：点进插件看不到 `menu_data` / `capabilities.commands` 全表。
3. **社区规格偏薄**：作者指南未定义 L1/L2 声明完整度；`check` 不校验 `command_permissions` 与 `menu_data` 一致性。
4. **第三方公开 API 未单独成文**：依赖边界散见于 Cookbook 与 AGENTS.md。

---

## 设计原则

1. **声明在 extra，业务在 config，覆盖在 webui.json**（与 [settings-storage](settings-storage.md)、[core-devx-roadmap · 内核键名约定](core-devx-roadmap.md#内核键名约定) 一致）。
2. **命令 ID 为治理主键**（`<plugin>.<action>`），权限/CD/帮助/help 菜单共用同一 ID（[cmd_perm](../common/cmd_perm/README.md)）。
3. **Core 严格、社区宽松**：主仓 `pb_*` golden；社区 **L1 画像** 即可进索引，L2 为推荐优选。
4. **能聚合展示的不新建存储**：优先扩展现有 API 响应，避免 `plugin_governance` 与 `cmd_perm` 双写（首版不新增独立落盘段，见下文分期）。
5. **WebUI 窄屏可用**：新面板遵循 [Pallas-Bot-WebUI AGENTS.md](https://github.com/PallasBot/Pallas-Bot-WebUI/blob/main/AGENTS.md) ≤560px 规则。

---

## 社区插件画像（L0–L3）

与 [community-plugin-author.md](../guide/community-plugin-author.md) 目录要求 **叠加**，不替代 NoneBot 最小结构。

| 档位 | 作者要求 | 站点获得 | 索引策展 |
| --- | --- | --- | --- |
| **L0 兼容** | NoneBot 包 + `PluginMetadata` | 可加载；帮助/控制台信息少 | 一般不推荐公开收录 |
| **L1 推荐** | L0 + `command_permissions` + `menu_data` + 规范 `usage`/`description` | 帮助图、「何人可用」、**插件页指令表**、`/plugins/capabilities` 有数据 | **公开收录默认门槛** |
| **L2 增强** | L1 + `command_limits` + matcher 鉴权一致；口令推荐 [plugin_sdk](core-devx-roadmap.md#p1--plugin_sdk) | 站长可配 CD；可选 `config.py` 热重载 | 商店「优选」标签（可选） |
| **L3 商店完整** | L2 + `assets/icon.png` + README + `check` 零 error + `min_pallas_version` | 商店卡片、详情、图标推断 | 索引 PR 合并条件 |

### L1 最小 metadata 形状（社区作者复制基线）

```python
from src.features.cmd_perm.declare import command_perm_list, command_perm_row
from src.features.plugin_sdk import command_limit_list, command_limit_row  # L2

__plugin_meta__ = PluginMetadata(
    name="示例插件",
    description="一句话说明。",
    usage="...",  # usage_line + join_usage；不写死权限角色
    extra={
        "version": "3.0.0",
        "command_permissions": command_perm_list(
            command_perm_row("my_plugin.action", "示例口令", "everyone"),
        ),
        "menu_data": [
            {
                "func": "示例功能",
                "trigger_method": "on_cmd",
                "trigger_scene": "群内",
                "trigger_condition": "牛牛示例",
                "command_permission": "my_plugin.action",
                "brief_des": "简介。",
            },
        ],
        # L2:
        # "command_limits": command_limit_list(
        #     command_limit_row("my_plugin.action", 60),
        # ),
    },
)
```

约束与 [cmd_perm 维护者细则](../common/cmd_perm/README.md) 一致：`trigger_condition` 不写权限角色；权限由帮助图与 WebUI 动态展示。

### 第三方可依赖的公开面（白名单）

社区插件 **仅建议** import：

| 模块 | 用途 |
| --- | --- |
| `src.features.plugin_sdk` | 口令注册、CD/权限封装 |
| `src.features.cmd_perm` | 鉴权 helper |
| `src.features.command_limits` | CD helper |
| `src.features.plugin_storage` | 声明式群/用户存储 |
| `src.console.webui` | `install_hot_reload_config`（可选） |

其余 `src.plugins.*`、`src.platform.*` 视为内部；破坏性变更走 4.x minor 说明或 alias 一周期（与 core-devx 一致）。

---

## 插件页信息架构（WebUI）

点选插件 `sing` 后，`PluginConfigWorkspace` 建议分区（自上而下）：

```text
┌─ 概览 ─────────────────────┐  标题、描述、来源、usage 摘要
├─ 指令与能力 ───────────────┤  menu_data × capabilities 合并表
├─ 运行控制 ─────────────────┤  已有：全实例禁用、群白名单、帮助可见
├─ 命令权限 / 冷却 ──────────┤  仅本插件命令；保存写 webui.json 覆盖项
├─ 业务配置 ─────────────────┤  现有 config fields
└─ 高级链接 ─────────────────┘  只读：本插件在哪些群/实例被禁用 → 跳转
```

### 指令表字段（合并规则）

| 列 | 优先来源 | 说明 |
| --- | --- | --- |
| 功能名 | `menu_data.func` | 无 menu 时用 `capabilities.label` |
| 触发方式 | `menu_data.trigger_condition` | 面向用户 |
| 场景 | `menu_data.trigger_scene` | 群内/私聊/自动 |
| 命令 ID | `capabilities.command_id` | 维护者 |
| 何人可用 | `capabilities.effective_level` | 与 cmd_perm 一致 |
| CD（秒） | `capabilities.effective_cd_sec` | 0 表示无 CD |
| 简介 | `menu_data.brief_des` | 可选 |

合并键：`command_id`；仅有 menu 无 perm 声明的行标「未登记权限」；仅有 perm 无 menu 的行仍展示（兼容维护者向命令）。

窄屏：列多时使用卡片列表（参考 WebUI `DatabaseBackupsPage` 模式），避免横向表格错位。

---

## API 分期

与 [WebUI API · 插件](../common/webui/api/02-plugins.md) 对齐；**首版以扩展现有路径为主**。

### P0 · 只读聚合（WebUI + 可选 Bot 零行为变更）

| 变更 | 说明 |
| --- | --- |
| `GET /plugins/{name}/config` 增加 `governance` 或顶层字段 | 注入：`capabilities` 中该插件行；`menu_data` 自 `GET /plugins` metadata；`usage` 摘要 |
| 或新增 `GET /plugins/{name}/governance` | 仅读；返回 `{ commands, menu_items, runtime, perm_ui_filtered, limits_ui_filtered }` |
| WebUI | `PluginConfigWorkspace` 增加「指令与能力」折叠区；复用 `fetchPluginCapabilities` + 已选 `pluginRow` |

验收：任意 L1 社区插件安装后，插件页可见全部声明口令；与「牛牛帮助」二级项无矛盾。

### P1 · 插件页写权限/CD + 运行控制合一保存

| 变更 | 说明 |
| --- | --- |
| `PUT /plugins/{name}/governance` | Body：`command_permission_overrides`、`command_limit_overrides`（仅本插件 ID 前缀）、`global_disable`、`help_hidden` |
| 落盘 | 仍写 `webui.json` → `PALLAS_COMMAND_PERMISSION_OVERRIDES` / `PALLAS_COMMAND_LIMIT_OVERRIDES`；复用 `env_sections` 清缓存逻辑 |
| WebUI | 从 `CommonConfigPage` 抽取 `CommandPermMatrix` / limits 表，传 `pluginFilter` |

验收：在 sing 插件页修改 `sing.*` 权限与 CD，无需打开通用配置；保存后 matcher 鉴权生效。

### P2 · 作者工具与索引策展

| 变更 | 说明 |
| --- | --- |
| `validate_community_plugin_dir` | 校验 L1/L2 metadata 完整度、`menu_data.command_permission` / `command_limits` 与声明 ID 一致性 |
| `check --profile L1\|L2` | 输出画像档位与命令 ID 摘要 JSON |
| 索引仓 README | 公开收录默认要求 L1；L2 为优选 |
| 示例 | `examples/community_golden_plugin/` 或独立模板仓（L1/L2 各一） |

### P3 · 可选增强（社区成熟后再做）

| 项 | 说明 |
| --- | --- |
| per-plugin 用户/群黑白名单 | 新 feature `plugin_governance.gate`，在 `help/event_preprocessor` 前检查；**不**替代 `blacklist` 插件 |
| ingress `priority_offset` | 只读展示代码 priority；WebUI 改 priority 仍非目标 |
| `sdk_min_version` 启动 warn | extra 拟定键，见 core-devx-roadmap |

---

## 运行时治理（不新增双源）

启停与禁用 **继续** 使用现有链，插件页仅聚合展示：

```text
全实例禁用 (webui.json)
    ↓
单牛 disabled_plugins (BotConfig)
    ↓
单群 disabled_plugins (GroupConfig)
    ↓
群舰队白名单 (豁免全实例禁用)
    ↓
run_preprocessor: check_plugin_enabled (help/event_preprocessor.py)
```

权限/CD：

```text
extra 默认 → webui.json 覆盖 → permission_for_command / command_limits
```

超管豁免：保持 `superuser_bypasses_plugin_disable`。

---

## 与参照项目的差异（为何这样设计）

| 参照 | 借鉴 | 不照搬 |
| --- | --- | --- |
| GsUID | 单插件页集中展示与配置 | 每插件 dict 含 pm/priority/黑白名单 |
| 真寻 | `menu_data` 自动 help；多作用域启停；插件列表看功能 | ZXPM 整数权限；`plugin2cd.yaml` 第二 CD 源 |
| AmiyaBot | 商店安装、JsonSchema 业务配置 | 自研 handler 栈与运行时装拆 |

Pallas 差异化：**命令级** 权限/CD + **声明聚合 API** + NoneBot 生态兼容。

---

## 里程碑与验收

| ID | 内容 | 仓 | 验收 |
| --- | --- | --- | --- |
| **G-P0** | 插件页指令与能力只读表 | WebUI (+ 可选 Bot 扩展 GET) | L1 插件全指令可见；窄屏卡片可用 |
| **G-P1** | 插件页 perm/CD 编辑 + governance PUT | Bot + WebUI | 单插件保存覆盖生效 |
| **G-P2** | 社区 L1/L2 画像文档 + `check` 增强 + 示例插件 | Bot + Docs | 索引 PR 可引用 `--profile L1` |
| **G-P3** | 可选名单 gate / 高级治理 | Bot | 有独立设计 PR，不阻塞 P0–P2 |

### G-P0 自检清单（WebUI）

- [ ] 选中插件后「指令与能力」默认展开或易发现
- [ ] 展示 `trigger_condition` 与 effective 权限/CD
- [ ] 无 `menu_data` 时仍列出 `capabilities.commands`
- [ ] ≤560px 无表头错位、按钮不挤占标题行

### G-P2 自检清单（作者）

- [x] `uv run python tools/community_plugin_author.py check ./my_plugin --profile L1` 通过
- [ ] 安装到 `local/plugins/` 后插件页与帮助图一致
- [ ] README 注明 `min_pallas_version` 与公开面白名单

---

## 相关文档与代码

| 项 | 位置 |
| --- | --- |
| extra 键权威表 | [core-devx-roadmap.md · 内核键名约定](core-devx-roadmap.md#内核键名约定) |
| Core golden | [core-plugin-unification-design.md](core-plugin-unification-design.md) |
| 插件目录约定 | [plugin-convention.md](plugin-convention.md) |
| 社区作者 | [community-plugin-author.md](../guide/community-plugin-author.md) |
| 商店 | [community-plugin-store.md](../guide/community-plugin-store.md) |
| WebUI API | [02-plugins.md](../common/webui/api/02-plugins.md) |
| cmd_perm / limits | [cmd_perm](../common/cmd_perm/README.md)、[command_limits](../common/command_limits/README.md) |
| 能力聚合 | `src/features/plugin_capabilities/schema.py` |
| 禁用门控 | `src/plugins/help/event_preprocessor.py`、`plugin_manager.py` |
| 插件页 UI | Pallas-Bot-WebUI `PluginConfigWorkspace.vue`、`PluginsPage.vue` |
| Golden checklist | [08-golden-plugin-checklist.md](../skills/pallas-plugin-development/references/08-golden-plugin-checklist.md) |

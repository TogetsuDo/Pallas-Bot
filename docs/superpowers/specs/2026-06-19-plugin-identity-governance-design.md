# Pallas 插件身份治理与迁移设计

> 状态：draft confirmed in chat  
> 日期：2026-06-19  
> 范围：主仓 `Pallas-Bot` + 官方扩展仓的插件身份、解析、兼容、自检与迁移计划  
> 目标：把插件身份从“多个名称并行漂移”收口到“单一真相 + 统一消费 + 可验证迁移”

## 1. 背景

本轮排障暴露了两个表面不同、结构上同类的问题：

1. `community_stats` 仍通过旧路径 `packages.bot_status` 访问扩展能力，导致定时任务在运行期崩溃。
2. `relogin_bot` 的 hub 转发通过模糊模块解析命中了 `pallas_plugin_protocol.service`，而不是 `pallas_plugin_relogin_bot.service`，导致“牛牛重新上号”在真实流量上失效。

这两类问题都说明：当前内核对“插件是谁、从哪里加载、该用哪个模块入口、业务层该拿什么作为插件身份”没有单一真相。

## 2. 问题定义

当前仓内并存多种插件名称形态：

- 规范插件 ID，如 `bot_status`、`draw`、`relogin_bot`、`pb_stats`
- bundled 模块入口，如 `packages.help`、`packages.pb_protocol`
- pip 模块入口，如 `pallas_plugin_bot_status`、`pallas_plugin_draw`
- legacy alias，如 `community_stats -> pb_stats`
- pip package 名，如 `pallas-plugin-protocol`

这些名称目前被不同模块直接消费，形成以下结构缺陷：

- 业务代码能直接依赖具体模块路径，导致迁移后运行期崩溃。
- 解析器对同包多插件的映射不够严格，容易命中错误模块前缀。
- route index / matcher / help / 权限 / WebUI / 测试各自使用不同名称口径。
- 兼容逻辑分散在多处，无法知道哪些旧入口仍被依赖。
- 缺少启动期和 CI 级别的插件身份自检，错误只能在真实流量命中后暴露。

## 3. 目标

### 3.1 核心目标

建立一套覆盖主仓和官方扩展仓的插件身份治理体系，使：

- 内核只存在一个可消费的插件身份：`plugin_id`
- 所有解析、路由、权限、帮助、WebUI、日志和测试都通过 `plugin_id` 工作
- bundled / pip / alias / package 都退化为来源信息，而不是业务真相
- 兼容窗口可控、可审计、可退场
- 启动时和 CI 中能够主动发现插件身份漂移

### 3.2 设计目标

- 主仓先成为唯一真相，再逐步推动官方扩展仓适配
- 不要求一次性重写全部插件，只要求建立统一模型和阶段计划
- 对用户面兼容保持温和，对代码面兼容保持收敛

## 4. 非目标

- 不在本设计内统一所有插件业务逻辑
- 不把插件体系改造成新的框架或包管理器
- 不在第一阶段强制社区第三方插件立即遵循全部规则
- 不要求一次性消除所有 legacy alias

## 5. 单一身份模型

### 5.1 规范身份

内核唯一允许被业务消费的插件身份是 `plugin_id`。

示例：

- `help`
- `pb_protocol`
- `relogin_bot`
- `bot_status`
- `draw`
- `pb_stats`

`plugin_id` 是以下系统的唯一键：

- route index
- matcher 归因
- help 可见性
- command permission / cooldown
- WebUI 插件治理
- 子模块解析入口
- 日志归因
- 测试假插件工厂

### 5.2 来源身份

以下名称不再被业务直接消费，只作为解析层输入或注册表元数据存在：

- `packages.<name>`
- `pallas_plugin_<name>`
- legacy alias
- pip package 名

规则：

> 任何模块一旦需要“认插件”，必须先从原始名字归一化到 `plugin_id`，再继续后续逻辑。

## 6. 中心注册表

主仓需要建立一个插件身份注册中心，作为插件身份单一真相。

建议注册项包含：

- `plugin_id`
- `kind`: `core` / `extra` / `shard-internal` / `local`
- `bundled_module_prefix`
- `pip_module_prefix`
- `pip_package`
- `legacy_aliases`
- `default_load_roles`
- `allow_submodule_import`
- `display_name`
- `help_hidden_default`

### 6.1 注册表职责

注册表只做三件事：

1. 描述 `plugin_id` 与各种来源名字的映射关系
2. 提供统一归一化 API：`raw -> plugin_id`
3. 提供统一反查 API：`plugin_id -> module_prefix / package / roles / aliases`

### 6.2 现有结构的调整方向

- `plugin_matrix` 从“装载表”升级为“身份注册表 + 装载元数据表”
- `plugin_package_aliases` 不再只是零散别名，而是注册表查询接口的一部分
- `EXTRA_PACKAGE_MODULES` 与 `EXTRA_PLUGIN_PACKAGES` 继续存在，但只作为注册表底层数据，不再被业务层散用

## 7. 消费分层

为了防止旧名字继续在内核流动，需要把插件身份消费明确分层。

### 7.1 解析层

负责：

- loader
- `import_plugin_submodule()`
- loaded plugin 识别
- bundled / pip / local 入口选择

允许接触原始模块名，但输出必须是：

- `plugin_id`
- 当前命中的模块前缀

### 7.2 运行层

负责：

- route index
- matcher 归因
- help 与 visibility
- permission / cooldown / limits
- WebUI 插件治理
- 日志归因

规则：

> 运行层禁止直接消费 `packages.*`、`pallas_plugin_*`、pip package 名，只能消费 `plugin_id`。

### 7.3 测试基建层

测试里不得再把原始模块路径当业务真相。

统一由测试辅助工厂构造：

- `plugin_id`
- `module_prefix`
- `metadata`
- `kind`

### 7.4 兼容层

兼容层应集中存在，职责仅为：

- 接收 legacy 名称
- 翻译到 `plugin_id`
- 发出兼容告警或统计

兼容层不能成为旧名字继续在业务层传播的通道。

## 8. 核心约束

### 8.1 主仓业务代码约束

主仓业务代码原则上不得直接 import：

- `packages.<extra_plugin>`
- `pallas_plugin_<name>`

如果业务需要访问扩展子模块，只能通过：

- `plugin_id`
- 统一的子模块解析 API

### 8.2 路由与 matcher 约束

route index、matcher 归因、事件派发使用的插件键必须统一经过 `canonical plugin_id` 归一化。

### 8.3 测试约束

测试中出现以下写法应逐步视为违规：

- 把 `packages.bot_status` 当作业务真相
- 把 `pallas_plugin_draw` 当作 route key
- 直接用模块末段代替 `plugin_id`

## 9. 兼容策略

### 9.1 用户面兼容

允许保留一个版本周期的兼容项：

- 旧配置键
- 旧文档名
- 旧帮助名

目标是让站长和用户不被立刻打断。

### 9.2 代码面兼容

代码面兼容应严格收缩：

- 可以短期集中承接 legacy alias
- 不建议新增散落式兼容壳
- 必须进入 CI 报警与淘汰计划

原则：

> 用户面兼容平滑，代码面兼容尽快退场。

## 10. 自检与治理机制

### 10.1 Identity Lint

新增主仓静态检查，扫描业务代码中是否直接引用：

- `packages.<extra_plugin>`
- `pallas_plugin_*`

命中后给出明确错误信息和建议改法。

当前主仓已落地 `tools/check_plugin_identity_imports.py`，并接入本地 pre-commit hook，默认检查 `pallas/`、`packages/`、`tests/`、`tools/`。

### 10.2 Resolver Audit

对官方插件逐个验证：

- `plugin_id`
- 预期模块前缀
- 关键子模块是否可导入

最小覆盖对象：

- `relogin_bot`
- `bot_status`
- `draw`
- `maa`
- `sing`
- `dream`
- `pb_protocol`

当前主仓已落地最小审计入口 `audit_plugin_submodule_targets()`，用于验证 `plugin_id -> module_prefix` 是否仍能解析到预期模块。

### 10.3 Loaded Plugin Audit

启动时对已加载插件进行一致性审计：

- loaded plugin name
- 实际 module prefix
- 解析得到的 `plugin_id`
- metadata 中的归属

若出现漂移，应显式 warning，而不是静默容忍。

### 10.4 测试工厂

新增统一测试辅助：

- fake loaded plugin builder
- fake route plugin builder
- fake metadata builder

目标是让测试不再写死旧模块路径。

当前主仓已先完成一批 registry-safe fixture 迁移：`command_limits`、`WebUI env sections`、`route index`、`bot_status` 相关测试都不再把 `packages.bot_status` 当业务真相，并避免对缺失的 `packages.maa` / `packages.sing` 形成硬依赖。

## 11. 分阶段迁移计划

### Phase A：主仓唯一真相

范围：

- 中心注册表
- `canonical plugin_id` API
- `import_plugin_submodule()` 重构
- loaded plugin 识别统一化
- route index key 统一化

完成标准：

- 主仓核心解析链只以 `plugin_id` 作为业务身份
- `relogin_bot` / `bot_status` / `draw` 类问题可由注册表避免

状态更新：

- 已完成：中心 registry、`canonical plugin_id` API、resolver registry 化、loaded plugin canonical 匹配、route index key canonical 化
- 已完成：最小 resolver audit 与 identity lint

### Phase B：主仓消费层清洗

范围：

- help / visibility
- permission / cooldown
- WebUI 插件页
- 日志归因
- 测试基建迁移

完成标准：

- 主仓业务消费层不再直接依赖模块路径
- 旧测试入口明显减少

状态更新：

- 部分完成：`command_limits`、`WebUI env sections`、`help` 兼容消费面已对齐或补兼容
- 未完成：更广范围的主仓业务层清理、启动期 loaded-plugin audit 展示

### Phase C：官方扩展仓适配

范围：

- `pallas-plugin-protocol`
- `pallas-plugin-bot-status`
- `pallas-plugin-draw`
- `pallas-plugin-maa`
- `pallas-plugin-dream`
- 其它官方扩展

完成标准：

- 每个扩展都有统一入口、自检和元数据约定
- 主仓能按同一模型解析所有官方扩展

### Phase D：兼容退场

范围：

- 移除代码面旧路径兼容
- 保留必要用户面 alias
- 调整文档与测试约束为硬规则

完成标准：

- 旧代码入口不再是开发面允许写法
- 插件身份体系长期稳定

## 12. 第一批建议落地项

第一批最值得做的不是“清全仓旧 import”，而是先堵结构口子：

1. 中心注册表
2. resolver 只通过注册表解析
3. route index / matcher 键统一为 `plugin_id`
4. identity lint
5. resolver audit
6. 测试辅助工厂

这批完成后，后续清理旧路径会变成“按规则替换”，而不是继续边修边猜。

当前进度：前 1-5 项已在主仓落地；第 6 项尚未抽成统一测试工厂模块，但关键测试已迁到统一的 registry-safe fixture 写法。

## 13. 风险与权衡

### 13.1 风险

- 需要同时触及 loader、route、tests、WebUI 等多个横切模块
- 主仓和扩展仓存在版本错位窗口
- 一些旧测试会在迁移初期批量失败

### 13.2 缓解

- 先做 Phase A，确保主仓先稳定
- 兼容层集中托管，不新增散落式 shim
- 让 CI 自检先报警，再分阶段转为硬失败

## 14. 验收标准

满足以下条件，可认为插件身份治理完成到“可持续阶段”：

- 主仓业务层只消费 `plugin_id`
- 官方插件解析统一走注册表
- route index / matcher / help / perm / WebUI 键名一致
- 启动期能发现解析漂移
- CI 能阻止新增旧路径硬编码
- 官方扩展仓完成统一入口适配

## 15. 建议实施顺序

建议按以下顺序推进：

1. 写注册表与解析 API
2. 收 resolver / route index / loaded plugin
3. 上 identity lint 和 resolver audit
4. 改测试基建
5. 清主仓业务消费层
6. 再推官方扩展仓适配

这能保证主仓先形成稳定核心，再向外推动全套治理。

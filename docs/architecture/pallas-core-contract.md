# Pallas 核心契约

> **状态**：现行总纲 · **日期**：2026-06-18  
> **目的**：用 Pallas 自己的产品与工程语言，统一描述本体的长期形态、品牌边界、代码边界与遗留建设项。  
> **替代关系**：本文件接管旧 4.0 总纲中仍有持续价值的部分；阶段性完成的 4.0 瘦身/视觉路线不再作为主入口维护。

## 1. 一句话

**Pallas 的品牌核心不是单体陪伴，而是以`语料底盘`为根、以`牛格`与`群味`为形、以`多牛社交`为主场的 AI 体。**

这意味着：

- Pallas **先是**语料驱动的基础复读系统，后才叠加 LLM、记忆与工具能力。
- Pallas 的人格首先服务于**群聊中的社交表现**，不是服务于一对一主陪伴关系。
- Pallas 的 AI 能力必须增强 `repeater` / `llm_chat` / `多牛协同`，而不是绕过这些能力另起一套产品。

## 2. Pallas 与参照项目的差异

### 2.1 借鉴什么

| 参照 | 借鉴点 |
| --- | --- |
| GsUID | 内核纪律、插件边界、控制台治理、插件仓分离 |
| AstrBot | AI-first 的中心化 runtime、统一任务/健康/队列语义 |
| MaiBot | persona、memory、陪伴感中可工程化的部分 |

### 2.2 不做成什么

| 方向 | Pallas 不做 |
| --- | --- |
| 运行时 | 不回退到“每个插件各自维护 provider / fallback / 熔断”的形态 |
| 产品核心 | 不做成以私聊主陪伴关系为第一目标的 MaiBot 路线 |
| 语料地位 | 不让 LLM 与记忆系统取代语料底盘成为默认主路径 |
| 人格来源 | 不让群味、牛格主要靠模型臆造，而脱离本机已学习语料 |

### 2.3 与 MaiBot 的品牌差异

Pallas 与 MaiBot 的本质差异不是“有没有 persona / memory”，而是**这些能力服务什么**：

- MaiBot 偏**单体陪伴**与关系连续性。
- Pallas 偏**群聊社交**与多牛分化。
- MaiBot 的 memory 首先服务“我和你”的关系。
- Pallas 的 memory 首先服务“这只牛在这个群里应该怎么说话、记得什么群内事实、如何延续群味”。
- MaiBot 可以把陪伴关系当产品根部。
- Pallas 必须把**语料底盘**当产品根部。

## 3. 三层体系

### 3.1 语料底盘（`corpus_foundation`）

这是 Pallas 的根。

组成：

- 本机学习语料
- `Context.answers`
- 基础复读命中与选句
- `repeater` 热路径
- 共享/联邦语料的读路径

原则：

1. **语料底盘优先**：能靠本地语料稳定完成的接话，不默认走 LLM。
2. **本机已学习语料优先塑形**：群味、候选句风格、接话统计口径都先看本机语料。
3. **LLM 不改写事实来源**：LLM 可以选句、润色、补位，但不能反向重写语料统计事实。

### 3.2 风格层（`persona_profile` + `group_flavor`）

这是 Pallas 的形。

组成：

- `persona_profile`：每只牛的基础牛格、行为档、archetype、情感轴
- `group_flavor`：群味、群内说话节奏、礼貌/冲度、口癖倾向
- `cross_group` 聚合：同一只牛跨群形成的稳定倾向
- `fanout` / 多牛分化：同群多头牛的差异化表现

原则：

1. **牛格是行为策略，不是大段设定文案。**
2. **群味是统计结果，不是 prompt 幻觉。**
3. **多牛差异必须可观测、可解释、可回退。**
4. **风格层只增强语料底盘，不替代语料底盘。**

### 3.3 增强层（`llm_runtime` + `memory_layers` + `tooling`）

这是 Pallas 的上层能力。

组成：

- `llm_runtime`：统一 Chat / Image / Media task
- `memory_layers`：会话记忆、群内记忆、关系备注、事件备注
- `tooling`：方舟知识、命令工具、外部能力
- `multi_bot_social`：主持牛、fanout、群内社交位置

原则：

1. LLM 是**增强层**，不是主路径。
2. memory 是**服务风格与社交一致性**，不是先服务陪伴叙事。
3. tools 是**确定性能力补充**，不是 persona 的替代品。

## 4. 代码职责边界

### 4.1 主仓 `Pallas-Bot`

主仓负责：

- 语料底盘
- 牛格 / 群味统计与解释
- 命令、权限、冷却、help、WebUI
- 接话、群内触发、消息发送
- 多牛、多群、分片、ingress、fanout
- 产品记忆策略

主仓不应长期负责：

- 多 provider fallback 编排
- image / sing / chat 各自独立健康状态机
- 媒体慢任务执行细节
- runtime 级 queue / circuit / callback 事实源

### 4.2 AI 仓 `Pallas-Bot-AI`

AI 仓负责：

- 统一 runtime
- provider / backend / routing / queue / circuit
- sync / async / hybrid 能力模式
- callback 任务收尾框架
- runtime health / diagnostics / metrics
- 运行时 session / task state

AI 仓不负责：

- 牛格定义权
- 群味统计权
- 产品人格最终解释权

## 5. 记忆分层契约

本节明确 Pallas 的 memory 不是一个总桶，而是多层分工。

| 中文名 | 工程名 | 用途 | 默认事实来源 |
| --- | --- | --- | --- |
| 会话记忆 | `session_memory` | 短期上下文、最近几轮对话 | 对话消息 |
| 群内旧事 | `episode_notes` | 群梗、被明确教导的群内事实、可检索摘要 | teach / 摘要 / 后续提炼 |
| 关系备注 | `relationship_notes` | 这只牛对某人/某类人的稳定关系备注 | 预设层 / 人工维护 / 后续审计通过的提炼 |
| 群味快照 | `group_flavor_snapshot` | 群体统计画像，供牛格解释 | 本机语料统计 |

原则：

1. `session_memory` 只解决“刚刚聊过什么”，不承载品牌人格。
2. `episode_notes` 只保存**对群聊有持续价值**的旧事，不做全量日记。
3. `relationship_notes` 是高门槛层，不能把短期情绪误写成稳定关系。
4. `group_flavor_snapshot` 是统计快照，不是用户可教导的随意记忆。

## 6. 当前建设结论（基于代码审计）

### 6.1 已基本成形

| 方向 | 结论 |
| --- | --- |
| 语料底盘 | 已成形；`repeater`、learn、群风格统计、本机语料口径都已是系统主轴 |
| 插件边界 | 已成形；`plugin_sdk`、capabilities、bundled/extra/local 分层明确 |
| AI runtime 接口 | 已成形；主仓与 AI 仓边界、callback hook、submodule resolve 已落代码 |
| 牛格 prompt 编译 | 已成形；`compile_persona_prompt`、group style、预设层可用 |

### 6.2 已有骨架但未收口

| 方向 | 现状 |
| --- | --- |
| LLM 接话 | `select` 已成默认推荐路径，`polish` 进入遗留态 |
| 会话记忆 | PG 会话与 TTL 已有，但多 worker / 高并发签收仍未完全收口 |
| 群内记忆 | teach + `episode_notes` 策略、注入上限、群内旧事文案已收口一轮，但仍是关键词检索级，不是完整记忆系统 |
| 插件治理页 | 单插件治理 API 已落地；插件页 UI 与作者画像校验闭环仍未完全收口 |

### 6.3 明确还未完成

| 方向 | 现状 |
| --- | --- |
| `multi_bot_social` 的品牌化收口 | 有 fanout / ingress / hosted activity，但缺总契约统一描述 |
| `relationship_notes` | 已落地按 `(bot,group,user)` 的写入/校正（upsert）/衰减（半衰期）与 prompt 注入；二级来源（审计提炼、自动观测写入）仍待补 |
| token 可观测闭环 | 日汇总与状态文本已接入；控制台表格与更细颗粒运维展示仍未全量收口 |
| memory infra 终态 | AI 仓侧运行时记忆基础设施仍未完成 |
| plugin governance 收尾 | 单插件 perm/CD 已有后端闭环；前端插件页聚合治理与作者 L1/L2 校验仍在途中 |

## 7. 仍需推进的建设项

### 7.1 语料底盘相关

- 控制面联邦语料剩余项：
  - `corpus_fed` 第二 PG
  - fleet 远程快照合并
  - heartbeat `actions` / write_fanout 增强
  - bootstrap 下发项从只读快照进入更多运行面，而不只是状态展示

### 7.2 牛格与群味相关

- `A6.4–A6.7` 继续收口：
  - archetype 分化可观测
  - affect triggers 闭环签收
  - scorer 内容加权验证
  - `compile_persona_prompt` 中段位文案补齐

### 7.3 LLM 与记忆相关

- reply gate 可观测与文档口径统一
- queue merge 完整接入与验证
- token 统计面板收口
- `episode_notes` 从 teach-only + 明确策略，继续升级到可控提炼
- `relationship_notes` 二级来源补齐：聊天观测自动写入、审计提炼通过后入库（契约/衰减规则已落地）

### 7.4 工具与知识相关

- 方舟 KB 已有统一 query / tool 主路径；MCP 暴露与口令查询统一仍待验收
- tool 黑名单、schema 瘦身、按需注入策略继续收口

### 7.5 插件与 WebUI 治理相关

- 单插件治理页：
  - 指令表可见性
  - per-plugin 权限/CD 保存
  - 作者 L1/L2 画像校验闭环

## 8. 旧 4.0 文档处理原则

以下旧文档不再作为“总入口”维护：

- `pallas-4.0-roadmap.md`
- `pallas-4.0-slim.md`

处理原则：

1. **已完成且纯阶段性**：可归档或删除。
2. **仍有未完成条目**：必须先迁入本文件或专项现行文档。
3. **仍被外部大量引用**：先改成“归档说明 + 指向新总契约”，再考虑后续删除。

## 9. 现行入口

- 本文件：Pallas 的品牌与系统总契约
- [pallas-final-ai-shape.md](pallas-final-ai-shape.md)：Bot ↔ AI 终态边界
- [persona-llm-roadmap.md](persona-llm-roadmap.md)：语言层与接话 LLM
- [llm-efficiency-roadmap.md](llm-efficiency-roadmap.md)：门控、记忆、tool、牛格增强
- [plugin-governance-community-roadmap.md](plugin-governance-community-roadmap.md)：插件治理与社区生态
- [control-plane-corpus-federation.md](control-plane-corpus-federation.md)：语料联邦与控制面

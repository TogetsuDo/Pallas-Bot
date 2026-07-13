# 运维 API

维护者可直接依赖的 API 入口（不做全量内部接口百科）。

## 首批关注哪些 API

你最常直接用到的通常是：

- 健康检查
- 控制台基础状态
- 插件治理相关接口
- 运行态与聚合状态接口

## 推荐先看这些接口域

| 域 | 用途 |
| --- | --- |
| 认证与健康检查 | 判断控制台与 Bot 是否在线 |
| 插件与插件配置 | 插件列表、配置、治理、可见性 |
| 通用配置 | 命令权限、消息审查、服务网关等 |
| 统计与仪表盘 | 运行态、日志、分片可观测 |

## 最常直接调用的接口

| 路径 | 用途 |
| --- | --- |
| `/pallas/api/health` | 最基础的健康检查 |
| `/pallas/api/system` | 控制台与系统状态 |
| `/pallas/api/bots` | 当前 Bot 在线状态 |
| `/pallas/api/plugins` | 插件 metadata 列表 |
| `/pallas/api/plugins/capabilities` | 插件能力聚合 |
| `/pallas/api/common-config/sections` | 通用配置段列表 |
| `/pallas/api/shard-observability` | 分片 worker 观测聚合 |

## 先理解这些接口的定位

这批接口主要承担三类职责：

- 控制台页面本身的数据来源
- 维护者排障时的直接观测入口
- 自动化脚本可谨慎依赖的基础运维接口

它们不等于「把主仓所有内部 FastAPI 路由都当作公开契约」。

## 按接口域理解，而不是按页面猜

### 认证与健康检查

优先用于判断：

- 控制台是否在线
- 当前会话或 token 是否有效
- Bot 基础状态是否能被读取

典型入口：

- `/pallas/api/health`
- `/pallas/api/system`
- `/pallas/api/bots`

### 插件与治理

优先用于判断：

- 插件列表是否正确
- capabilities 是否完整
- 单插件治理状态是否符合预期

典型入口：

- `/pallas/api/plugins`
- `/pallas/api/plugins/capabilities`
- `/pallas/api/plugins/{plugin_name}/governance`

### 通用配置

优先用于判断：

- 某个配置段是否已注册
- 当前值和默认值的关系
- 保存后是否能立即影响运行态

典型入口：

- `/pallas/api/common-config/sections`
- `/pallas/api/common-config/{section_id}`

### 分片与运行观测

优先用于判断：

- worker 是否都在线
- 聚合状态是否正常
- ingress / registry / observability 是否对得上

典型入口：

- `/pallas/api/shard-registry`
- `/pallas/api/shard-observability`
- `/pallas/api/ingress-dispatch`

## 维护者常见使用场景

### 看服务是否在线

优先看：

- `/health`
- `/system`

### 看插件状态是否对

优先看：

- `/plugins`
- `/plugins/capabilities`

### 看分片是否正常

优先看：

- `/shard-registry`
- `/shard-observability`
- `/ingress-dispatch`

## 写接口该怎么理解

以下以运维读取为主，但部分域也提供写接口，例如：

- 插件帮助可见性
- 全局禁用
- 单插件配置
- 通用配置段

把这些写接口理解成「控制台治理动作的后端契约」，而不是随意拼 JSON 的内部私有入口。

要做自动化写入时：

- 优先使用已经在文档分域里说明过的接口
- 先确认写操作是否要求单独写 token
- 先确认对应变更是热生效还是需要重启

## 使用边界

别把所有 JSON 结构都当成长期自动化契约。更稳妥的做法是：

- 健康检查和基础状态接口可以作为自动化入口
- 深层页面专用聚合结构，先按「控制台实现依赖」理解
- 要做长期外部集成，优先依赖本页列出的稳定域

## 自动化接入建议

做巡检、监控或简单运维脚本，建议优先依赖：

- `health`
- `system`
- `bots`
- `plugins`
- `plugins/capabilities`
- `common-config/sections`
- `shard-observability`

对于面向单个页面的深层聚合 JSON：

- 可以用于现场排障
- 不建议默认视为长期 semver 稳定契约

## 使用原则

- 把这些接口当成运维和排障入口
- 不要把尚未声明稳定的内部 JSON 结构当成长期契约
- 真要做自动化集成，优先依赖健康、插件治理、基础状态这类稳定域

## 相关阅读

- [WebUI API 总览](../../common/webui/api/README.md)
- [认证与健康检查](../../common/webui/api/01-auth-health.md)
- [插件 API](../../common/webui/api/02-plugins.md)
- [通用配置 API](../../common/webui/api/03-common-config.md)
- [仪表盘与统计 API](../../common/webui/api/04-stats-dashboard.md)

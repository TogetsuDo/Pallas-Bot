# multi_bot_social 品牌契约总述

> **OPT-DOC-010** · 维护者向：舰队、主持牛、fanout 与群味相关能力的统一入口说明。

## 1. 概念

| 术语 | 含义 |
| --- | --- |
| **舰队（fleet）** | 同站点多只牛牛共享群上下文；通过 `pallas.api.platform` 舰队 API 协作 |
| **主持牛（host bot）** | 群内承担 fanout / 去重 / 主持 gate 的代表牛牛 |
| **fanout** | 一条用户消息在舰队内只由一个 matcher 实例处理，避免 N 牛重复回复 |
| **群味（persona）** | 语料 + 牛格编译结果，影响复读与 LLM 接话风格 |

## 2. 维护者文档入口

| 主题 | 文档 |
| --- | --- |
| 入站与 fanout | [central-ingress-dispatch.md](central-ingress-dispatch.md) |
| 分片与 hub/worker | [bot_process_sharding.md](../bot_process_sharding.md) |
| 产品与边界 | [pallas-core-contract.md](pallas-core-contract.md) |
| 牛格 / 群味 | [persona 插件说明](../../plugins/persona/README.md) |

## 3. 插件作者边界

- 多 Bot 去重、群在线态、分片发送：**官方 / 内置** 通过 `pallas.api.platform`。
- 社区插件默认不依赖舰队 API；须文档说明时使用场景。
- 复读接话与 LLM 路径关系见 [llm-and-repeater.md](../../guide/llm-and-repeater.md)。

## 4. WebUI 与运维

- **实例**页：当前账号、连接状态、分片角色。
- **好友与群**：舰队白名单、群级配置。
- 重复前缀严格模式：`PALLAS_DUPLICATE_PREFIX_STRICT`（见 [site-customization-and-updates.md](../site-customization-and-updates.md)）。

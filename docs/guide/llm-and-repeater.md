# `@牛牛`、复读接话与 LLM 的关系

> 适用：4.0 `llm_chat` + `repeater` + `Pallas-Bot-AI`

Pallas 里有两条看起来都像“牛牛在说话”的路径，但它们不是一回事：

- **牛牛复读 / 接话**：先看本机学到的群聊语料，决定要不要接、怎么接
- **`@牛牛` 随时闲聊**：明确有人叫牛牛说话，走 `llm_chat`

理解这件事以后，很多“为什么这次像复读、为什么这次像 AI、为什么有时不回”就更容易判断。

## 一句话版本

Pallas 的默认顺序是：

1. **语料底盘优先**
2. **牛格 / 群味塑形**
3. **LLM 补位、轻润色、接旧事**

也就是说，Pallas 不追求把所有聊天都做成一个“通用大模型陪聊体”，而是先让牛牛更像这个群里长出来的牛。

## 两条路径分别是什么

### 1. 牛牛复读 / 接话

这是 [`repeater`](../plugins/repeater/README.md) 的能力。

特点：

- 平时群里正常聊天时自动生效
- 先参考本机学到的语料
- 会受牛格、群风格和群内上下文影响
- 不需要每次都走 LLM

### 2. `@牛牛` 随时闲聊

这是 [`llm_chat`](../plugins/llm_chat/README.md) 的能力。

特点：

- 只有群里明确 `@牛牛` 才会触发
- 走统一 LLM 能力层
- 会带会话记忆、群内旧事、关系备注、工具等能力
- 也会受到牛格和群味影响，但不是单纯复读

## 为什么两者会互相影响

因为 Pallas 不是把“复读”和“AI”完全割裂开的。

你看到的实际效果通常会同时受这些层影响：

- **语料底盘**：本机学到的群聊 message / answer
- **牛格**：这只牛的基础行为差异
- **群味**：这个群学出来的说话节奏、语气和偏好
- **群内旧事**：之前群里长期有价值的旧梗、旧约定、旧事实
- **关系备注**：这只牛对当前说话人的稳定关系印象
- **LLM**：补位、轻润色、多轮闲聊、工具调用

## `LLM_REPEATER_MODE` 是什么

这个配置控制 **LLM 会不会介入牛牛接话**。

| 值 | 含义 |
| --- | --- |
| `off` | 只用语料接话，不让 LLM 介入接话 |
| `fallback` | 语料不够时，让 LLM 补一口 |
| `polish` | 语料已有候选时，让 LLM 按牛格轻改写一下 |
| `both` | 既能 fallback，也能 polish |

用户感知上可以这样理解：

- `off`：更纯粹的语料牛
- `fallback`：语料接不上时，AI 帮忙补位
- `polish`：语料是底盘，但出口更顺、更像牛
- `both`：语料优先，AI 既能补位也能轻润色

## Repeater LLM pipeline

当前 `repeater` 的 LLM 增强按阶段顺序尝试：

1. grounded candidate `select`
2. grounded `rewrite` / `polish`
3. fallback `generate`

也就是说，Pallas 会先尽量在已有群语料上做选择和轻改写，只有前面的 grounded 路径都没走通时，才让 fallback 生成补位。

## 对话内核能力档位

`CONVERSATION_FEATURE_LEVEL` 用于控制 repeater 与 llm_chat 共享的对话内核收敛程度。留空时会按现有开关自动推断。

| 档位 | 含义 |
| --- | --- |
| `legacy_repeater` | 仅语料 + 规则 + 现有 persona/scorer，不依赖统一 decision 链路 |
| `repeater_plus_decision` | 启用统一 decision 与 trace，但不要求 feedback / writeback 全链路 |
| `full_conversation_kernel` | decision + generation + persona-affect + memory-learning 治理全启 |

老用户兼容原则：

- 未开启 `LLM_CHAT_ENABLED` 时，默认落在 `legacy_repeater`
- `LLM_REPEATER_FEEDBACK_ENABLED` / `LLM_REPEATER_BIAS_ENABLED` / `LLM_REPEATER_WRITEBACK_ENABLED` 默认关闭
- writeback 默认关闭，direct chat 原句不会无门槛写穿 repeater 主语料

## 为什么优化后可能“不总是回”

这通常不是坏事。

群聊里更自然的行为，本来就包括：

- 用户像还没说完时先等一下
- 别人和别人正在互聊时不抢话
- 已经说过一轮后不立刻补第二轮
- 有些时候只接一句，不把话说满

如果你感觉优化后“更像群友”，通常就会同时看到：

- 不再每条都回
- 回复变短一些
- 重复模板变少
- 没那么像客服式解释

## 什么时候优先看哪个文档

- 想看 `@牛牛` 怎么用：[`llm_chat`](../plugins/llm_chat/README.md)
- 想看平时接话 / 复读：[`repeater`](../plugins/repeater/README.md)
- 想看牛格和群味怎么来的：[`persona`](../plugins/persona/README.md)
- 想看 4.0 开关总览：[`4.0-start`](./4.0-start.md)

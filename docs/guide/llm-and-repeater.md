# `@牛牛`、复读接话与 LLM

群里牛「在说话」其实有两条路，别混成一件事：

| 路径 | 什么时候 | 本质 |
| --- | --- | --- |
| **复读 / 接话** | 平时群聊自动 | 先看本机学到的语料，再决定要不要接 |
| **`@牛牛` 闲聊** | 你明确叫它 | 走 `llm_chat` + AI |

默认顺序一句话：**语料优先 → 牛格 / 群味塑形 → LLM 补位或轻润色**。  
不是把所有聊天都做成「通用大模型陪聊」，而是先让牛更像这个群里长出来的。

## 两条路径

### 复读 / 接话（`repeater`）

- 平时群里正常聊天时自动生效
- 先参考本机学到的语料
- 会受牛格、群风格和群内上下文影响
- 不需要每次都走 LLM

详见 [`repeater`](../plugins/repeater/README.md)。

### `@牛牛` 随时闲聊（`llm_chat`）

- 只有群里明确 `@牛牛` 才会触发
- 走统一 LLM 能力层
- 会带会话记忆、群内旧事、关系备注、工具等
- 也会受牛格和群味影响，但不是单纯复读

详见 [`llm_chat`](../plugins/llm_chat/README.md)。

## 为什么两者会互相影响

复读和 AI 没有完全割裂。你看到的效果通常叠了这些层：

- **语料底盘**：本机学到的群聊
- **牛格**：这只牛的基础行为差异
- **群味**：这个群的说话节奏和偏好
- **群内旧事 / 关系备注**：旧梗、对某人的稳定印象
- **LLM**：补位、轻润色、多轮闲聊、工具调用

## `LLM_REPEATER_MODE` 怎么选

这个开关管：**LLM 会不会介入接话**（不是管 `@` 闲聊总闸）。

| 值 | 你感觉到的 |
| --- | --- |
| `off` | 更纯粹的语料牛，LLM 不插手接话 |
| `fallback` | 语料接不上时，AI 帮忙补一句 |
| `polish` | 语料是底盘，出口更顺、更像牛 |
| `both` | 语料优先；AI 既能补位也能轻润色 |

总闸仍是 **`LLM_CHAT_ENABLED`**。开关总览：[把玩法 / AI 也装上](4.0-start.md)。

## 接话时 LLM 怎么走

`repeater` 的增强大致按这个顺序试：

1. 在已有语料里选一句（grounded select）
2. 需要时轻改写 / polish
3. 前面都走不通，才 fallback 生成补位

## 对话内核档位（进阶）

`CONVERSATION_FEATURE_LEVEL` 控制 repeater 与 llm_chat 共用内核的收敛程度。留空时会按现有开关自动推断。

| 档位 | 含义 |
| --- | --- |
| `legacy_repeater` | 仅语料 + 规则 + 现有 persona/scorer |
| `repeater_plus_decision` | 启用统一 decision 与 trace |
| `full_conversation_kernel` | decision + generation + persona-affect + memory-learning 全启 |

兼容原则：

- 未开 `LLM_CHAT_ENABLED` 时，默认落在 `legacy_repeater`
- `LLM_REPEATER_FEEDBACK_ENABLED` / `BIAS` / `WRITEBACK` 默认关闭
- writeback 默认关：direct chat 原句不会无门槛写穿 repeater 主语料

## 为什么优化后「不总是回」

这通常不是坏事。更像群友时，本来就会：

- 对方像没说完时先等一下
- 别人互聊时不抢话
- 说过一轮后不立刻补第二句
- 有时只接一句，不把话说满

你会同时看到：回得更少、更短、重复模板变少、没那么像客服。

## 相关文档

- [`@牛牛` 怎么用](../plugins/llm_chat/README.md)
- [平时接话 / 复读](../plugins/repeater/README.md)
- [牛格和群味](../plugins/persona/README.md)
- [开关总览](4.0-start.md)

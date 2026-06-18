# llm_chat（随时闲聊）

群内 @牛牛 多轮智能对话；**4.0 core 内置**，需部署 [Pallas-Bot-AI](https://github.com/PallasBot/Pallas-Bot-AI) 并在控制台开启智能对话（`LLM_CHAT_ENABLED`）。

原 pip 包 `pallas-plugin-llm-chat` / 遗留名 `ollama` 已废弃，请使用内置 `llm_chat`。

模型与人设由部署者在服务端配置；**不提供**群内更换模型或卸载模型的口令。超管可在**私聊**使用「换模型」「卸模型」（不出现在群帮助图），或在控制台「智能对话与 AI 服务」面板切换。

## 用户命令

| 口令 | 场景 | 说明 |
| --- | --- | --- |
| @牛牛 + 消息 | 群内 | 多轮对话 |
| @牛牛 clear | 群内 | 清空本会话记忆 |

## 命令权限

| 命令 ID | 默认等级 |
| --- | --- |
| `llm_chat.chat` | everyone |
| `llm_chat.clear` | everyone |

## LLM 工具（`llm_tools`）

插件在 `PluginMetadata.extra["llm_tools"]` 声明可被 AI 调用的口令工具（与 [draw](../draw/README.md) 等同机制）：

| tool 名 | 命令 ID | 说明 |
| --- | --- | --- |
| `llm_chat.clear` | `llm_chat.clear` | 用户口头要求「忘掉刚才聊的」时，LLM 可派发 `clear` 清空 PG/Redis 会话 |

总闸 **`LLM_TOOLS_ENABLED`**（WebUI「智能对话与 AI 服务」）关闭时不注入 schema。闲聊任务 `task=llm_chat` 会附带 `tool_schemas`；酒后 `drunk`、复读 **fallback/select/polish** 任务不注入 tools（见下节）。

## 与 repeater 的关系

| 能力 | 模块 | 说明 |
| --- | --- | --- |
| 随时 @ 闲聊 | `llm_chat` + `features/llm` | 本插件；语料池 ≥2 条时可走 `repeater_select` |
| 语料 miss → AI 接话 | `features/llm/fallback.py` | `LLM_REPEATER_MODE` 含 `fallback` / `select_fallback` |
| 命中语料 → 情绪选句 | `features/llm/select.py` | **推荐** `select` / `select_polish_lite` |
| 命中语料 → 偶尔轻润色 | `features/llm/polish_lite.py` | `select_polish_lite` 模式，默认约 12% 采样 |
| 命中语料 → 轻润色（遗留） | `features/llm/polish.py` | `polish` 模式，完整人设 |
| 语料学习与选句 | `repeater` | scorer 预筛；select 失败回退 Top-1 |

**省 Token 与能力演进**（门控、记忆 RAG、tool 治理）见 [architecture/llm-efficiency-roadmap.md](../../architecture/llm-efficiency-roadmap.md)。

开发向细节：[persona-llm-roadmap](../../architecture/persona-llm-roadmap.md)、[arknights-knowledge-mcp](../../architecture/arknights-knowledge-mcp.md)（方舟 tool 由 `features/llm/tools/` 注册）。

## 配置

1. **通用配置 → 智能对话与 AI 服务**：开启总开关，填写服务地址；可选 `LLM_TOOLS_ENABLED`。
2. **插件 → 随时闲聊**：可选自定义人设提示词文件（维护者向，勿暴露给群用户修改入口）。

酒后 `chat` 插件与随时闲聊共用同一总开关。

## 排障

| 现象 | 处理 |
| --- | --- |
| 无回复 | 确认总开关已开、AI 服务在跑；发 `牛牛连通` 测延迟 |
| 与酒后聊天混淆 | 随时 @ 即可；酒后须先「牛牛喝酒」 |
| LLM 未调用画画等工具 | 确认 `LLM_TOOLS_ENABLED` 与对应扩展已加载（如 `draw`） |

## 实现

[`src/plugins/llm_chat/`](../../../src/plugins/llm_chat/)

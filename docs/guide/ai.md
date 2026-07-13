# AI 扩展

不玩 AI 可以整节跳过——复读、喝酒、轮盘不受影响。

**Pallas-Bot** 管 QQ 消息；**Pallas-Bot-AI** 管唱歌、画画、部分对话。  
两个都要跑，并在控制台填 AI 地址。

## 能做什么

| 能力 | 群里怎么说（示例） |
| --- | --- |
| 翻唱 / 点歌 | `牛牛唱歌 …`、`牛牛点歌 …` |
| 酒后对话 | 喝酒状态下的智能聊天 |
| 文生图 | `牛牛画画 …`（需 draw 扩展） |
| 随时闲聊 | @ 牛；见 [闲聊与复读](llm-and-repeater.md) |

精确口令以 **牛牛帮助** 为准。

## 硬件怎么选

| 方案 | 说明 |
| --- | --- |
| 有 NVIDIA 显卡 | 建议 **≥6GB** 显存 |
| 纯 CPU | 能跑但慢，内存可能 **10GB+** |
| 无 GPU、用云端 API | 可不跑本地大模型；仍要轻量 AI 服务，见 [remote-only](https://github.com/PallasBot/Pallas-Bot-AI/blob/main/docs/deploy/remote-only.md) |

::: tip 新手推荐
先按 AI 仓文档起服务，再在控制台填地址。本地大模型可以后装。
:::

## 三步接上

1. **部署 Pallas-Bot-AI**  
   按 [仓库文档](https://github.com/PallasBot/Pallas-Bot-AI) 启动，记下地址（如 `http://127.0.0.1:5000`）。

2. **在控制台填地址**  
   `/pallas/` → **通用配置** 或对应插件页 → 填 AI URL / 密钥。

3. **验收**  
   群里发 `牛牛连通`，或试一条唱歌 / 画画口令。通了就行。

## 和扩展的关系

| 能力 | 包 |
| --- | --- |
| 唱歌、酒后聊天 | 多在 `pallas-plugin-ai-media` |
| 画画 | `pallas-plugin-draw` |
| 随时闲聊 | core 插件 `llm_chat`（仍要 AI 在线） |

扩展安装：[安装官方扩展](install-extensions.md)。运维细项：[LLM 与 AI](../maintainer/operate/llm-and-ai.md)。

▶ [安装插件](install-plugins.md) · [使用指南](../user/README.md)

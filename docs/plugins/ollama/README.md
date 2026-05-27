# ollama（随时闲聊）

群内 **@牛牛** 多轮对话，后端为 [Pallas-Bot-AI](https://github.com/PallasBot/Pallas-Bot-AI) 的 Ollama 接口；与「酒后聊天」（RWKV）独立。帮助菜单里查 **`牛牛帮助 随时闲聊`**（旧称「牛牛聊天」仍可匹配）。

## 用户命令

| 口令 / 触发 | 场景 | 说明 |
| --- | --- | --- |
| @牛牛 + 消息 | 群内 | 多轮对话 |
| @牛牛 clear | 群内 | 清空本会话记忆（保留人设） |
| @牛牛 unload | 群内 | 卸载 Ollama 模型（释放显存） |
| @牛牛 model [模型名] | 群内或私聊 | 查询当前模型 / 热更换（超管） |

## 命令权限

| 命令 ID | 默认等级 | 说明 |
| --- | --- | --- |
| `ollama.chat` | everyone | 群内 @牛牛 多轮对话 |
| `ollama.clear` | everyone | `@牛牛 clear` 清空本会话记忆 |
| `ollama.unload` | staff | `@牛牛 unload` 卸载模型（群管/号主） |
| `ollama.set_model` | superuser | `@牛牛 model [模型名]` 查询或热更换模型 |

可在 WebUI「通用配置 → 命令权限」覆盖；帮助图「何人可用」列随生效等级自动展示。

`chat` / `sing` / `ollama` 在对应 `*_enable=false` 时不会出现在帮助总览中。

## 配置

[`config.py`](../../../src/plugins/ollama/config.py) 字段以 WebUI **插件 → ollama** 为准（落盘 `data/pallas_config/webui.json`，保存后热重载）。也可在 **`config/pallas.toml` 的 `[env]`** 写同名键（如 `OLLAMA_ENABLE`），合并顺序见 [settings-storage](../../architecture/settings-storage.md)。

| 键 | 配置键名 | 说明 |
| --- | --- | --- |
| `ollama_enable` | `OLLAMA_ENABLE` | 是否启用，默认 `false` |
| `ai_server_host` | `AI_SERVER_HOST` | Pallas-Bot-AI 地址（与 sing/chat 共用） |
| `ai_server_port` | `AI_SERVER_PORT` | AI 服务端口 |
| `ollama_system_prompt_path` | `OLLAMA_SYSTEM_PROMPT_PATH` | 可选自定义 prompt 文件（相对仓库根）；留空用内置 `system_prompt.txt` |

Ollama 模型、URL、自动拉起等仅在 **Pallas-Bot-AI** 侧配置（`.env` 或 Docker compose），Bot 不再直连 Ollama。

修改 `system_prompt.txt` 或自定义 prompt 文件后**下一条消息即生效**，无需重启 Bot。

## 排障

| 现象 | 处理 |
| --- | --- |
| 无回复 | 确认 WebUI / `pallas.toml` 中 `OLLAMA_ENABLE=true`、AI 服务与 Ollama 可达 |
| 人设不对 | 检查 `system_prompt.txt` 或 `ollama_system_prompt_path` |
| 与酒后聊天混淆 | 本插件随时 @ 可用；`chat` 须先喝酒 |

## AI 服务：模型热更换

```bash
curl -X PUT http://127.0.0.1:9099/api/ollama/model \
  -H 'Content-Type: application/json' \
  -d '{"model":"qwen2.5:7b","pull":true}'
```

详见 [Pallas-Bot-AI 部署文档 · Ollama 配置参考](https://github.com/PallasBot/Pallas-Bot-AI/blob/main/docs/Deployment.md#ollama-配置参考)。

## 实现

[`src/plugins/ollama/`](../../../src/plugins/ollama/)

# 理解 Pallas-Bot 怎么拼起来

只想先跑起来？直接看 [五分钟跑起来](quickstart.md)。  
本节方便排错时知道该查哪一块。

## 一条消息怎么走

```text
QQ 用户
  → NapCat 等协议端（OneBot v11）
  → WebSocket
  → Pallas-Bot（插件）
  → PostgreSQL（现行默认）
```

浏览器里的 **Web 控制台**、**协议端管理页**，和上面是**同一个 Bot 进程**提供的。

## 四块各干什么

| 块 | 干什么 | 你要不要先管 |
| --- | --- | --- |
| 协议端 | 替 QQ 登录、收发 | 要，至少扫码一次 |
| Pallas-Bot | 复读、帮助、扩展玩法 | `uv run nb run` |
| 数据库 | 语料、群配置、用户数据 | 先起 PostgreSQL |
| Web 控制台 | 改配置、看日志、装扩展 | `/pallas/` + 启动口令 |

## 配置写哪

日常改插件：网页里保存即可。

| 优先级 | 路径 | 写什么 |
| --- | --- | --- |
| 低 | `config/pallas.toml` | 端口、超管、数据库 |
| 中 | `.env`（可选） | 老式 nb/pip 项 |
| **高** | `data/pallas_config/webui.json` | 控制台保存的配置 |

详见 [配置存储](../architecture/settings-storage.md)。

## 插件从哪来

```text
本体 core（默认有）     → repeater、help、drink …
官方扩展（要装）       → duel、maa、who_is_spy …
站点 local             → local/plugins/<名>/
```

- 装官方扩展：[安装插件](install-plugins.md)  
- AI 另仓：[AI 扩展](ai.md)

## 和 AI 的关系

```text
Pallas-Bot  ←HTTP→  Pallas-Bot-AI（可选）
```

唱歌、画画、随时闲聊要另起 AI。不玩 AI 可以不装，复读 / 喝酒 / 轮盘不受影响。

## 多只牛（进阶）

很多 QQ 号时可开 **hub + worker 分片**。见 [多进程分片](../architecture/bot_process_sharding.md)。

▶ [五分钟跑起来](quickstart.md) · [使用指南](../user/README.md) · [进阶介绍](advanced.md)

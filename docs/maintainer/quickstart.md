# 运维入口

第一次装、只想本机跑通？去 **[五分钟跑起来](../guide/quickstart.md)**。  
这里只指路：部署形态、升级、排障、配置——**不重复**装本体步骤。

## 你要做什么

| 目标 | 打开 |
| --- | --- |
| 本机第一次跑通 | [五分钟跑起来](../guide/quickstart.md) |
| 装决斗 / MAA / 协议端 / AI | [把玩法 / AI 也装上](../guide/4.0-start.md) |
| Docker | [Docker 部署](deploy/docker.md) |
| 单进程长跑 | [单进程部署](deploy/single-process.md) |
| 多账号 / 分片 | [分片部署](deploy/sharded.md) |
| 从旧版升级 | [升级](deploy/upgrade.md) · [从 3.x 迁到现行版本](../guide/4.0-migration.md) |
| 新装验收走查 | [安装验收 Checklist](install/ga-install-checklist.md) |
| 排障 | [排障](operate/troubleshooting.md) |
| 闲聊 / 记忆不生效 | [LLM 与 AI](operate/llm-and-ai.md) |
| 查配置键 | [配置参考](reference/config.md) |

## 安装与组件（按需细读）

| 组件 | 文档 |
| --- | --- |
| 本体 | [本体安装](install/bot.md) |
| WebUI | [WebUI](install/webui.md) |
| 协议端 | [协议端](install/protocol.md) |
| 官方扩展 | [官方扩展](install/official-extensions.md) |
| AI Runtime | [AI Runtime](install/ai-runtime.md) |
| 命令权限 | [命令权限](operate/command-permissions.md) |
| Web 控制台日常 | [Web 控制台](operate/webui.md) |

::: tip 什么时候才需要分片
多 Bot 账号同时在线、单进程已有明显压力、或需要更稳的 worker / 协调时，再看 [分片部署](deploy/sharded.md)。平时单进程即可。
:::

上手分流：[选一条路](../guide/welcome.md)

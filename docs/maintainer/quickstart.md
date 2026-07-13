# 运维快速开始

最短路径跑通 Pallas-Bot：能登录、能连 QQ、能装扩展；出事也知道去哪查。

::: tip 先跑起来再折腾
第一次装：单进程即可。消息怎么进牛、要不要装扩展，可先瞄 [把玩法 / AI 也装上](../guide/4.0-start.md) 里的两张图。卡住了去 [排障](operate/troubleshooting.md)。
:::

## 跑通后你会有什么

- 一套能启动的 `Pallas-Bot`
- 一个能登录的 WebUI
- 一条可用的协议端连接
- 至少一个能正常加载的官方扩展
- 需要 AI 时，再接上 `Pallas-Bot-AI`

## 推荐路径

1. 安装并启动本体
2. 确认 WebUI 可访问
3. 接入协议端并让 QQ 连上
4. 安装至少一个官方扩展
5. 按需接入 AI runtime
6. 账号多、负载大时再考虑分片

安装验收走查：[4.0 安装验收 Checklist](install/ga-install-checklist.md)。

## 第一步：先跑起本体

备好：

- Python `3.12`
- `uv`
- 一份本地 `config/pallas.toml`

然后读：

- [本体安装](install/bot.md)
- [配置参考](reference/config.md)

## 第二步：确认 WebUI 能用

本体起来后先打开：

```text
http://<host>:8088/pallas/
```

页面打不开？别急着排协议端，先确认：

- Bot 是否已启动
- `pb_webui` 是否正常挂载
- `data/pb_webui/public/` 是否存在可用资源

对应文档：[WebUI](install/webui.md)

## 第三步：让协议端接进来

Bot 在跑 ≠ QQ 消息已经进来。接着确认：

- 协议端实例是否已创建
- 反向 WebSocket 是否指向正确目标
- 单进程或分片下，连的是不是正确角色

对应文档：[协议端](install/protocol.md)

## 第四步：安装官方扩展

大量玩法不再默认内置。Bot 能启动只说明 core 在跑；决斗、MAA、谁是卧底还得自己装。

- [安装官方扩展](install/official-extensions.md)

装完至少验一次：

- WebUI 商店显示已加载
- 群内帮助菜单能看到新增命令

## 第五步：按需接入 AI Runtime

需要 @ 对话、接话 LLM、唱歌、媒体任务时再接：

- **本机**：`uv run pallas ai setup`（或 AI 仓 `./scripts/ai_bootstrap.sh`）
- **Docker 全栈**：主仓 `docker-compose.full.yml`（见 [Docker 部署](../DockerDeployment.md)）
- **排障边界**：[AI Runtime](install/ai-runtime.md)

::: tip AI runtime 不是必需品
别把 AI 当成「Bot 能不能跑起来」的前置。本体 + 官方扩展就能成立。
:::

## 第六步：什么时候进分片

这些场景才值得提前考虑分片：

- 多 Bot 账号同时在线
- 单进程已有明显性能或连接压力
- 需要更稳的 worker / callback / 协调

对应文档：[分片部署](deploy/sharded.md)

## 一条最短命令路径

熟悉仓库的话，典型顺序：

1. 准备 `config/pallas.toml`
2. 启动 Bot
3. 登录 `/pallas/`
4. 接协议端
5. 安装官方扩展

「能启动但不回复」或「页面能开但状态不对」时：

- [排障](operate/troubleshooting.md)（页首有决策树）
- [LLM 与 AI](operate/llm-and-ai.md)
- 上手分流：[选一条路](../guide/welcome.md)

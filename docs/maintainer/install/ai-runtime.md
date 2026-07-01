# AI Runtime

这页帮你接入 AI Runtime，并在它没反应时分清问题出在哪一侧。

AI Runtime 由独立仓负责，Bot 通过回调和运行时协议跟它协作。把它当成“独立服务”，不是主仓里的普通插件。

## 它负责什么

典型能力：

- 绘图
- 唱歌与音频类任务
- 媒体或工具型 AI 任务执行
- 任务状态回调与结果回传

## 先记住这个边界

- `Pallas-Bot` 负责接消息、发起任务、接收 callback、把结果送回群或会话。
- `Pallas-Bot-AI` 负责真正执行 AI 任务。
- 任何一侧异常，都会表现成“AI 功能没反应”，但根因不一定在同一仓。

所以排障时要分清：

- Bot 端没发出任务
- AI Runtime 没收到任务
- AI Runtime 跑了但没回调
- callback 回到 hub 了但没被正确转发

## 什么时候需要接入

这些需求才需要 AI Runtime：

- 绘图或媒体生成
- 歌曲、音频、工具调用类异步任务
- 独立的 AI 执行流水线
- **@ 对话、接话 LLM、醉聊**（4.0 智能对话）

::: tip
只是普通命令、权限、帮助、插件治理，本体就够了，不必先接 AI Runtime。
:::

## 安装（维护者）

### 本机开发（推荐）

在 **Pallas-Bot-AI** 仓库：

```bash
cp .env.example .env
./scripts/ai_bootstrap.sh --bot-host 127.0.0.1 --bot-port 8088
```

或在 **Pallas-Bot** 仓库（同级已克隆 AI 仓时）：

```bash
uv run pallas ai setup
```

Bot 已跑在其它端口时用 `--bot-port`；仅体检用 `--check-only`。

### Docker（仅 AI 栈）

```bash
docker compose -f docker-compose.llm.yml up -d
```

### 与 Bot 同编排（新装）

使用主仓 **`docker-compose.full.yml`**（PostgreSQL + Bot + Redis + Ollama + AI），见 [Docker 部署](../../DockerDeployment.md)。

### Bot 侧最小配置

`config/pallas.toml` 的 `[env]` 或 WebUI「智能对话与 AI 服务」：

- `LLM_CHAT_ENABLED=true`
- `AI_SERVER_HOST` / `AI_SERVER_PORT`（默认 `127.0.0.1:9099`；全栈 compose 内由环境注入）

详细变量见 [Pallas-Bot-AI README](https://github.com/PallasBot/Pallas-Bot-AI/blob/main/README.md) 与 [LLM 与 AI 运维](../operate/llm-and-ai.md)。

## 接入前要确认的四件事

### 1. 运行地址与服务可达

你至少要知道：

- AI Runtime 的基址
- Bot 发任务时用的目标地址
- AI Runtime 回调 Bot 时用的 callback 地址

::: warning callback 地址最容易出错
分片下它应该回到 hub，而不是任意 worker。
:::

### 2. token 与鉴权一致

两边鉴权不一致时，常见现象是：

- 任务提交看似成功，实际被拒绝
- callback 发回来了，但 Bot 拒收

### 3. 网络路径正确

Docker、多机或反代场景下，问题往往不在代码，而是：

- AI Runtime 访问不到 hub 的 callback 地址
- 把内网地址写给了外部服务
- 端口开放和反代转发不完整

### 4. Bot 侧已经启用相关能力

即使 AI Runtime 本身在线，也要确认：

- 对应插件或能力已安装
- 服务网关配置正确
- WebUI 里显示的运行态和真实配置一致

## 维护者的最短联调顺序

1. 先跑通 Bot 本体。
2. 再启动 AI Runtime。
3. 在 Bot 侧填写 AI 相关地址、token、网关配置。
4. 确认 AI Runtime 能访问 Bot 的 callback 地址。
5. 触发一个最小任务，验证整条链路。
6. 再看 WebUI 里的 AI 状态与任务结果。

## 分片下的关键点

- callback 应回到 hub。
- worker 上登记的任务，需要 hub 再转发到对应 worker。
- 所以“AI Runtime 能访问 worker，但访问不到 hub”并不能替代正确配置。

::: tip
分片下的 AI 问题，先当成“回调路径问题”来查，别先猜插件逻辑。
:::

## 最常见的三类现象

### 任务发出但没有结果

优先判断：

- AI Runtime 是否真的收到任务
- 任务是否执行失败
- callback 是否成功打回 Bot

### 页面显示 AI 离线

优先判断：

- 运行态探测接口是否正常
- 服务地址是否填错
- 只是 WebUI 状态旧了，还是后端确实探测失败

### 群里没有任何回执

优先判断：

- Bot 是否真的发起了任务
- callback 是否回到 hub
- hub 是否把结果转发给了登记任务的 worker

## 相关阅读

- [LLM 与 AI 运维](../operate/llm-and-ai.md)
- [AI 实施与联调](../../architecture/internal/pallas-ai-implementation.md)
- [AI 终态架构](../../architecture/internal/pallas-final-ai-shape.md)

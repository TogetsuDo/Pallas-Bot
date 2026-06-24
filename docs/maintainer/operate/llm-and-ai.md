# LLM 与 AI 运维

这页只关注运行中的 AI 链路是否正常，不讲插件开发和架构设计。

## 最常看的四件事

- LLM 总开关是否打开
- AI runtime 是否可达
- callback 是否正常回到 Bot
- 任务与会话状态是否可观察

## 先分清 Bot 和 AI Runtime

- `Pallas-Bot` 负责产品侧触发、权限、消息发送与 callback 接收
- `Pallas-Bot-AI` 负责具体 AI / 媒体任务执行

所以「AI 相关功能不可用」时，问题可能在任一侧。

## 先看哪些配置

优先确认：

- `LLM_CHAT_ENABLED`
- `AI_SERVER_HOST`
- `AI_SERVER_PORT`

::: warning 总开关没开，后端在线也白搭
如果 `LLM_CHAT_ENABLED` 没开，很多 AI 功能即使后端在线也不会触发。
:::

## 先看哪些现象

### @ 牛闲聊无响应

优先检查：

- LLM 总开关
- AI runtime 连通性
- 相关日志里是否有请求发出

### 媒体任务发出但没有结果

优先检查：

- AI runtime 任务是否已接收
- callback 是否打回 Bot
- Bot 是否成功处理 callback

### 页面显示 AI 离线

优先检查：

- AI runtime 进程是否运行
- Bot 到 AI 的地址配置是否正确
- 网络和端口是否可达

## 控制台里先看哪几个接口

如果你在排前端或反代问题，也可以直接访问控制台 API：

- `/pallas/api/auth/setup-status`
  - 看是否还停留在默认口令 / 首次引导阶段
- `/pallas/api/common-config/llm/wizard/status`
  - 看 AI 服务、provider、LLM 总闸哪个环节还没就绪
- `/pallas/api/common-config/llm/runtime-overview`
  - 一屏看 health、模型、任务统计、conversation kernel

这三者的关系：

- `setup-status` 解决“控制台是否该先引导改密”
- `wizard/status` 解决“AI 配置还差哪一步”
- `runtime-overview` 解决“现在到底是哪一层在异常”

## callback 的判断思路

你不用搞懂所有内部实现，但要记住一件事：

- AI runtime 任务成功，不等于群里一定能收到结果

中间还经过：

- callback 回到 Bot
- Bot 路由到正确上下文
- 最终消息发送

所以看到「AI 端执行成功但群里没消息」，别只盯着 AI 仓。

## 相关阅读

- [AI Runtime 安装](../install/ai-runtime.md)
- [排障](troubleshooting.md)
- [AI 终态架构](../../architecture/internal/pallas-final-ai-shape.md)

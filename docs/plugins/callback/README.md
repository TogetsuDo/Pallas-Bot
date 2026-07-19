# callback（任务回调）

接收 AI/唱歌等异步任务的 HTTP 回调，更新任务状态并向 QQ 推送结果。

## 用户命令

无。端点：`POST /callback/{task_id}`（维护者配置 AI 服务回调地址）。

## 命令权限

无。

## 配置

依赖各业务插件创建的 `TaskManager` 任务记录。

## 排障

| 现象 | 处理 |
| --- | --- |
| 404 | `task_id` 不存在或已过期 |
| 无群消息 | 查任务关联群号与 Bot 在线状态；若协议端发送失败，回调可能返回 `{"message": "failed"}` |

## 实现

[`src/plugins/callback/`](../../../src/plugins/callback/)

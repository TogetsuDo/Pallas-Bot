# request_handler（申请管理）

好友申请与入群邀请：私聊提醒号主，支持同意/拒绝与自动同意开关。

## 用户命令

| 口令 | 场景 | 说明 |
| --- | --- | --- |
| 查看好友申请 / 查看入群邀请 | 私聊 | 列出待处理 |
| 同意 / 好（可引用提醒） | 私聊 | 处理最新或引用条 |
| 同意好友 \<QQ\> / 拒绝好友 \<QQ\> | 私聊 | 指定 QQ |
| 同意入群 \<群号\> 等 | 私聊 | 入群邀请 |
| 开启/关闭自动同意好友/入群 | 私聊 | 写入 BotConfig |

## 命令权限

审批命令：**号主**（`admins`）或 **超管**（见代码 `satisfies_command_permission`）。

## 配置

[`config.py`](../../../src/plugins/request_handler/config.py)：`request_handler_poll_doubt_friends` 等。

## 排障

| 现象 | 处理 |
| --- | --- |
| 无提醒 | 插件是否被 `牛牛关闭`；号主能否收私聊 |
| 同意无效 | 提醒过期（约 7 天）；用带 QQ/群号命令 |

## 实现

[`src/plugins/request_handler/`](../../../src/plugins/request_handler/)

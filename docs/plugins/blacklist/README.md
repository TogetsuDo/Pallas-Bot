# blacklist（牛牛黑名单）

私聊维护**全局**拉黑；群聊维护**本群**拉黑列表。

## 用户命令

| 口令 | 场景 | 说明 |
| --- | --- | --- |
| 牛牛拉黑 / 牛牛屏蔽 + QQ 或 @ | 私聊 | 写入全局 `UserConfig.banned` |
| 同上 | 群内 | 追加本群 `blocked_user_ids` |
| 牛牛解禁 / 牛牛取消拉黑 + 目标 | 私聊/群内 | 对应解除 |

## 命令权限

| 命令 ID | 默认等级 |
| --- | --- |
| `blacklist.add` | staff（私聊号主 / 群内群管或号主；超管始终可用） |
| `blacklist.remove` | staff |

## 配置

无独立插件配置；数据见 `UserConfig` / `GroupConfig`。

## 排障

| 现象 | 处理 |
| --- | --- |
| 仍收到消息 | 确认私聊/群内场景与名单类型 |
| 好友请求 | 仅全局拉黑会拒绝好友申请 |

## 实现

[`src/plugins/blacklist/`](../../../src/plugins/blacklist/)

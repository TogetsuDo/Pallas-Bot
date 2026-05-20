# block（其它牛牛拦截）

拦截**其它牛牛账号**在本群的群消息与部分通知，避免多 Bot 互相触发逻辑。

## 用户命令

无（维护者向能力，`help_audience: maintainer`）。

## 命令权限

无。

## 配置

[`config.py`](../../../src/plugins/block/config.py)：`bots` 集合由连接事件维护。

## 排障

| 现象 | 处理 |
| --- | --- |
| 本牛消息被挡 | 确认 `self_id` 未误入其它牛集合 |

## 实现

[`src/plugins/block/`](../../../src/plugins/block/)

# 社区统计上报（community_stats）

向 [Pallas-Bot-Community-Stats](https://github.com/TogetsuDo/Pallas-Bot-Community-Stats) 中心 **opt-in** 上报部署心跳，用于统计社区内自托管部署数与在线数。默认**开启**；不需要可在 `config/pallas.toml` 关闭。

## 配置（`[community_stats]`）

| 键 | 默认 | 说明 |
| --- | --- | --- |
| `enabled` | `true` | `false` 时不上报 |
| `endpoint` | `https://stats.pallasbot.top/v1/heartbeat` | POST 地址 |
| `token` | 空 | 与中心 `HEARTBEAT_TOKEN` 一致；生产必填 |
| `interval_sec` | `300` | 周期上报间隔（60–3600） |

等价环境变量：`PALLAS_COMMUNITY_STATS_*`。

## 行为

- 首次启用时在 `data/pallas_config/community_stats.json` 生成 `deployment_id`（UUID）。
- **单进程 / hub** 上报；**分片 worker** 不上报（避免重复计数）。
- 失败仅记日志，不影响 Bot 启动与消息处理。

## 隐私

不上报 QQ 号、群号或消息内容，仅聚合字段（在线牛数量、是否分片等）。

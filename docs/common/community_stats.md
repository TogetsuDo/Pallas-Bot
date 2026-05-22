# 社区统计上报（community_stats）

向官方共用中心 **`https://stats.pallasbot.top`** 上报部署心跳（[Pallas-Bot-Community-Stats](https://github.com/TogetsuDo/Pallas-Bot-Community-Stats)），用于统计社区内自托管部署数与在线数。

**升级**：包含 `community_stats` 插件的 release 在 **hub / 单进程** 启动后**默认自动接入**，**不必**在 `pallas.toml` 增加 `[community_stats]` 或 `enabled = true`。仅 opt-out：显式 `enabled = false` 或 `PALLAS_COMMUNITY_STATS_ENABLED=false`。**无需向用户分发 token。**

## 配置（`[community_stats]`，均可省略）

| 键 | 默认 | 说明 |
| --- | --- | --- |
| `enabled` | `true` | 省略整段 `[community_stats]` 亦为开启；仅 `false` 时不上报 |
| `endpoint` | `https://stats.pallasbot.top/v1/heartbeat` | POST 地址 |
| `token` | 空 | **共用中心 `stats.pallasbot.top` 留空即可**；仅自建私有中心且启用 token 时才填 |
| `interval_sec` | `300` | 周期上报间隔（60–3600） |

等价环境变量：`PALLAS_COMMUNITY_STATS_*`。

## 行为

- 首次启用时在 `data/pallas_config/community_stats.json` 生成 `deployment_id`（UUID）。
- **单进程 / hub** 上报；**分片 worker** 不上报（避免重复计数）。
- `online_bots` 与控制台 **「在线 Bot」** 同源（分片为 presence 合并，单进程为 `get_bots()`）；首包在启动约 **60 秒** 后发送，之后按 `interval_sec`（默认 300 秒）刷新。
- WebUI **「在线牛总和」** 为**全社区**各部署 `online_bots` 之和，不是本机实时数；本机以首页 **「在线 Bot」** 为准。
- 失败仅记日志，不影响 Bot 启动与消息处理。

## 隐私

不上报 QQ 号、群号或消息内容，仅聚合字段（在线牛数量、是否分片等）。

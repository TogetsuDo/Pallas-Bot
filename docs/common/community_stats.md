# 社区统计上报（community_stats）

向官方共用中心上报部署心跳（[Pallas-Bot-Community-Stats](https://github.com/TogetsuDo/Pallas-Bot-Community-Stats)），用于统计社区内自托管部署数与在线数。

**升级**：包含 `community_stats` 插件的 release 在 **hub / 单进程** 启动后**默认自动上报心跳**，**不必**在 `pallas.toml` 增加 `[community_stats]`。插件为内部能力，**不出现在用户帮助总览**（`help_audience: maintainer` + 内置隐藏）。仅 opt-out：`enabled = false` 或 `PALLAS_COMMUNITY_STATS_ENABLED=false`。**无需向用户分发 token。**

社区**语料多读源**与心跳独立：**默认不上报语料、不 enroll**；需在 WebUI **语料联邦** 手动开启 `community_enabled`（见 [语料联邦](corpus/README.md)）。

## 心跳地址

默认上报至：

`https://stats.pallasbot.top/v1/heartbeat`

无需在配置中填写；仅在自建私有统计中心时通过 `endpoint` 覆盖。

## 配置（`[community_stats]`，均可省略）

| 键 | 默认 | 说明 |
| --- | --- | --- |
| `enabled` | `true` | 省略整段 `[community_stats]` 亦为开启；仅 `false` 时不上报 |
| `endpoint` | `https://stats.pallasbot.top/v1/heartbeat` | 仅自建/特殊地址时修改 |
| `token` | 空 | **共用中心留空即可**；仅自建私有中心且启用 token 时填写 |
| `interval_sec` | `300` | 周期上报间隔（60–3600） |

等价环境变量：`PALLAS_COMMUNITY_STATS_*`。

## 行为

- 首次上报时在 `data/pallas_config/community_stats.json` 生成 `deployment_id`（UUID）。
- **社区语料**默认关：仅当 WebUI / `[corpus] community_enabled=true` 后，hub 启动时才会 `POST /v1/corpus/enroll` 并写入 `corpus_community` 段；手动 `[corpus.community] token` 时跳过 auto enroll。
- 开启 community 后 **community_contribute** 默认 auto（开）：学习结果可 mirror 到社区池（详见 [语料联邦](corpus/README.md)）。
- 心跳与语料读共用 **主/备域名 failover**（`stats.pallasbot.top` ↔ `pallas.togetsudo.com`）。
- **单进程 / hub** 上报；**分片 worker** 不上报（避免重复计数）。
- `online_bots` 与控制台 **「在线 Bot」** 同源；首包在启动约 **60 秒** 后发送，之后按 `interval_sec`（默认 300 秒）刷新。
- WebUI 首页 **社区与语料**、**语料联邦** 配置页（`/pallas/corpus-config`）；**在线牛总和** 为全社区 `online_bots` 之和。
- 控制台 `GET /pallas/api/community-stats` 优先拉取中心 **`GET /v1/monitor/overview`**（不可用时回退 `/v1/stats`），展示语料接入数、24h 活跃部署、在线版本分布等。
- 上报失败仅记日志，不影响 Bot 启动与消息处理。

## 中心监控 API（只读）

| 路径 | 说明 |
| --- | --- |
| `GET /v1/stats` | 基础聚合；`corpus.enrollments_total` 为累计接入语料库的 deployment 数 |
| `GET /v1/stats/corpus` | 语料池专用指标（含 `enrollments_online`、`answer_hits_sum` 等） |
| `GET /v1/monitor/overview` | 控制台一页式快照（部署 + 语料 + 版本 Top5） |

详见 Community-Stats 仓库 [docs/API.md](https://github.com/TogetsuDo/Pallas-Bot-Community-Stats/blob/main/docs/API.md)。

## 隐私

不上报 QQ 号、群号或消息内容，仅聚合字段（在线牛数量、是否分片等）。

## 相关

- [语料联邦](corpus/README.md)（同中心 `/v1/corpus/*`、auto enroll）

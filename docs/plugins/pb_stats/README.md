# pb_stats（在线统计）

> **内核插件**（4.0 core）：向社区统计中心周期上报部署心跳，供控制台与 [社区主站](https://stats.pallasbot.top/) 展示。**无群内用户口令**。

## 用户命令

无（维护者向后台任务）。

## 配置

WebUI **通用配置 → 在线统计与社区主站**（段 ID 仍为 `community_stats`），或 `config/pallas.toml` 的 `[community_stats]` 段。默认开启；设置 `enabled=false` 可关闭。

详细说明见 [在线统计与社区主站](../../common/community_stats.md)。

## 实现

- 插件壳：[`src/plugins/pb_stats/`](../../../src/plugins/pb_stats/)
- 业务：[`src/features/community_stats/`](../../../src/features/community_stats/)

## 迁移说明

原扩展包名 `community_stats` / `pallas-plugin-community-stats` 已升格为内置 `pb_stats`；**请勿再安装** pip extra。

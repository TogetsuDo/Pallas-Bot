# pallas_protocol（协议端管理）

多账号 NapCat/SnowLuma 协议端：创建、启停、日志与配置同步。

## 用户命令

无。入口：`/protocol/console`（`help_audience: maintainer`）。

## 命令权限

无。

## 配置

鉴权：`X-Pallas-Protocol-Token` 或 `?token=`。Docker、`runtime_profile` 等见原文档细节于 [`config`](../../../src/plugins/pallas_protocol/config.py)。

## 排障

| 现象 | 处理 |
| --- | --- |
| 账号无法启动 | 查协议端日志与发行包版本 |
| 与控制台登不上 | 共用 `data/pallas_console/` 口令 |

## 实现

[`src/plugins/pallas_protocol/`](../../../src/plugins/pallas_protocol/)

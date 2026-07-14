# 连接 QQ / 协议端

**Pallas-Bot 不直接登录 QQ。** 路径是：

```text
QQ  ←→  NapCat（协议端）  ←→  Pallas-Bot  ←→  数据库
```

牛「在线但不说话」，多半是协议端没连上，或 WebSocket 指错了主机。

## 默认地址

端口以 `config/pallas.toml` 的 `[bootstrap] port` 为准，默认 **8088**。

| 页面 | 地址 |
| --- | --- |
| 协议端管理 | `http://<主机>:8088/pallas/protocol` |
| Web 控制台 | `http://<主机>:8088/pallas/` |
| OneBot WebSocket | `ws://<主机>:8088/onebot/v11/ws` |

本机 `<主机>` 填 `127.0.0.1`；远程填服务器 IP 或域名。

## 方式一：控制台管 NapCat（推荐）

前提：`uv run nb run` 已起来，能打开 `/pallas/`。

1. 打开协议端页，用和控制台**同一口令**登录
2. **新建实例** → 选 **NapCat** → 扫码
3. 实例列表变成 **在线**（WS 一般指向 `ws://127.0.0.1:8088/onebot/v11/ws`）

验收（三项都过才算通）：

- 协议端页：**在线**
- 控制台首页：能看到在线 Bot
- 群里发 `牛牛帮助`：**有图**

::: details Docker 里用「Docker 模式」拉 NapCat
需给 `pallasbot` 挂载 `/var/run/docker.sock`（见 compose 注释）。挂载 sock 有安全风险，仅建议可信内网。
:::

## 方式二：自己装 NapCat

1. 按 [NapCat 文档](https://napneko.github.io/) 安装并登录
2. 添加 **正向 WebSocket 客户端**
3. URL：`ws://<Bot主机>:8088/onebot/v11/ws`

::: tip Bot 和 NapCat 不在同一台？
不要写 `127.0.0.1`，写 Bot 那台机器能从 NapCat 访问到的地址。
:::

## 群里怎么验

牛已进群后发：

```text
牛牛帮助
```

也可发 `牛牛` 测打招呼（多只牛同群可能齐回）。

## 常见问题

| 现象 | 处理 |
| --- | --- |
| 打不开协议端页 | Bot 是否在跑、端口是否放行 |
| 协议端离线 | 看 NapCat 日志；重启实例 |
| 在线但群无反应 | 确认牛在群；看运行日志有没有进消息 |
| 要多只 QQ | 再建实例，或部署多只牛 |

▶ [安装官方插件](install-extensions.md) · [网页控制台](web-console.md) · [排障](../maintainer/operate/troubleshooting.md)

# 五分钟跑起来

把 **Pallas-Bot** 在本机跑通：能开控制台 → 能连 QQ → 群里 **牛牛帮助** 有回复。

::: tip 第一次就这样
先别开分片，也先别装一堆扩展。通一句再说。
:::

## 你只需要这三样

1. **Python 3.12+**（推荐用 [uv](https://docs.astral.sh/uv/)）
2. **一个空的 PostgreSQL 库**（本机或 Docker 都行）
3. **一个 QQ 小号**（协议端可以等 Bot 起来再扫）

::: tip 从 3.x 升级？
还在用 MongoDB 的可以暂时保留。**新站请用 PostgreSQL。**
:::

## 第 1 步：下载

```bash
git clone https://github.com/PallasBot/Pallas-Bot.git
cd Pallas-Bot
```

看到 `pyproject.toml`、`config/pallas.example.toml` 就对了。

## 第 2 步：装依赖

```bash
uv sync --extra pg
uv run python -c "import nonebot"
```

终端没报错 = 依赖 OK。

## 第 3 步：写配置

```bash
cp config/pallas.example.toml config/pallas.toml
```

打开 `config/pallas.toml`，至少改这些：

```toml
[bootstrap]
host = "0.0.0.0"          # 仅本机可写 127.0.0.1
port = 8088
superusers = ["你的QQ号"]
db_backend = "postgresql"

[bootstrap.postgres]
host = "127.0.0.1"        # Docker 连 compose 库时改为 postgres
port = 5432
user = "pallas"
password = "pallas"
db = "PallasBot"
```

::: warning 别提交密钥
`pallas.toml` 已在 `.gitignore`，不要推进公开仓库。
:::

## 第 4 步：启动

```bash
uv run nb run
```

日志里你该看到：

1. 没有数据库 `connection refused`
2. 一行 **Web 控制台初始口令**（也可在 `data/pallas_console/` 找回）
3. 浏览器打开 `http://127.0.0.1:8088/pallas/` —— **出现登录页就对了**

::: tip 地址怎么填
本机用 `127.0.0.1`。远程把主机换成服务器 IP，并放行 **8088**。
:::

## 第 5 步：连 QQ

Pallas-Bot **不会自己登录 QQ**，要靠 NapCat 等协议端。

1. 打开 `http://<主机>:8088/protocol/console/`
2. 用和控制台**同一口令**登录
3. **新建实例** → NapCat → 手机扫码
4. 实例变成 **在线**

把牛拉进群，发：

```text
牛牛帮助
```

**有帮助图 = 通了。** 细节见 [连接 QQ](connect-qq.md)。

## 通了之后

| 你想… | 打开 |
| --- | --- |
| 装决斗 / MAA | [安装官方扩展](install-extensions.md) |
| 改配置、看日志 | [网页控制台](web-console.md) |
| Docker / 分片 / 升级 | [运维入口](../maintainer/quickstart.md) |
| 卡住了 | [排障](../maintainer/operate/troubleshooting.md) · [FAQ](../FAQ.md) |

## 排障速查

| 现象 | 先看 |
| --- | --- |
| 数据库连不上 | PostgreSQL 是否启动；`pallas.toml` 的 host/port/库名 |
| 忘记控制台口令 | [FAQ](../FAQ.md) |
| 协议端在线但群没反应 | 牛是否在群；**运行日志**有没有收到消息 |

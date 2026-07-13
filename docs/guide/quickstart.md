# 五分钟跑起来

把 **Pallas-Bot** 在本机跑通：能开控制台 → 能连 QQ → 群里 **牛牛帮助** 有回复。  
先别开分片，也先别装一堆扩展。

## 准备

| 项 | 要求 |
| --- | --- |
| Python | **3.12+**（推荐 [uv](https://docs.astral.sh/uv/)） |
| 数据库 | **PostgreSQL**（现行默认）；本机或 Docker 起一个空库即可 |
| QQ | 建议小号；协议端可以等 Bot 起来再配 |

从 3.x 升级的站点若仍用 MongoDB，可暂时保留，新站请用 PostgreSQL。

## 1. 克隆

```bash
git clone https://github.com/PallasBot/Pallas-Bot.git
cd Pallas-Bot
```

目录里应有 `pyproject.toml`、`config/pallas.example.toml`。

## 2. 装依赖

```bash
uv sync --extra pg
uv run python -c "import nonebot"
```

无报错即可。

## 3. 写配置

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

## 4. 启动

```bash
uv run nb run
```

日志里应能看到：

1. 没有数据库 `connection refused`  
2. **Web 控制台初始口令**（也可在 `data/pallas_console/` 找回）  
3. 浏览器打开 `http://127.0.0.1:8088/pallas/` 出现登录页  

::: tip 地址
本机用 `127.0.0.1`；远程把主机换成服务器 IP，并放行 **8088**。
:::

## 5. 连 QQ

Pallas-Bot **不会自己登录 QQ**，要靠 NapCat 等协议端。

1. 打开 `http://<主机>:8088/protocol/console/`  
2. 用与控制台相同口令登录  
3. **新建实例** → NapCat → 手机扫码  
4. 实例状态为 **在线**

群里发：

```text
牛牛帮助
```

有帮助图就通了。细节见 [连接 QQ](connect-qq.md)。

## 通了之后

▶ [安装官方扩展](install-extensions.md) · [网页控制台](web-console.md) · [运维快速开始](../maintainer/quickstart.md)  
▶ 卡住了：[排障](../maintainer/operate/troubleshooting.md) · [FAQ](../FAQ.md)

## 排障速查

| 现象 | 先看 |
| --- | --- |
| 数据库连不上 | PostgreSQL 是否启动；`pallas.toml` 的 host/port/库名 |
| 忘记控制台口令 | [FAQ](../FAQ.md) |
| 协议端在线但群没反应 | 牛是否在群；**运行日志**是否收到消息 |

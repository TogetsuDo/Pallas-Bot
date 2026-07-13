# 安装官方扩展

只讲 **官方扩展 pip 包**（决斗、MAA 等）。  
自己写的插件见 [安装插件 · local](install-plugins.md#二安装站点自有插件local)。

::: tip 和 core 的区别
- **core**：复读、帮助、控制台……`uv run nb run` 就有  
- **官方扩展**：商店或 `uv run pallas ext install …` 安装，**装完要重启**  
拿不准先看 [启动说明 · 一分钟对照](4.0-start.md#一分钟对照)。
:::

::: tip 从 3.x 升级
已有 `local/plugins/`（或旧副本）的站点**不必立刻 pip**——加载链仍以 local 优先。  
默认 `load_bundled_extra_plugins = "auto"`：pip 有则用 pip，没有则用镜像内副本。  
要统一走 PyPI 时，用商店一键装或 CLI（wheel **4.0.1+**）。
:::

## WebUI 安装（推荐）

1. 打开 `http://<主机>:8088/pallas/` 并登录  
2. 侧栏 **插件商店**  
3. 找到卡片 → **一键安装**  
4. 有 **安装并重启** 就点；否则装完自己重启  

| 商店显示 | 含义 |
| --- | --- |
| 未安装 | 还没 pip |
| 已安装待重启 | pip 有了，重启才加载 |
| 已加载 | 当前进程里已在跑 |

::: tip 一条糙规则
装、卸、升级扩展之后，都重启一次。比纠结能不能热载省心。
:::

## 命令行

在 **Pallas-Bot 仓库根**：

```bash
uv run pallas ext install pallas-plugin-duel
uv run pallas ext install pallas-plugin-maa
uv run pallas ext install pallas-plugin-who-is-spy
```

可抽查导入是否成功：

```bash
uv run python -c "import pallas_plugin_duel"
```

然后 **重启 Bot**。

## 扩展包对照表

| pip 包 | CLI | 包含（示例） |
| --- | --- | --- |
| `pallas-plugin-duel` | `uv run pallas ext install pallas-plugin-duel` | 决斗 |
| `pallas-plugin-who-is-spy` | `uv run pallas ext install pallas-plugin-who-is-spy` | 谁是卧底 |
| `pallas-plugin-maa` | `uv run pallas ext install pallas-plugin-maa` | MAA 远控 |
| `pallas-plugin-dream` | `uv run pallas ext install pallas-plugin-dream` | 做梦 |
| `pallas-plugin-draw` | `uv run pallas ext install pallas-plugin-draw` | 画画 |
| `pallas-plugin-ai-media` | `uv run pallas ext install pallas-plugin-ai-media` | 唱歌、酒后聊天 |
| `pallas-plugin-protocol` | `uv run pallas ext install pallas-plugin-protocol` | 协议端、上号 |
| ~~`pallas-plugin-llm-chat`~~ | 无需安装 | 已内置为 `llm_chat` core |
| `pallas-plugin-bot-status` | `uv run pallas ext install pallas-plugin-bot-status` | 在吗、报数 |
| ~~`pallas-plugin-community-stats`~~ | 无需安装 | 已内置为 `pb_stats` core |

口令与说明：[插件手册](../plugins/README.md)。

## Docker 用户

官方镜像往往是 **精简 core**，容器里不一定有 `uv` 现场装包。常见做法：

1. 构建时带上 extras（如 `PALLAS_UV_EXTRAS=perf,pg`，见 [Docker](../DockerDeployment.md)）  
2. 挂载 `local/plugins/`  
3. 在有源码的机器上装好扩展再整目录部署  

## 卸载

**WebUI**：商店 → **卸载**（仅 pip 包）

```bash
uv run pallas ext uninstall pallas-plugin-duel
```

卸载 pip **不会**删 `local/plugins/` 副本。装或卸之后都要 **重启 Bot**。

▶ [安装插件总览](install-plugins.md) · [口令与功能](usage.md) · [网页控制台](web-console.md)

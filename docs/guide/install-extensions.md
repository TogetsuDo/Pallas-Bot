# 安装官方扩展

本文只讲 **官方扩展 pip 包**（决斗、MAA 等）。  
站点自写插件请看 [安装插件 · local](install-plugins.md#二安装站点自有插件local)。

::: tip 和 core 的区别
- **core**：复读、帮助、控制台……随 `uv run nb run` 就有  
- **官方扩展**：通过插件商店或 `uv run pallas ext install pallas-plugin-xxx` 安装，**装完要重启 Bot**  
拿不准装不装？先看 [4.0 启动说明 · 一分钟对照](4.0-start.md#一分钟对照)。
:::

::: info 3.x 升级到 4.0
已有 **`local/plugins/`** 或 **`src/plugins/` 迁移副本** 的站点**不必立刻 pip 安装**——加载链仍以 **local 优先**。  
默认 **`load_bundled_extra_plugins = "auto"`**：pip 包已装则用 pip，未装则用仓库/镜像内 `src/plugins/` 副本。  
需要统一用 pip 包管理时，可在 WebUI 商店一键安装，或执行 `uv run pallas ext install pallas-plugin-xxx`（包来自 **PyPI**，首版可用 wheel 为 **4.0.1+**）。
:::

---

## WebUI 安装（一步步点）

1. 打开 `http://<主机>:8088/pallas/` 并登录  
2. 侧栏 **插件商店**  
3. 搜索或浏览卡片 → **一键安装**  
4. 有 **安装并重启** 就点它；否则装完后自己重启 Bot  

**如何确认成功**：

| 商店显示 | 含义 |
| --- | --- |
| 未安装 | 还没 pip 装 |
| 已安装待重启 | pip 有了，重启后才会加载 |
| 已加载 | 当前进程里已经在跑 |

::: tip 恭喜通了
商店显示 **已加载**，且群里对应口令有反应（例如决斗）= 扩展真的进当前进程了。卡在「待重启」就再重启一次 Bot。
:::

---

## 命令行安装

官方扩展包发布在 **PyPI**（包名 `pallas-plugin-*`，**4.0.1+** 起 wheel 含完整代码）。在仓库根目录执行（任选一个包）：

```bash
uv run pallas ext install pallas-plugin-duel
uv run pallas ext install pallas-plugin-maa
uv run pallas ext install pallas-plugin-who-is-spy
```

**如何确认成功**：

```bash
uv run python -c "import pallas_plugin_duel"   # 以决斗包为例，无 ImportError 即可
```

然后 **重启 Bot**。

---

## 扩展包对照表

| pip 包 | CLI 安装命令 | 包含插件（示例） |
| --- | --- | --- |
| `pallas-plugin-duel` | `uv run pallas ext install pallas-plugin-duel` | 决斗 |
| `pallas-plugin-who-is-spy` | `uv run pallas ext install pallas-plugin-who-is-spy` | 谁是卧底 |
| `pallas-plugin-maa` | `uv run pallas ext install pallas-plugin-maa` | MAA 远控 |
| `pallas-plugin-dream` | `uv run pallas ext install pallas-plugin-dream` | 做梦 |
| `pallas-plugin-draw` | `uv run pallas ext install pallas-plugin-draw` | 画画 |
| `pallas-plugin-ai-media` | `uv run pallas ext install pallas-plugin-ai-media` | 唱歌、酒后聊天 |
| `pallas-plugin-protocol` | `uv run pallas ext install pallas-plugin-protocol` | 协议端管理、上号 |
| ~~`pallas-plugin-llm-chat`~~ | ~~无需安装~~ | **已内置为 `llm_chat` core，无需安装** |
| `pallas-plugin-bot-status` | `uv run pallas ext install pallas-plugin-bot-status` | 在吗、报数 |
| ~~`pallas-plugin-community-stats`~~ | ~~无需安装~~ | **已内置为 `pb_stats` core，无需安装** |

完整说明与口令：[插件手册](../plugins/README.md)。

---

## Docker 用户

官方 `pallasbot/pallas-bot` 镜像往往是 **精简 core**，没有 `uv` 在容器里现场装包。

常见做法：

1. **构建镜像时** 带上主仓依赖 extras，例如 `PALLAS_UV_EXTRAS=perf,pg`（见 [Docker 部署](../DockerDeployment.md)）  
2. **挂载** `local/plugins/` 放插件代码  
3. 在**有源码的开发机** 用插件商店或 `uv run pallas ext install ...` 装好官方扩展后整目录部署  

---

## 卸载

**WebUI**：插件商店 → **卸载**（仅对 pip 安装的包）

**命令行**：

```bash
uv run pallas ext uninstall pallas-plugin-duel
```

卸载 pip **不会**删 `local/plugins/` 里的副本。  
无论装还是卸，改完后都要 **重启 Bot**。

---

▶ 下一步：[插件手册](../plugins/README.md) · [安装插件总览](install-plugins.md)

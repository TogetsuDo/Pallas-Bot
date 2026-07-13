# 安装官方插件

**官方插件**是 pip 包（决斗、MAA 等）。自己写的、第三方的见 [安装插件](install-plugins.md)。

::: tip 先分清两样东西
- **core**（复读、帮助、控制台…）：启动即有，不用装
- **官方插件**（决斗、MAA…）：**控制台插件商店**装/卸/更新，**装完要重启**

拿不准装什么？看 [把玩法 / AI 也装上 · 一分钟对照](4.0-start.md#一分钟对照)。
:::

::: tip 从 3.x 升级、本地已有插件？
`local/plugins/` 里已有的**不必立刻 pip**——同名时 local 优先。  
默认 `load_bundled_extra_plugins = "auto"`：有 pip 用 pip，没有就用镜像内副本。  
以前商店或 pip 装过的，升到 4.0 **一般不用重装**。
:::

## 第 1 步：控制台插件商店（推荐）

1. 打开 `http://<主机>:8088/pallas/` 并登录
2. 侧栏 **插件商店**
3. 找到卡片 → **一键安装**（或 **更新** / **卸载**）
4. 有 **安装并重启** 就点；否则装完在控制台或侧栏重启 Bot

| 商店显示 | 含义 |
| --- | --- |
| 未安装 | 还没 pip |
| 已安装待重启 | pip 有了，重启才加载 |
| 已加载 | 当前进程里已在跑 |

::: tip 一条糙规则
装、卸、升级之后都重启一次。日常改配置、看插件状态也留在控制台即可。
:::

**验收**：商店显示「已加载」，群里 **牛牛帮助** 出现新口令。

## 第 2 步（可选）：命令行

适合 **初次拉 Bot**、**SSH 升级本体**、或精简 Docker 没有商店按钮时。日常装/卸/更新官方插件仍优先用控制台。

在 **Pallas-Bot 仓库根**：

```bash
uv run pallas ext list
uv run pallas ext install pallas-plugin-duel --restart
```

无 WebUI 时可用；有控制台时以商店为准。

## 官方插件对照表

| pip 包 | 商店 / CLI | 包含（示例） |
| --- | --- | --- |
| `pallas-plugin-duel` | 插件商店 或 `pallas ext install` | 决斗 |
| `pallas-plugin-who-is-spy` | 同上 | 谁是卧底 |
| `pallas-plugin-maa` | 同上 | MAA 远控 |
| `pallas-plugin-dream` | 同上 | 做梦 |
| `pallas-plugin-draw` | 同上 | 画画 |
| `pallas-plugin-ai-media` | 同上 | 唱歌、酒后聊天 |
| `pallas-plugin-protocol` | 同上 | 协议端、上号 |
| ~~`pallas-plugin-llm-chat`~~ | 无需安装 | 已内置为 `llm_chat` core |
| `pallas-plugin-bot-status` | 同上 | 在吗、报数 |
| ~~`pallas-plugin-community-stats`~~ | 无需安装 | 已内置为 `pb_stats` core |

口令与说明：[插件手册](../plugins/README.md)。

## Docker 用户

官方镜像往往是 **精简 core**，容器里不一定有 `uv` 现场装包。常见做法：

1. 构建时带上 extras（如 `PALLAS_UV_EXTRAS=perf,pg`，见 [Docker](../DockerDeployment.md)）
2. 挂载 `local/plugins/`
3. 有控制台且能跑 `uv` 时，仍优先 **插件商店**；否则构建期预装或外部 `pallas ext install`

## 卸载

**控制台**：插件商店 → **卸载**（仅 pip 包）

无 UI 时：

```bash
uv run pallas ext uninstall pallas-plugin-duel --restart
```

卸载 pip **不会**删 `local/plugins/` 副本。

▶ [安装插件总览](install-plugins.md) · [口令与功能](usage.md) · [网页控制台](web-console.md)

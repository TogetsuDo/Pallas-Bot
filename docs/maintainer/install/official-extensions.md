# 安装官方扩展

这页帮你装、卸、更新官方扩展。

4.0 之后，大部分玩法和站点能力都从本体拆成了独立扩展包。先分清三种东西：

- `core`：随主仓启动就有，不用额外装。
- `official extensions`：走 PyPI 包分发，要单独装。
- `local / community plugins`：站点私有插件或社区仓库插件，一般放在 `local/plugins/`。

## 什么时候该看这页

- 你已经把主仓跑起来，但帮助菜单里没有决斗、MAA、谁是卧底之类的能力。
- 你想通过 WebUI 或 CLI 安装、卸载、更新官方扩展。
- 你在 Docker 或分片环境里，需要确认扩展到底是 pip 安装、镜像预装，还是 `local/plugins/` 副本在生效。

## 推荐安装顺序

1. 先用 WebUI 插件商店装。
2. 要脚本化或批量部署，用 `uv run pallas ext install ...`。
3. 只有镜像预装或构建镜像时，才考虑 `uv sync --extra ...` 这类依赖打包方案。

## 先确认运行前提

在仓库根目录跑一下：

```bash
uv --version
uv run pallas --help
```

满足这几条，WebUI 商店一般能直接装：

- 当前部署目录是完整的 Pallas-Bot 工作目录。
- 运行环境能执行 `uv`。
- 服务器能访问 PyPI，或你已经备好了可用的 wheel 缓存。

::: warning 精简 Docker 镜像例外
精简镜像往往没有在容器里现场装包的条件。这种情况更适合构建期预装，或在外部准备好目录后再部署。
:::

## 方式一：WebUI 插件商店

绝大多数情况都用它。

1. 打开 `http://<主机>:8088/pallas/` 并登录。
2. 进侧栏“插件商店”。
3. 找到目标扩展，点“安装”或“安装并重启”。
4. 页面提示“已安装待重启”时，重启一次 Bot。

安装后，商店状态一般是这几种：

| 状态 | 含义 |
| --- | --- |
| 未安装 | 当前环境里还没有 pip 包 |
| 已安装待重启 | 包已装入环境，但当前进程还没加载 |
| 已加载 | 当前运行进程已经在使用 |

## 方式二：命令行安装

适合批量部署、自动化脚本，或用不了 WebUI 的场景。

```bash
uv run pallas ext install pallas-plugin-protocol
uv run pallas ext install pallas-plugin-duel
uv run pallas ext install pallas-plugin-who-is-spy
uv run pallas ext install pallas-plugin-maa
uv run pallas ext install pallas-plugin-ai-media
uv run pallas ext install pallas-plugin-draw
uv run pallas ext install pallas-plugin-dream
uv run pallas ext install pallas-plugin-bot-status
```

以单个包为例：

```bash
uv run pallas ext install pallas-plugin-duel
uv run python -c "import pallas_plugin_duel"
```

`import` 不报错，只说明包已装入环境。要真正生效，还得重启 Bot。

## 常见官方扩展对照

| 包名 | 作用 |
| --- | --- |
| `pallas-plugin-protocol` | 协议端管理、账号上号、relologin 相关能力 |
| `pallas-plugin-duel` | 决斗与八角笼玩法 |
| `pallas-plugin-who-is-spy` | 谁是卧底 |
| `pallas-plugin-maa` | MAA 远控 |
| `pallas-plugin-ai-media` | 唱歌、酒后聊天等媒体类能力 |
| `pallas-plugin-draw` | 绘图相关能力 |
| `pallas-plugin-dream` | 做梦相关能力 |
| `pallas-plugin-bot-status` | 在吗、报数等状态类能力 |

以下能力已经在 4.0 回归 core，不需要再额外安装对应扩展：

- `llm_chat`
- `pb_stats`

## 安装后怎么确认真的生效

按这个顺序看：

1. WebUI 商店显示“已加载”。
2. WebUI 插件目录里能看到对应插件。
3. 群里发“牛牛帮助”，能看到新增能力。
4. 插件有配置页的话，对应页面能打开并读到配置。

::: warning 分片部署留意最后一步
有些扩展只在 worker 侧运行。能不能在控制台看到加载态，取决于 hub 聚合到的 worker 元数据是否正确。
:::

## 卸载与回滚

WebUI 商店能直接卸载 pip 安装的官方扩展。命令行也行：

```bash
uv run pallas ext uninstall pallas-plugin-duel
```

::: warning 同名副本会盖过卸载
- 卸载 pip 包不会删掉 `local/plugins/` 里的同名副本。
- 同名插件还在 `local/plugins/` 时，最终可能仍然被加载。
- 装、卸、升级之后都做一次明确重启，别只依赖热重载。
:::

## Docker 与预装场景

Docker 精简镜像的麻烦不是“装不上插件”，而是“容器里没有适合现场装包的环境”。

常见做法：

1. 构建镜像时把需要的 extras 或 wheel 一并打进去。
2. 把站点自有插件挂到 `local/plugins/`。
3. 在外部开发机装好扩展，再把整个工作目录部署到目标机。

::: warning
要稳定生产部署，别在运行中的容器里临时手工装扩展，再指望容器重建后还留着。
:::

## 什么时候需要重启

插件治理层把生效方式分成几类：

- `hot-reloadable`
- `workers-restart`
- `full-restart`

::: tip 一条糙但管用的规则
装、卸、升级扩展之后，都重启一次。比纠结某个插件能不能完整热重载省心多了。
:::

## 常见问题

### 商店里没有“一键安装”

优先检查：

- 当前环境是否有 `uv`
- 是否使用了精简镜像
- 服务器是否能访问 PyPI

### 安装成功但帮助菜单没变化

优先检查：

- 是否已经重启
- 是否被 `local/plugins/` 的同名插件覆盖
- 分片场景下目标能力是否实际运行在 worker

### Docker 里装完下一次容器重建又没了

这是典型的运行时临时改动未固化。改用镜像预装、挂载工作目录，或外部完成安装后再部署。

## 延伸阅读

- [插件治理](../operate/plugin-governance.md)
- [安装 Bot 本体](bot.md)
- [安装 WebUI](webui.md)
- [旧版官方扩展安装说明](../../guide/install-extensions.md)

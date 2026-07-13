# 安装插件

装之前先分清三类东西：

| 类型 | 举例 | 你要不要动手 |
| --- | --- | --- |
| **本体 core** | 复读、帮助、控制台 | 不用装，自带 |
| **官方扩展** | 决斗、MAA、谁是卧底 | 要单独装 |
| **站点 / 社区** | 自己写的、第三方 | 商店 git 装，或放 `local/plugins/` |

装完群里发 **牛牛帮助**，新功能应出现在帮助图里。

## 一、官方扩展（最常见）

决斗、MAA、唱歌等在 **pip 扩展包**里。

### 方法 A：网页一键装（推荐）

条件：目录有 `pyproject.toml`，系统能跑 `uv`。

1. 登录 `http://<主机>:8088/pallas/`
2. 侧栏 **插件商店**
3. **一键安装** → **安装并重启**（或装完手动重启）

商店显示「已加载」、帮助图出现新口令 = 成功。

::: details 没有「一键安装」？
常见原因：Docker 精简镜像、PATH 里没有 `uv`。改用方法 B，或构建时带上 `PALLAS_UV_EXTRAS`（见 [Docker](../DockerDeployment.md)）。  
无网络时：镜像内若有官方副本，默认 `load_bundled_extra_plugins = "auto"` 会在 pip 未装时用副本。
:::

### 方法 B：命令行

在 **Pallas-Bot 仓库根**：

```bash
uv run pallas ext install pallas-plugin-duel
```

装完 **必须重启**。包对照：[安装官方扩展](install-extensions.md#扩展包对照表)。

## 二、站点自有插件（local）

适合 Docker 精简环境、fork、或任意 NoneBot 插件目录。

```text
local/plugins/你的插件名/__init__.py
```

推荐配置：

```toml
[bootstrap]
extra_plugin_dirs = ["local/plugins"]
load_bundled_extra_plugins = "auto"
```

未配置时，目录下已有合法插件也会自动加载。然后 **重启 Bot**。  
与官方扩展 **同名时 local 优先**。细节：[站点定制](../maintainer/deploy/upgrade.md)。

## 三、pip / nb 插件（老方式，可选）

在根目录 `.env` 写模块名。别和 `webui.json` 同名键冲突。新站更推荐 **local/plugins**。

## 四、社区插件商店

索引默认来自 [community-plugin-index](https://github.com/PallasBot/community-plugin-index)。

1. `/pallas/` → **插件商店** → **社区插件**
2. **安装** → clone 到 `local/plugins/<ID>/`
3. 未收录：用 **从 Git 安装**
4. 重启 Bot

完整说明：[社区插件商店](community-plugin-store.md)。作者：[写社区插件并上架](community-plugin-author.md)。

## 列表在哪看

| 地方 | 内容 |
| --- | --- |
| [插件手册](../plugins/README.md) | 口令与配置 |
| 控制台 **插件目录** | 当前进程实际加载了谁 |
| **插件商店** | 官方扩展 + 社区插件 |

▶ [口令与功能](usage.md) · [进阶介绍](advanced.md)

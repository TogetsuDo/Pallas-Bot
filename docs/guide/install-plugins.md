# 安装插件

::: tip 装之前先看
| 类型 | 举例 | 要不要装 |
| --- | --- | --- |
| **本体 core** | 复读、帮助、控制台 | 随 Bot 自带，不用装 |
| **官方扩展** | 决斗、MAA、谁是卧底 | 默认**没装**，要单独安装 |
| **站点插件** | 你自己写的、第三方 nb 插件 | 商店 git 装或放到 `local/plugins/` |

装完后群里发 **牛牛帮助**，新功能应出现在帮助图里。
:::

---

## 一、安装官方扩展（最常见）

决斗、MAA、唱歌等玩法在 **pip 扩展包**里，不在默认 slim 镜像中。

### 方法 A：网页一键装（推荐）

**条件**：运行目录有 `pyproject.toml`，且系统能执行 `uv`。

1. 登录 `http://<主机>:8088/pallas/`  
2. 侧栏进 **插件商店**（或 **插件** → **插件商店**）  
3. 找到扩展包，点 **一键安装**  
4. 点 **安装并重启**（或装完后手动重启 Bot）

**如何确认成功**：商店里该包显示「已安装」或「已加载」；重启后 **插件目录** 能看到对应插件；群里 **牛牛帮助** 出现新口令。

::: details 没有「一键安装」按钮？
典型原因：

- Docker 官方镜像（没有完整源码树 / 没有 `uv`）  
- 服务器 PATH 里找不到 `uv`  

改用下面的 **方法 B**，或构建镜像时带上对应 `PALLAS_UV_EXTRAS`（见 [Docker 部署](../DockerDeployment.md)）。  
无网络时：若镜像内带 `src/plugins/` 官方副本，默认 **`load_bundled_extra_plugins = "auto"`** 会在 pip 未装时自动用副本（见 [安装官方扩展](install-extensions.md)）。
:::

### 方法 B：命令行装

在 **Pallas-Bot 仓库根目录**：

```bash
# 决斗
uv sync --extra plugins-duel

# 或 CLI
uv run pallas ext install pallas-plugin-duel
```

装完 **必须重启 Bot**：

```bash
# 前台跑的 Ctrl+C 后重新
uv run nb run

# 或用项目脚本（若已配置）
./scripts/pallas restart
```

扩展包与 `uv sync --extra` 对照表见 [安装官方扩展 · 包列表](install-extensions.md#扩展包对照表)。

---

## 二、安装站点自有插件（local）

适合：Docker 精简环境、整包 fork、或任意 NoneBot 插件目录。

1. 在仓库根建目录：

```text
local/plugins/你的插件名/__init__.py
```

2. 在 `config/pallas.toml` 启用（推荐；未配置时若目录下已有插件包也会自动加载）：

```toml
[bootstrap]
extra_plugin_dirs = ["local/plugins"]
load_bundled_extra_plugins = "auto"
```

`load_bundled_extra_plugins` 默认即为 `"auto"`，可省略。

3. **重启 Bot**

**如何确认成功**：WebUI **插件目录** 出现该插件；与官方扩展 **同名时 local 优先加载**。

细节：[站点定制与扩展](../architecture/site-customization-and-updates.md)。

---

## 三、pip / nb 插件（老方式，可选）

在根目录 `.env` 里写 NoneBot 插件模块名。  
**注意**：不要与 `webui.json` 里同名键冲突。新站点更推荐 **local/plugins**。

---

## 四、社区插件商店

第三方插件由 [**community-plugin-index**](https://github.com/PallasBot/community-plugin-index) 策展，Bot 默认拉取该仓 `index.json`；站点可用 `COMMUNITY_PLUGIN_INDEX_URL` 或本地 JSON 覆盖。

1. `/pallas/` → **插件商店** → **社区插件**  
2. **安装** → 插件 clone 到 `local/plugins/<ID>/`  
3. 未收录的仓库：点 **从 Git 安装** 填写 ID 与地址  
4. 重启 Bot（需 `extra_plugin_dirs` 或自动检测，见上文第二节）

完整说明：[社区插件商店](community-plugin-store.md)。**插件作者**见 [社区插件开发者指南](community-plugin-author.md)。

---

## 插件列表在哪看

- 文档：[插件手册](../plugins/README.md)（每个插件的口令与配置）  
- 网页：控制台 **插件目录**（当前进程实际加载了谁）  
- 商店：**插件商店**（官方扩展 + 社区插件）

---

▶ 下一步：[口令与功能](usage.md) · [进阶介绍](advanced.md)

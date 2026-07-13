# 社区插件商店

当前主线起，控制台 **插件商店 → 社区插件** 可从策展索引浏览第三方插件，并通过 git 安装到 `local/plugins/<id>/`。

与 **官方扩展**（pip / `uv sync --extra`）并存；**同名时 `local/plugins` 优先**。

---

## 索引从哪里来

Bot **不会**让每个站点维护者手改 `config/community_plugin_index.json` 来上架插件。日常策展在独立索引仓维护：

| 仓库 | 作用 |
| --- | --- |
| [**PallasBot/community-plugin-index**](https://github.com/PallasBot/community-plugin-index) | 官方策展 JSON（`index.json`） |
| 各插件作者仓库 | 实际 NoneBot 插件代码 |

**加载顺序**（后者为兜底）：

1. 环境变量 **`COMMUNITY_PLUGIN_INDEX_URL`**（若设置，覆盖默认远程）
2. 默认远程：`https://raw.githubusercontent.com/PallasBot/community-plugin-index/main/index.json`
3. `data/pallas_config/community_plugin_index.json`（站点本地覆盖）
4. `config/community_plugin_index.json`（主仓内置，通常为空）

远程拉取失败时会 **自动回退** 本地文件，离线/Docker 内网仍可用手写索引。

### 私有索引

自建索引仓时，在 `config/pallas.toml` 的 `[env]` 写入 raw JSON 地址：

```toml
[env]
COMMUNITY_PLUGIN_INDEX_URL = "https://example.com/my-index.json"
```

---

## WebUI 安装（推荐）

**条件**：运行环境可执行 `git`（WebUI 会 `git clone`）。

1. 打开 `/pallas/` → **插件商店** → **社区插件**
2. 选择条目 → **安装**（或 **安装并重启**）
3. 重启 Bot 后，在 **插件目录** 确认已加载

**无需索引**：点 **从 Git 安装**，填写插件 ID 与仓库地址即可（与索引安装落点相同）。

安装目标路径：`local/plugins/<插件 ID>/`。

### `extra_plugin_dirs`

推荐在 `config/pallas.toml` 显式配置：

```toml
[bootstrap]
extra_plugin_dirs = ["local/plugins"]
```

若 **未配置** 但 `local/plugins/` 下已有有效插件包（含 `__init__.py`），启动时也会 **自动纳入** 加载链；仍建议写上配置，便于文档与排障。

Docker 挂载示例见 [站点定制 · Docker](../architecture/site-customization-and-updates.md#docker--外挂插件卷)。

---

## 详情弹窗：README 与更新日志

点击商店卡片打开详情弹窗，可在 **README** / **更新日志** 两个分栏间切换：

- **README**：拉取仓库根目录 `README.md`。
- **更新日志**：优先展示仓库根目录 `CHANGELOG.md`；社区插件若仓库未提供，则对已安装到 `local/plugins/<id>/` 的副本按本地 git 提交历史**自动生成**（仅列提交标题）。

官方扩展与社区插件都适用。作者维护 `CHANGELOG.md` 的约定见 [社区插件开发者指南 · 版本与更新日志](community-plugin-author.md#版本与更新日志)。

---

## 手动投放（不经过商店）

与商店安装结果相同：把 NoneBot 插件目录放到 `local/plugins/<名>/`，配置 `extra_plugin_dirs`（或依赖自动检测），重启 Bot。

适合：无法访问 git、或插件不在公共索引中。

---

## 收录第三方插件

向 [**community-plugin-index**](https://github.com/PallasBot/community-plugin-index) 提交 PR，在 `index.json` 追加条目。要求见该仓 README（开源、唯一 id、标准 NoneBot 结构等）。**README 插件列表由该仓 CI 根据 JSON 自动更新**，无需手工改表格。

**开发者**：目录自检、生成索引 JSON、图标约定见 [社区插件开发者指南](community-plugin-author.md)。

索引 **只存元数据**，不托管插件源码。未收录的插件仍可通过 **从 Git 安装** 或手工 `local/plugins/` 使用。

---

## 与官方扩展、`auto` bundled 的关系

| 类型 | 安装方式 | 加载优先级 |
| --- | --- | --- |
| 社区 / 站点插件 | git clone 或手工 → `local/plugins/` | **最高** |
| 官方 pip 扩展 | `uv sync --extra` / 商店一键装 | 中 |
| 仓库内 `src/plugins/` 副本 | 默认 **`load_bundled_extra_plugins = "auto"`**：pip 未装时用副本 | 低 |

Docker 等无法 pip 的环境：镜像若带 `src/plugins/` 官方副本，`auto` 会在无 pip 包时自动加载；社区插件仍推荐 `local/plugins/`。

详见 [安装插件 · 官方扩展](install-plugins.md#一安装官方扩展最常见) 与 [安装官方扩展](install-extensions.md)。

---

## 相关实现

- 索引加载：`src/console/webui/community_plugin_index.py`
- 图标推断：`src/console/webui/community_plugin_assets.py`
- 安装/卸载：`src/console/webui/community_plugin_install.py`
- 作者 CLI：`tools/community_plugin_author.py`
- API：`GET /pallas/api/plugins/community-store`

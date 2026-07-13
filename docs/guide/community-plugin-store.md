# 社区插件商店

从策展索引浏览第三方插件，用 git 装到 `local/plugins/<id>/`。

路径：控制台 **插件商店 → 社区插件**。  
与 **官方插件**（pip）并存；**同名时 `local/plugins` 优先**。

---

## 索引从哪来

日常策展在独立索引仓，不必手改主仓里的空 JSON：

| 仓库 | 作用 |
| --- | --- |
| [**PallasBot/community-plugin-index**](https://github.com/PallasBot/community-plugin-index) | 官方策展 JSON（`index.json`） |
| 各插件作者仓库 | 实际 NoneBot 插件代码 |

**加载顺序**（后者为兜底）：

1. 环境变量 **`COMMUNITY_PLUGIN_INDEX_URL`**（若设置，覆盖默认远程）
2. 默认远程：`https://raw.githubusercontent.com/PallasBot/community-plugin-index/main/index.json`
3. `data/pallas_config/community_plugin_index.json`（站点本地覆盖）
4. `config/community_plugin_index.json`（主仓内置，通常为空）

远程拉失败会 **自动回退** 本地文件，离线 / Docker 内网仍可用手写索引。

### 私有索引

```toml
[env]
COMMUNITY_PLUGIN_INDEX_URL = "https://example.com/my-index.json"
```

---

## WebUI 安装（推荐）

**条件**：运行环境能跑 `git`。

1. 打开 `/pallas/` → **插件商店** → **社区插件**
2. 选条目 → **安装**（或 **安装并重启**）
3. 重启 Bot 后，在 **插件目录** 确认已加载

**不走索引**：点 **从 Git 安装**，填插件 ID 与仓库地址即可（落点相同）。

安装路径：`local/plugins/<插件 ID>/`。

### `extra_plugin_dirs`

建议写明：

```toml
[bootstrap]
extra_plugin_dirs = ["local/plugins"]
```

未配置但目录下已有有效插件包时，启动也会自动纳入；仍建议写上，方便排障。

Docker 挂载见 [升级 · Docker 外挂插件](../maintainer/deploy/upgrade.md#docker--外挂插件卷)。

---

## 详情：README 与更新日志

点商店卡片打开详情：

- **README**：仓库根目录 `README.md`
- **更新日志**：优先 `CHANGELOG.md`；没有则对已装副本按 git 提交标题兜底生成

作者约定见 [写社区插件并上架 · 版本与更新日志](community-plugin-author.md#版本与更新日志)。

---

## 手动投放

把插件目录放到 `local/plugins/<名>/`，配好 `extra_plugin_dirs`（或靠自动检测），重启 Bot。结果与商店安装相同。

适合：不能访问 git，或不在公共索引里。

---

## 收录第三方插件

向 [**community-plugin-index**](https://github.com/PallasBot/community-plugin-index) 提 PR，在 `index.json` 追加条目。  
**README 插件列表由 CI 根据 JSON 自动更新**，不用手改表格。

作者自检：[写社区插件并上架](community-plugin-author.md)。

索引 **只存元数据**，不托管源码。未收录仍可用 **从 Git 安装** 或手工 `local/plugins/`。

---

## 和官方插件、`auto` bundled 的关系

| 类型 | 安装方式 | 加载优先级 |
| --- | --- | --- |
| 社区 / 站点插件 | git clone 或手工 → `local/plugins/` | **最高** |
| 官方 pip 扩展 | `uv sync --extra` / 商店一键装 | 中 |
| 仓库内 `src/plugins/` 副本 | 默认 **`load_bundled_extra_plugins = "auto"`**：pip 未装时用副本 | 低 |

详见 [安装插件](install-plugins.md) 与 [安装官方插件](install-extensions.md)。

---

## 相关实现

- 索引加载：`src/console/webui/community_plugin_index.py`
- 图标推断：`src/console/webui/community_plugin_assets.py`
- 安装/卸载：`src/console/webui/community_plugin_install.py`
- 作者 CLI：`tools/community_plugin_author.py`
- API：`GET /pallas/api/plugins/community-store`

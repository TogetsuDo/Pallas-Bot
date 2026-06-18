# 社区插件开发者指南

面向 **第三方 NoneBot 插件**作者：如何让站点管理员能发现、安装你的插件，以及如何自检与提交索引。

站点管理员安装说明见 [社区插件商店](community-plugin-store.md)；插件结构见 [插件结构](../develop/plugin/structure.md)。

---

## 三种接入方式

| 方式 | 谁用 | 做法 |
| --- | --- | --- |
| **索引收录** | 希望被公开展示的作者 | 向 [community-plugin-index](https://github.com/PallasBot/community-plugin-index) 提 PR |
| **Git 直装** | 站点管理员 | WebUI **插件商店 → 社区插件 → 从 Git 安装**（无需索引） |
| **手工投放** | 开发者 / 内网 | 复制目录到 `local/plugins/<id>/` |

三种方式安装结果相同；**同名时 `local/plugins` 优先于官方扩展**。

---

## 插件目录要求

最小结构（与 NoneBot 一致）：

```text
my_plugin/
├── __init__.py          # 含 __plugin_meta__（PluginMetadata）
├── README.md            # 商店详情页会尝试展示
└── assets/
    └── icon.png         # 推荐 256×256，商店卡片图标
```

约定：

- **插件 ID**：小写字母开头，仅 `a-z` / `0-9` / `_`，最长 64；与 `local/plugins/<id>/` 目录名一致。
- 可在 `__init__.py` 定义 `PLUGIN_ID = "my_plugin"`，便于与目录名对齐。
- 依赖 Pallas 内核能力时，在 README 注明最低 **Pallas 4.0** 版本。

可选：接入 [cmd_perm](../common/cmd_perm/README.md) 的 `command_permissions`，帮助图会自动展示「何人可用」。

### 社区插件画像（L1 / L2）

公开收录与 WebUI 插件页「指令与能力」依赖 **metadata 声明完整度**，分档见 [插件治理与社区生态路线 · 社区插件画像](../architecture/plugin-governance-community-roadmap.md#社区插件画像l0l3)：

| 档位 | 要点 |
| --- | --- |
| **L1（索引默认门槛）** | `command_permissions` + `menu_data` + 规范 `usage` |
| **L2（优选）** | L1 + `command_limits` + 鉴权 ID 一致；口令推荐 `plugin_sdk` |

`check` 的 L1/L2 规则将随 **G-P2** 落地；当前仍以目录/ID/图标为主。

---

## 图标与索引元数据

商店卡片图标优先级：

1. 索引条目中的 **`icon`**（完整 URL）
2. 自动推断：`https://raw.githubusercontent.com/<owner>/<repo>/<ref>/assets/icon.png`（Gitee 同理）
3. 作者 GitHub 头像（`author` 或仓库 owner）

**推荐**：在仓库放 `assets/icon.png`，索引里只写 `repository` 即可；不必重复写 `icon` URL。

索引单条示例（追加到 `index.json` 的 `plugins` 数组）：

```json
{
  "id": "my_plugin",
  "name": "我的插件",
  "description": "一句话说明功能。",
  "repository": "https://github.com/you/my_plugin.git",
  "ref": "main",
  "author": "your_github_id",
  "tags": ["工具"],
  "min_pallas_version": "4.0.0"
}
```

提交 PR 前更新根级 **`updated_at`**（ISO 日期），便于客户端刷新图标缓存。

---

## 作者工具 CLI

在 **Pallas-Bot 仓库根目录**执行：

### 校验插件目录

```bash
uv run python tools/community_plugin_author.py check path/to/my_plugin
```

检查 `__init__.py`、ID 规范、推荐 `assets/icon.png` 与 README。

### 生成索引条目

从插件目录读取 `PluginMetadata` 草稿：

```bash
uv run python tools/community_plugin_author.py index-entry ./my_plugin \
  --repository https://github.com/you/my_plugin.git \
  --author your_github_id \
  --tags "工具,示例"
```

无本地目录时也可仅按仓库生成：

```bash
uv run python tools/community_plugin_author.py index-entry \
  --repository https://github.com/you/my_plugin.git \
  --id my_plugin \
  --name "我的插件" \
  --description "简介"
```

将 stdout 中的 JSON 对象追加到 [community-plugin-index](https://github.com/PallasBot/community-plugin-index) 的 `index.json`。

### README 插件列表（索引仓 CI 自动）

**无需手工改 README 表格。** 索引仓 CI 在 PR / push `main` 时运行 `tools/sync_readme.py`，根据 `index.json` 更新 README 中 `<!-- PLUGIN_LIST_START -->` … `<!-- PLUGIN_LIST_END -->` 区段。

本地可选预览：

```bash
# 在 community-plugin-index 仓库根目录
python tools/sync_readme.py --write
python tools/sync_readme.py --check
```

### 校验 index.json

```bash
uv run python tools/community_plugin_author.py validate-index
# 或指定路径
uv run python tools/community_plugin_author.py validate-index /path/to/index.json
```

索引仓另有 `python tools/validate_index.py`（与 CI 一致）。

---

## 收录 PR 检查清单

- [ ] 开源仓库，HTTPS clone 地址可访问（GitHub / Gitee / GitLab / Codeberg）
- [ ] 插件 ID 全局唯一，符合命名规范
- [ ] 仓库根即为 NoneBot 插件包（含 `__init__.py`），或 README 说明 clone 后路径
- [ ] `assets/icon.png` 或索引中提供 `icon`
- [ ] `description` 一句说清功能；`min_pallas_version` 如实填写
- [ ] 更新 `index.json` 的 `updated_at`

合并后 CI 会同步 README 插件列表；Bot 拉取远程 `index.json` 即可，无需再手工改 README。

---

## 私有 / 公会索引

站点可在 `config/pallas.toml` 使用自建索引，无需进入公共策展仓：

```toml
[env]
COMMUNITY_PLUGIN_INDEX_URL = "https://example.com/my-guild-index.json"
```

或落盘 `data/pallas_config/community_plugin_index.json` 覆盖远程。

---

## 相关文档与代码

| 项 | 位置 |
| --- | --- |
| 商店使用 | [community-plugin-store.md](community-plugin-store.md) |
| 站点 `local/plugins` | [站点定制](../architecture/site-customization-and-updates.md) |
| 索引加载 | `src/console/webui/community_plugin_index.py` |
| Git 安装 | `src/console/webui/community_plugin_install.py` |
| 作者工具 | `tools/community_plugin_author.py` |
| 治理与生态路线 | [plugin-governance-community-roadmap.md](../architecture/plugin-governance-community-roadmap.md) |

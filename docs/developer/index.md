# Developer

Pallas-Bot 开发者入口。第一次跑通见 [五分钟跑起来](/guide/quickstart)；运维索引见 [运维入口](/maintainer/quickstart)。

## 从这里动手（推荐）

1. **[写第一个插件](plugin-development/first-plugin.md)** — 可复制的 `local/plugins` 示例  
2. [Golden Plugin](plugin-development/golden-plugin.md) — 正式骨架  
3. [cmd_perm](/common/cmd_perm) — 权限与帮助「何人可用」  
4. [Cookbook](plugin-development/pallas-api-cookbook.md) — `pallas.api.*` 一览  

## 读者分流

| 角色 | 顺序 |
| --- | --- |
| 社区 / 站点插件 | [首插件](plugin-development/first-plugin.md) → [入门](plugin-development/getting-started.md) → [配置](plugin-development/config-and-webui.md) → [发布](plugin-development/publishing.md) |
| 官方扩展 | [Core vs 扩展](architecture/core-vs-extensions.md) → [Golden](plugin-development/golden-plugin.md) → [元数据](plugin-development/metadata.md) → [发布](plugin-development/publishing.md) |
| 主仓 / 平台 | [架构总览](architecture/overview.md) → [分片](architecture/shard-runtime.md) → [配置存储](architecture/config-storage.md) → [治理](architecture/plugin-governance.md) |

按身份短索引：[Author](author/index.md)。

## 稳定边界

| 边界 | 约定 |
| --- | --- |
| 能力分层 | `core` / `official extension` / `community extension` |
| 插件公开 API | 仅 `pallas.api.*`（社区强制） |
| WebUI | 源码在 `Pallas-Bot-WebUI`；主仓 `data/pb_webui/public/` 为运行产物 |
| AI | `Pallas-Bot-AI` 可选；产品语义在主仓 |
| 配置合并 | `pallas.toml` → `.env` → `webui.json` |
| 分片 | hub / worker / Redis；消息主路径在 worker |

## 目录

| 区 | 内容 |
| --- | --- |
| [architecture/](architecture/overview.md) | 运行时、分层、分片、配置、治理 |
| [plugin-development/](plugin-development/first-plugin.md) | 首插件、骨架、元数据、配置、测试、发布 |
| [reference/](reference/repo-layout.md) | 仓库布局、API 分层、控制台约定 |

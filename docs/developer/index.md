# Developer

Pallas 4.0 开发者契约入口。维护者部署见 [`docs/maintainer/`](../maintainer/quickstart.md)。深度设计稿见 [`docs/architecture/`](../architecture/)（非主入口）。

## 读者分流

| 角色 | 必读顺序 |
| --- | --- |
| 社区 / 站点插件作者 | [入门](plugin-development/getting-started.md) → [Golden Plugin](plugin-development/golden-plugin.md) → [pallas.api](plugin-development/pallas-api-cookbook.md) → [配置](plugin-development/config-and-webui.md) → [发布](plugin-development/publishing.md) |
| 官方扩展作者 | [Core vs 扩展](architecture/core-vs-extensions.md) → [Golden Plugin](plugin-development/golden-plugin.md) → [元数据](plugin-development/metadata.md) → [Reload / Activation](plugin-development/reload-and-activation.md) → [发布](plugin-development/publishing.md) |
| 主仓 / 平台维护者 | [架构总览](architecture/overview.md) → [分片](architecture/shard-runtime.md) → [配置存储](architecture/config-storage.md) → [治理](architecture/plugin-governance.md) → [仓库布局](reference/repo-layout.md) |

按作者身份整理的短索引：[Author](author/index.md)。

## 稳定边界（事实）

| 边界 | 约定 |
| --- | --- |
| 能力分层 | `core` / `official extension` / `community extension` |
| 插件公开 API | 仅 `pallas.api.*`（社区扩展强制） |
| WebUI | 源码在 `Pallas-Bot-WebUI`；主仓 `data/pb_webui/public/` 为运行产物 |
| AI | `Pallas-Bot-AI` 为可选 runtime；产品语义与记忆边界在主仓 |
| 配置合并 | `pallas.toml` → 遗留 `.env` → `webui.json`（后者覆盖） |
| 分片 | hub / worker / Redis 职责分离；消息处理默认在 worker |

## 目录

| 区 | 内容 |
| --- | --- |
| [architecture/](architecture/overview.md) | 运行时、分层、分片、配置、治理 |
| [plugin-development/](plugin-development/getting-started.md) | 骨架、元数据、配置、测试、发布 |
| [reference/](reference/repo-layout.md) | 仓库布局、API 分层、控制台约定、文风 |

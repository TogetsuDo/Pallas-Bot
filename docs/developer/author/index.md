# Author

按作者身份索引 Developer 文档。非第三条主线。

## 路径

| 身份 | 顺序 |
| --- | --- |
| 主仓 / 平台 | [架构总览](../architecture/overview.md) → [分片](../architecture/shard-runtime.md) → [治理](../architecture/plugin-governance.md) → [仓库布局](../reference/repo-layout.md) |
| 官方扩展 | [Core vs 扩展](../architecture/core-vs-extensions.md) → [Golden](../plugin-development/golden-plugin.md) → [元数据](../plugin-development/metadata.md) → [发布](../plugin-development/publishing.md) |
| 社区插件 | [入门](../plugin-development/getting-started.md) → [配置](../plugin-development/config-and-webui.md) → [Cookbook](../plugin-development/pallas-api-cookbook.md) → [Internal 边界](../reference/internal-api.md) |

## 边界速查

| 主题 | 约定 |
| --- | --- |
| 能力分层 | core / official / community |
| 公开 API | 社区仅 `pallas.api.*` |
| WebUI | 源码仓 ≠ 主仓运行产物 |
| 分片 | activation / claim 按 worker 设计 |

## 相关

- [Developer](../index.md)

# 架构文档（素材层）

这一层不是文档站的正式入口，现行开发文档在 [`docs/developer/`](../developer/index.md)。

这里留下两类东西：

- **仍描述现行事实的细节页**，会逐步提炼进 `developer/` 或 `maintainer/`。
- **深层设计文档**，已挪到 [`internal/`](internal/)，作为边界与契约的参考，不再当新人入口。

## 想看当前架构，先去这里

- [架构总览](../developer/architecture/overview.md)
- [Core 与扩展](../developer/architecture/core-vs-extensions.md)
- [分片运行时](../developer/architecture/shard-runtime.md)
- [配置存储](../developer/architecture/config-storage.md)

## 这一层还剩什么

仍描述现行事实、有参考价值的细节页：

- [运行配置存储](settings-storage.md)
- [多进程分片](bot_process_sharding.md)
- [热重载分级](hot-reload-tiers.md)
- [插件目录约定](plugin-convention.md)
- [站点定制与在线更新](site-customization-and-updates.md)

深层设计与契约（[`internal/`](internal/)）：核心契约、内核插件统一化、AI 终态架构与实施、包布局、中央入站调度。这些更像“为什么要这样设计”的底稿，按需再读。

::: tip
旧路线图、阶段验收类文档已经从这里清掉。剩下的内容只作素材，不代表它们仍是推荐入口。
:::

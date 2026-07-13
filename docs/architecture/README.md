# 架构文档（素材层）

这一层不是文档站的正式入口。现行上线文档：

- 运维：[Maintainer](../maintainer/quickstart.md)
- 开发：[Developer](../developer/index.md)

这里只留两类内容：

- **仍描述现行事实的细节页**（会逐步提炼进 `maintainer/` / `developer/`）
- **契约与布局底稿**（[`internal/`](internal/)），回答「为什么这样设计」，不是安装入口

## 想看当前架构，先去这里

- [架构总览](../developer/architecture/overview.md)
- [Core 与扩展](../developer/architecture/core-vs-extensions.md)
- [分片运行时](../developer/architecture/shard-runtime.md)
- [配置存储](../developer/architecture/config-storage.md)

## 这一层还剩什么

仍有参考价值的细节页：

- [运行配置存储](settings-storage.md)
- [多进程分片](bot_process_sharding.md)
- [热重载分级](hot-reload-tiers.md)
- [插件目录约定](plugin-convention.md)
- [站点定制与在线更新](site-customization-and-updates.md)
- [Ingress 入站管线](ingress-pipeline.md)

契约与布局底稿（[`internal/`](internal/)）：

- [核心契约](internal/pallas-core-contract.md)
- [AI 终态架构](internal/pallas-final-ai-shape.md)
- [AI 实施摘要](internal/pallas-ai-implementation.md)
- [包布局](internal/pallas-package-layout.md)
- [内核插件统一化](internal/core-plugin-unification-design.md)
- [中央入站调度](internal/central-ingress-dispatch.md)
- [多牛社交品牌契约](internal/multi-bot-social-brand-contract.md)

对标前辈 bot 的 OPT 清单已迁到 Notion 里程碑「4.0 前辈对标优化路线」，仓库内不再维护双份。

# Pallas-Bot 4.0 · 本体瘦身与插件分家（归档）

> **状态**：归档，安装与迁移信息仍保留。  
> **现行总纲**：见 [Pallas 核心契约](pallas-core-contract.md)。

## 本文仍保留什么

- core / extra / local 的历史迁移背景
- 旧 3.x / 4.0 升级说明入口
- 扩展安装路径的历史说明

## 当前结论

- 插件分家已成为既有现实，不再作为阶段路线维护。
- 后续只在现行文档中维护仍未完成的事项。

## 仍有效的运维结论

- `local/plugins` 仍是最高优先级覆盖路径。
- 官方扩展可通过 WebUI 商店或 `uv sync --extra ...` 安装。
- core / extra / local 加载规则以运行时代码为准。

## 仍在持续建设

- 插件治理页：见 [插件治理与社区生态路线](plugin-governance-community-roadmap.md)
- AI 扩展运行时收口：见 [Pallas AI 实施与联调](pallas-ai-implementation.md)
- 总契约与品牌边界：见 [Pallas 核心契约](pallas-core-contract.md)

## 历史迁移背景

4.0 的“瘦身”历史上主要指：

- 将玩法与重依赖插件从本体默认树中解耦
- 让 core / extra / local 三层加载关系稳定下来
- 让 WebUI、CLI、官方扩展商店与本体形成统一运维体验

## 保留说明

本文件仅作为迁移历史与旧链接稳定目标保留。  
新的建设项不再追加到本文件，请改看 [Pallas 核心契约](pallas-core-contract.md) 与各专项现行文档。

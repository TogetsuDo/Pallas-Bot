# 通用知识源 / RAG 接入模型

## 术语

| 术语 | 含义 |
| --- | --- |
| `knowledge source` | 可被声明、治理与检索的外部知识提供方（插件或产品域） |
| `retrieval mode` | 知识如何进入模型上下文：`prompt_inject` / `metadata_only` / `tool_only` |
| `usage boundary` | 知识块注入时的免责声明与优先级（不得覆盖核心人设） |
| `scope` | 知识作用域：`global` / `group` / `user` |
| `authority` | 谁可声明与启用该知识源（插件元数据 + 运行时治理开关） |

## 与现有资产层的关系

| 资产 | 是否纳入本抽象 | 说明 |
| --- | --- | --- |
| `persistent_memory` | 否 | 群内 teach 记忆，走 `memory/inject.py` |
| `corpus_foundation` | 否 | 接话语料底盘，服务 repeater |
| `tool-backed KB` | 否 | 如方舟干员查询，走 `llm_tools` |
| `generic knowledge source` | 是 | 插件声明的 FAQ / 规则集 / 静态文档 |

首版仅支持**文本块关键词检索 + prompt 注入**；embedding / vector store / rerank 通过接口预留，不在本阶段实现。

## Bot 职责

- 插件通过 `extra['knowledge_sources']` 声明知识源
- `memory_governance` 提供 `can_read_generic_knowledge()` 门控
- `knowledge/inject.py` 统一检索与 system prompt 注入
- `client.py` 将 `knowledge_policy` / `retrieval_trace` 写入 AI metadata

## AI 职责

- 接收并保留 Bot 下发的 knowledge metadata（契约版本 `1`）
- `agent_stage_plan` 兼容 `retrieve` 阶段（首版不执行 AI 侧检索）
- `agent_trace` 透传 `retrieval_trace` 供观测

## 插件声明示例

```python
from pallas.product.llm.knowledge.declare import knowledge_source_row

extra={
    "knowledge_sources": [
        knowledge_source_row(
            source_id="my_plugin.faq",
            title="插件 FAQ",
            description="本插件常见问题",
            chunks=[
                {"title": "用法", "content": "...", "keywords": "帮助,用法"},
            ],
        ),
    ],
}
```

## 何时用 inject vs tool

- **inject**：短文本、FAQ、规则集、产品说明（首版默认）
- **tool**：需精确查询、参数化、懒加载的大 KB（沿用 `llm_tools`）

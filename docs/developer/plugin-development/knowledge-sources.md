# 插件知识源与本地知识目录

插件可通过 `PluginMetadata.extra['knowledge_sources']` 声明静态文本知识源；Bot 在 LLM 闲聊前统一检索并注入 system prompt。另支持从 `data/pallas_knowledge/` 加载 Markdown / JSONL。

## 官方参考

本体 [`packages/llm_chat`](../../packages/llm_chat/__init__.py) 与内置 FAQ（`pallas.bot_faq`）可作为对照。

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
                {
                    "title": "用法",
                    "content": "发送 xxx 触发功能。",
                    "keywords": "用法,帮助,怎么用",
                },
            ],
        ),
    ],
}
```

## 本地目录 ingest

| 项 | 说明 |
| --- | --- |
| 路径 | `data/pallas_knowledge/**/*.md` 或 `.jsonl` |
| 开关 | `LLM_KNOWLEDGE_FILE_INGEST_ENABLED`（默认开） |
| source_id | `pallas.file_ingest` |
| Markdown | 按 `#` 标题切块 |
| JSONL | 每行 `{"title","content","keywords"}` |

示例见仓库内 `data/pallas_knowledge/example.md`。

## 知识源 vs LLM Tool

| 场景 | 推荐 |
| --- | --- |
| 短 FAQ、规则、产品说明 | `knowledge_sources` / 本地目录 + prompt 注入 |
| 参数化查询、大 KB | `llm_tools` |

## 治理与检索

| 变量 | 默认 | 说明 |
| --- | --- | --- |
| `LLM_KNOWLEDGE_SOURCES_ENABLED` | 开 | 总闸 |
| `LLM_VECTOR_RETRIEVE` | `hybrid` | `hybrid` / `keyword` / `embedding`；向量失败回落关键词 |
| `LLM_EMBEDDING_MODEL` | `stub` | 对齐 AI 仓 embeddings |
| `LLM_KNOWLEDGE_TOP_K` | `3` | 注入块数上限 |

读取受 `memory_governance.can_read_generic_knowledge()` 门控。运维视角见 [LLM 与 AI](../../maintainer/operate/llm-and-ai.md)。

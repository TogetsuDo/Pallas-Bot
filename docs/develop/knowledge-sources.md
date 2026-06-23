# 插件知识源声明

插件可通过 `PluginMetadata.extra['knowledge_sources']` 声明静态文本知识源，由 Bot 在 LLM 闲聊前统一检索并注入 system prompt。

## 官方参考实现

本体插件 [`packages/llm_chat/__init__.py`](../../packages/llm_chat/__init__.py) 同时声明了 `llm_tools`（动作）与 `knowledge_sources`（FAQ 说明），可作为对照：

- **`llm_chat.clear` tool**：用户明确要求忘记时，由模型触发清空动作
- **`llm_chat.faq` knowledge source**：回答「怎么聊 / 怎么清空」类问题时注入参考文案

## 声明示例

```python
from pallas.product.llm.knowledge.declare import knowledge_source_row

__plugin_meta__ = PluginMetadata(
  # ...
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
  },
)
```

## 何时用知识源 vs LLM Tool

| 场景 | 推荐方式 |
| --- | --- |
| 短 FAQ、规则说明、产品文案 | `knowledge_sources` + prompt 注入 |
| 需参数查询、懒加载、大 KB | `llm_tools` |

## 治理与配置

- 全局开关：`LLM_KNOWLEDGE_SOURCES_ENABLED`（默认开启）
- 读取受 `memory_governance.can_read_generic_knowledge()` 门控
- 与 `persistent_memory`、`corpus_foundation`、专用 tool-KB 相互独立

详见 [knowledge-source-rag.md](../architecture/internal/knowledge-source-rag.md)。

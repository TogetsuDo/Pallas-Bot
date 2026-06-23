"""通用知识源接入。"""

from pallas.product.llm.knowledge.declare import knowledge_source_row
from pallas.product.llm.knowledge.inject import enrich_system_with_knowledge_sources
from pallas.product.llm.knowledge.models import (
    KNOWLEDGE_CONTRACT_VERSION,
    KnowledgeInjectionResult,
    KnowledgeSourceDecl,
)
from pallas.product.llm.knowledge.registry import knowledge_metadata_payload

__all__ = [
    "KNOWLEDGE_CONTRACT_VERSION",
    "KnowledgeInjectionResult",
    "KnowledgeSourceDecl",
    "enrich_system_with_knowledge_sources",
    "knowledge_metadata_payload",
    "knowledge_source_row",
]

"""多语料源：local + 可选 fed / community。"""

from src.features.corpus.composite_repo import CompositeContextRepository
from src.features.corpus.config import clear_corpus_config_cache, get_corpus_config
from src.features.corpus.factory import maybe_wrap_composite
from src.features.corpus.merge import merge_contexts

__all__ = [
    "CompositeContextRepository",
    "clear_corpus_config_cache",
    "get_corpus_config",
    "maybe_wrap_composite",
    "merge_contexts",
]

"""多语料源：local + 可选 fed / community。"""

from src.common.corpus.composite_repo import CompositeContextRepository
from src.common.corpus.config import clear_corpus_config_cache, get_corpus_config
from src.common.corpus.factory import maybe_wrap_composite
from src.common.corpus.merge import merge_contexts

__all__ = [
    "CompositeContextRepository",
    "clear_corpus_config_cache",
    "get_corpus_config",
    "maybe_wrap_composite",
    "merge_contexts",
]

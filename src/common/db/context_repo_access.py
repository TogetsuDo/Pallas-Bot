"""进程内共享 ContextRepository（enroll 后可失效重建）。"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.common.db.repository import ContextRepository

_holder: ContextRepository | None = None


def get_shared_context_repository() -> ContextRepository:
    global _holder
    if _holder is None:
        from src.common.db import make_context_repository

        _holder = make_context_repository()
    return _holder


def invalidate_shared_context_repository() -> None:
    global _holder
    _holder = None


class LazyContextRepository:
    """供 repeater 等模块 `context_repo.xxx` 委托至当前 holder。"""

    def __getattr__(self, name: str):
        return getattr(get_shared_context_repository(), name)


context_repo = LazyContextRepository()

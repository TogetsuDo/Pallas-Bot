from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ServiceProbeResult:
    category: str
    site: str
    ok: bool
    latency_ms: int | None
    status_code: int | None
    error: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

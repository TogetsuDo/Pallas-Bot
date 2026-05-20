from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .types import ServiceProbeResult


def format_probe_line(result: ServiceProbeResult) -> str:
    prefix = f"{result.category}：{result.site}"
    if result.ok and result.latency_ms is not None:
        return f"{prefix}：{result.latency_ms}ms"
    if result.status_code is not None:
        return f"{prefix}：HTTP {result.status_code}"
    if result.error:
        return f"{prefix}：{result.error}"
    return f"{prefix}：不可用"


def format_probe_lines(results: list[ServiceProbeResult]) -> list[str]:
    return [format_probe_line(r) for r in results]


def format_probe_text(results: list[ServiceProbeResult]) -> str:
    if not results:
        return "未配置可探测的服务端点。"
    return "\n".join(format_probe_lines(results))

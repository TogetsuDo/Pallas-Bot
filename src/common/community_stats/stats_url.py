"""由心跳 endpoint 推导公开 stats URL。"""

from __future__ import annotations

from urllib.parse import urljoin, urlparse

_DEFAULT_STATS = "https://stats.pallasbot.top/v1/stats"


def stats_url_from_endpoint(heartbeat_endpoint: str) -> str:
    ep = (heartbeat_endpoint or "").strip()
    if not ep:
        return _DEFAULT_STATS
    norm = ep.rstrip("/")
    if norm.endswith("/heartbeat"):
        return norm[: -len("/heartbeat")] + "/stats"
    parsed = urlparse(ep)
    if parsed.scheme and parsed.netloc:
        root = f"{parsed.scheme}://{parsed.netloc}"
        return urljoin(root + "/", "v1/stats")
    return _DEFAULT_STATS

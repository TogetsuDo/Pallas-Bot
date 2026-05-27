"""拉取中心 GET /v1/corpus/usage（本部署共享语料用量）。"""

from __future__ import annotations

from typing import Any

import httpx
from nonebot import logger

from src.features.corpus.config import (
    community_configured,
    resolved_community_api_base_urls,
    resolved_community_token,
)
from src.features.corpus.store import corpus_community_enrollment_valid
from src.features.message_scrub.quiet_http_loggers import scrub_http_log_noise

_HTTP_TIMEOUT_SEC = 10.0


async def fetch_corpus_community_usage() -> dict[str, Any] | None:
    if not corpus_community_enrollment_valid() and not community_configured():
        return None
    token = resolved_community_token()
    bases = resolved_community_api_base_urls()
    if not token or not bases:
        return None
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    last_error = ""
    try:
        async with scrub_http_log_noise():
            async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT_SEC) as client:
                for base in bases:
                    usage_url = f"{base.rstrip('/')}/usage"
                    if not usage_url.startswith("http"):
                        continue
                    try:
                        resp = await client.get(usage_url, headers=headers)
                    except httpx.HTTPError as e:
                        last_error = str(e)
                        logger.debug("corpus usage fetch failed api_base={}: {}", base, e)
                        continue
                    if resp.status_code == 401:
                        from src.features.corpus.enroll import maybe_refresh_corpus_enrollment_on_auth_failure

                        await maybe_refresh_corpus_enrollment_on_auth_failure()
                        return None
                    if resp.status_code != 200:
                        last_error = f"HTTP {resp.status_code}"
                        continue
                    data = resp.json()
                    if not isinstance(data, dict):
                        continue
                    return {
                        "read_lookups": int(data.get("read_lookups") or 0),
                        "read_hits": int(data.get("read_hits") or 0),
                        "contribute_ok": int(data.get("contribute_ok") or 0),
                        "updated_at": int(data["updated_at"]) if data.get("updated_at") is not None else None,
                        "source": "community_stats",
                    }
    except httpx.HTTPError as e:
        last_error = str(e)
        logger.debug("corpus usage fetch failed: {}", e)
    if last_error:
        logger.debug("corpus usage: no endpoint succeeded last_error={}", last_error)
    return None

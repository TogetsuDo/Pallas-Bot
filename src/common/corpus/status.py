"""本部署语料多源状态快照（供控制台 /corpus-status）。"""

from __future__ import annotations

import time
from typing import Any

from src.common.corpus.config import (
    auto_enroll_enabled,
    community_configured,
    community_contribute_enabled,
    community_manual_configured,
    corpus_composite_enabled,
    fed_configured,
    get_corpus_config,
    is_community_corpus_wanted,
    resolve_enabled,
    resolved_community_api_base,
    resolved_community_api_base_urls,
)
from src.common.corpus.store import corpus_community_enrollment_valid, load_corpus_community_state


def build_corpus_status_snapshot() -> dict[str, Any]:
    cfg = get_corpus_config()
    community_state = load_corpus_community_state()
    enrolled = corpus_community_enrollment_valid(community_state)
    manual = community_manual_configured()
    community_wanted = is_community_corpus_wanted(cfg)
    fed_on = resolve_enabled(cfg.fed_enabled, configured=fed_configured())
    community_on = community_wanted and (community_configured() or auto_enroll_enabled())
    api_base = resolved_community_api_base() if community_configured() else ""
    api_bases = resolved_community_api_base_urls() if community_configured() else []

    expires_at = community_state.get("expires_at")
    enrolled_at = community_state.get("enrolled_at")
    contribute_policy = community_state.get("contribute")
    if contribute_policy is not None:
        contribute = bool(contribute_policy)
    else:
        contribute = community_contribute_enabled(cfg)

    deployment_id = ""
    heartbeat_endpoint = ""
    community_stats_enabled = False
    try:
        from src.common.community_stats.config import get_community_stats_config
        from src.common.community_stats.store import load_community_stats_state, load_or_create_deployment_id

        cs_cfg = get_community_stats_config()
        community_stats_enabled = bool(cs_cfg.enabled)
        deployment_id = load_or_create_deployment_id()
        heartbeat_endpoint = str(load_community_stats_state().get("heartbeat_endpoint") or "").strip()
    except Exception:
        pass

    token = str(community_state.get("corpus_token") or cfg.community_token or "").strip()

    return {
        "composite_active": corpus_composite_enabled(cfg),
        "merge_order": list(cfg.merge_order),
        "merge_strategy": str(cfg.merge_strategy or "local_first"),
        "on_remote_failure": str(cfg.on_remote_failure or "local_only"),
        "sources": {
            "local": {
                "enabled": True,
                "readable": True,
                "writable": True,
            },
            "fed": {
                "enabled": fed_on,
                "configured": fed_configured(),
                "readable": fed_on,
                "writable": bool(cfg.fed_contribute) and fed_on,
            },
            "community": {
                "enabled": community_on,
                "wanted": community_wanted,
                "configured": community_configured(),
                "enrolled": enrolled,
                "manual": manual,
                "auto_enroll": auto_enroll_enabled(),
                "readable": community_on and bool(api_base) and (enrolled or manual),
                "writable": community_contribute_enabled(cfg) and enrolled,
                "api_base": api_base,
                "api_bases": api_bases,
                "contribute": contribute,
                "token_present": bool(token),
                "enrolled_at": int(enrolled_at) if enrolled_at is not None else None,
                "expires_at": int(expires_at) if expires_at is not None else None,
            },
        },
        "deployment": {
            "deployment_id": deployment_id,
            "community_stats_enabled": community_stats_enabled,
            "heartbeat_endpoint": heartbeat_endpoint,
        },
        "as_of": int(time.time()),
    }

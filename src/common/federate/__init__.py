"""跨 deployment 联邦协调（Phase 2 ingress 去重等）。"""

from .config import (
    clear_federate_config_cache,
    federate_ingress_active,
    federate_redis_available,
    get_federate_config,
    resolved_federate_id,
)
from .dedup import try_claim_cross_federate_message
from .ingress import claim_federate_group_message_ingress

__all__ = [
    "claim_federate_group_message_ingress",
    "clear_federate_config_cache",
    "federate_ingress_active",
    "federate_redis_available",
    "get_federate_config",
    "resolved_federate_id",
    "try_claim_cross_federate_message",
]

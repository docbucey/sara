"""
Shared shunt header validation used by all five SARA pillars.
"""

SHUNT_REQUIRED_FIELDS = [
    "shunt_id", "source_pillar", "target_pillar", "timestamp",
    "intent", "payload", "context_tags", "requires_response",
]


def validate_shunt_header(payload: dict) -> bool:
    """Enforce shunt header contract on inbound/outbound actions."""
    return all(field in payload for field in SHUNT_REQUIRED_FIELDS)

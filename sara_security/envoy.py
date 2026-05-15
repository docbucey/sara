# sara_security/envoy.py
# Extracted from sara_securitygen1.py — VNCE envoy record validation.

try:
    from sara_common.types import SecurityOutcome
except ImportError:
    pass

ENVOY_PROTOCOL_VNCE: str = "vnce"


def _validate_vnce_envoy_record(envoy_record: dict) -> dict:
    """
    SECURITY-only VNCE envoy validator. Ensures correct schema, token, caps, and policy.
    """
    if not isinstance(envoy_record, dict):
        raise ValueError("VNCE envoy record must be a dict")

    if envoy_record.get("type") != "envoy":
        raise ValueError("VNCE envoy record must have type='envoy'")

    if envoy_record.get("protocol") != ENVOY_PROTOCOL_VNCE:
        raise ValueError("VNCE envoy record must have protocol='vnce'")

    host = envoy_record.get("host")
    port = envoy_record.get("port")
    token = envoy_record.get("token")

    if not host or not isinstance(host, str):
        raise ValueError("VNCE envoy host is required")

    if not isinstance(port, int) or port <= 0:
        raise ValueError("VNCE envoy port must be a positive integer")

    if not token or not isinstance(token, str):
        raise ValueError("VNCE envoy token is required")

    caps = envoy_record.get("caps") or []
    if "frame" not in caps or "input" not in caps:
        raise ValueError("VNCE envoy caps must include 'frame' and 'input'")

    policy = envoy_record.get("policy")
    if policy is not None and not isinstance(policy, list):
        raise ValueError("VNCE envoy policy must be a list if provided")

    return envoy_record

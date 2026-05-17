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


def vnce_proximity_handshake_sec(envoy_record: dict, proximity_token: str = "") -> dict:
    """
    VNCE proximity handshake stub.

    Validates a VNCE envoy record and issues a proximity challenge.  Full
    attestation (BLE/WiFi-RTT signal-strength confirmation) is pending
    hardware integration and will replace this stub in a future sprint.

    Returns a result dict with keys:
      handshake        — "stub" until hardware integration ships
      proximity_confirmed — always False at stub level
      reason           — machine-readable outcome code
      host             — the envoy host that was evaluated
      challenge_issued — True when a proximity token was accepted for replay
    """
    if not isinstance(envoy_record, dict):
        return {
            "handshake": "stub",
            "proximity_confirmed": False,
            "reason": "PROXIMITY:invalid-record",
            "host": "",
            "challenge_issued": False,
        }

    try:
        _validate_vnce_envoy_record(envoy_record)
    except ValueError as exc:
        return {
            "handshake": "stub",
            "proximity_confirmed": False,
            "reason": f"PROXIMITY:envoy-record-invalid:{exc}",
            "host": str(envoy_record.get("host", "")),
            "challenge_issued": False,
        }

    host = str(envoy_record.get("host", "")).strip()
    if not host:
        return {
            "handshake": "stub",
            "proximity_confirmed": False,
            "reason": "PROXIMITY:no-host",
            "host": "",
            "challenge_issued": False,
        }

    token_presented = bool(str(proximity_token).strip())
    return {
        "handshake": "stub",
        "proximity_confirmed": False,
        "reason": "PROXIMITY:stub-pending-hardware",
        "host": host,
        "challenge_issued": token_presented,
        "note": (
            "Full proximity attestation requires BLE/WiFi-RTT hardware "
            "integration. This stub validates the envoy record schema and "
            "returns a challenge placeholder only."
        ),
    }

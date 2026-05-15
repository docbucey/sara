# sara_security/trust.py
# Extracted from sara_securitygen1.py — trust policy, environment posture, and utility helpers.

import os
import json
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any

try:
    from sara_common.types import SecurityOutcome
except ImportError:
    pass

SECURITY_OUTCOME_ALLOW = "ALLOW"
SECURITY_OUTCOME_CHALLENGE = "CHALLENGE"
SECURITY_OUTCOME_QUARANTINE = "QUARANTINE"
SECURITY_OUTCOME_LOCKDOWN = "LOCKDOWN"
SECURITY_OUTCOME_ZEROIZE_SAFE = "ZEROIZE_SAFE"

try:
    from .sara_securitygen1 import _SECURITY_KEEP_STATE
except ImportError:
    try:
        from sara_securitygen1 import _SECURITY_KEEP_STATE
    except ImportError:
        _SECURITY_KEEP_STATE: Dict[str, Any] = {
            "vault_state": "sealed",
            "control_lockdown": False,
            "last_outcome": SECURITY_OUTCOME_ALLOW,
            "volatile_cache": {},
            "pending_challenges": [],
            "incident_history": [],
            "posture": {},
            "stables_sessions": {},
            "trust_policy": {},
            "vnce_last_attested": {},
        }

_TRUST_POLICY_PATHS: List[str] = [
    "/etc/sara-lite/trust-policy.json",
    os.path.join(os.path.dirname(__file__), "trust-policy.json"),
]


def _default_trust_policy_sec() -> Dict[str, Any]:
    return {
        "allowed_environments": ["local", "local_only", "trusted_local", "interactive", "night_shift", "lan", "internet_strict"],
        "trusted_hosts": ["localhost", "127.0.0.1", "::1", "local_only"],
        "allow_lan": True,
        "allow_internet_strict": False,
    }


def _load_trust_policy_sec() -> Dict[str, Any]:
    cached = _SECURITY_KEEP_STATE.get("trust_policy")
    if isinstance(cached, dict) and cached:
        return cached

    policy = _default_trust_policy_sec()
    for path in _TRUST_POLICY_PATHS:
        if not os.path.exists(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                policy.update(loaded)
                break
        except Exception:
            continue

    _SECURITY_KEEP_STATE["trust_policy"] = policy
    return policy


def _iso_now_sec() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_safe_sec(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(k): _json_safe_sec(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe_sec(v) for v in value]
    return str(value)


def scout_house_posture_sec(context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Evaluate the current environment trust posture without changing user data."""
    details = dict(context or {})
    environment = str(details.get("environment") or "local_only").strip().lower() or "local_only"
    host = str(details.get("host") or details.get("envoy_host") or "localhost").strip().lower() or "localhost"
    session_id = str(details.get("session_id") or details.get("request_id") or "").strip()
    policy = _load_trust_policy_sec()
    allowed_env = {str(v).strip().lower() for v in (policy.get("allowed_environments") or [])}
    trusted_hosts = {str(v).strip().lower() for v in (policy.get("trusted_hosts") or [])}
    trusted_host = host in trusted_hosts
    trusted_environment = environment in allowed_env
    if environment == "lan" and not bool(policy.get("allow_lan", True)):
        trusted_environment = False
    if environment == "internet_strict" and not bool(policy.get("allow_internet_strict", False)):
        trusted_environment = False
    trusted = bool(trusted_host and trusted_environment)
    posture = {
        "trusted": trusted,
        "environment": environment,
        "host": host,
        "session_id": session_id,
        "authority_layer": "SCOUT_HOUSE",
        "policy_source": "trust-policy",
        "recommended_action": SECURITY_OUTCOME_ALLOW if trusted else SECURITY_OUTCOME_CHALLENGE,
        "evaluated_at": _iso_now_sec(),
    }
    _SECURITY_KEEP_STATE["posture"] = posture
    return posture

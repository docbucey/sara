# sara_security/vault.py
# Extracted from sara_securitygen1.py — vault lifecycle, zeroize, and incident management.

from datetime import datetime, timezone
from typing import Optional, Dict, Any

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

try:
    from .trust import _iso_now_sec, _json_safe_sec
except ImportError:
    try:
        from trust import _iso_now_sec, _json_safe_sec
    except ImportError:
        def _iso_now_sec() -> str:
            return datetime.now(timezone.utc).isoformat()

        def _json_safe_sec(value):
            if value is None or isinstance(value, (str, int, float, bool)):
                return value
            if isinstance(value, dict):
                return {str(k): _json_safe_sec(v) for k, v in value.items()}
            if isinstance(value, list):
                return [_json_safe_sec(v) for v in value]
            return str(value)

try:
    from .sheriff import sheriff_audit
except ImportError:
    try:
        from sheriff import sheriff_audit
    except ImportError:
        def sheriff_audit(event_type, actor, decision, reason, details=None, **extra):
            return {"ts": _iso_now_sec(), "event_type": event_type, "actor": actor, "decision": decision, "reason": reason}


def safe_zeroize_sec(reason: str = "", scope: str = "volatile") -> Dict[str, Any]:
    """Safe zeroize clears volatile in-memory state only. It never deletes files, NBS, profiles, or envelopes."""
    volatile_cache = _SECURITY_KEEP_STATE.get("volatile_cache")
    if not isinstance(volatile_cache, dict):
        volatile_cache = {}
    cleared_keys = sorted(list(volatile_cache.keys()))
    _SECURITY_KEEP_STATE["volatile_cache"] = {}
    _SECURITY_KEEP_STATE["pending_challenges"] = []
    _SECURITY_KEEP_STATE["last_outcome"] = SECURITY_OUTCOME_ZEROIZE_SAFE
    result = {
        "ok": True,
        "action": SECURITY_OUTCOME_ZEROIZE_SAFE,
        "scope": str(scope or "volatile"),
        "cleared_keys": cleared_keys,
        "cleared_count": len(cleared_keys),
        "files_deleted": 0,
        "nbs_deleted": 0,
        "profiles_deleted": 0,
        "reason": str(reason or "volatile-state-cleared"),
        "timestamp": _iso_now_sec(),
    }
    _SECURITY_KEEP_STATE["last_zeroize"] = result
    return result


def security_vault_lifecycle_sec(action: str = "seal", reason: str = "", incident_id: str = "") -> Dict[str, Any]:
    """Safe Gen1 vault lifecycle: seal, unseal, evict (volatile only), and recover."""
    requested_action = str(action or "seal").strip().lower() or "seal"
    before_state = str(_SECURITY_KEEP_STATE.get("vault_state", "sealed"))
    zeroize_result = None

    if requested_action == "seal":
        after_state = "sealed"
    elif requested_action == "unseal":
        after_state = "unsealed"
    elif requested_action == "evict":
        after_state = "evicted"
        zeroize_result = safe_zeroize_sec(reason=reason or "vault-evict", scope="volatile")
    elif requested_action == "recover":
        after_state = "recovered"
        _SECURITY_KEEP_STATE["control_lockdown"] = False
    else:
        return {
            "ok": False,
            "reason": f"unsupported_vault_action:{requested_action}",
            "vault_state": before_state,
        }

    _SECURITY_KEEP_STATE["vault_state"] = after_state
    result = {
        "ok": True,
        "action": requested_action,
        "vault_state_before": before_state,
        "vault_state_after": after_state,
        "reason": str(reason or f"vault:{requested_action}"),
        "incident_id": str(incident_id or ""),
        "timestamp": _iso_now_sec(),
    }
    if zeroize_result is not None:
        result["zeroize"] = zeroize_result
    return result


def security_incident_lifecycle_sec(
    event_type: str = "security.incident",
    actor: str = "security",
    severity: str = "medium",
    reason: str = "",
    outcome: str = SECURITY_OUTCOME_ALLOW,
    envelope: Optional[Dict[str, Any]] = None,
    recommended_action: str = "monitor",
) -> Dict[str, Any]:
    """Record a full non-destructive incident lifecycle for audit, quarantine, lockdown, and recovery flows."""
    final_outcome = str(outcome or SECURITY_OUTCOME_ALLOW).upper()
    incident_id = f"incident-{int(datetime.now(timezone.utc).timestamp() * 1000)}"
    stages = ["DETECT", "AUDIT"]
    if final_outcome == SECURITY_OUTCOME_QUARANTINE:
        stages.append("QUARANTINE")
    elif final_outcome == SECURITY_OUTCOME_LOCKDOWN:
        stages.append("LOCKDOWN")
        _SECURITY_KEEP_STATE["control_lockdown"] = True
    elif final_outcome == SECURITY_OUTCOME_ZEROIZE_SAFE:
        stages.append("ZEROIZE_SAFE")
    else:
        stages.append("RECOVER")

    incident = {
        "incident_id": incident_id,
        "timestamp": _iso_now_sec(),
        "event_type": event_type,
        "actor": actor,
        "severity": str(severity or "medium").lower(),
        "reason": str(reason or final_outcome),
        "recommended_action": str(recommended_action or "monitor"),
        "final_disposition": final_outcome,
        "stages": stages,
        "envelope": _json_safe_sec(envelope or {}),
    }
    history = _SECURITY_KEEP_STATE.setdefault("incident_history", [])
    history.append(incident)
    if len(history) > 200:
        del history[:-200]

    sheriff_audit(event_type, actor, final_outcome, incident["reason"], details=incident)
    return incident

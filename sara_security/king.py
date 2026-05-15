# sara_security/king.py
# Extracted from sara_securitygen1.py — sovereignty check and evaluation.

from datetime import datetime, timezone
from typing import Optional, Dict, Any

try:
    from sara_common.types import SecurityOutcome
except ImportError:
    pass

ROYAL_SIGNET = "USER_AUTH_CONFIRMED"

SECURITY_OUTCOME_ALLOW = "ALLOW"
SECURITY_OUTCOME_CHALLENGE = "CHALLENGE"
SECURITY_OUTCOME_QUARANTINE = "QUARANTINE"
SECURITY_OUTCOME_LOCKDOWN = "LOCKDOWN"

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
    from .trust import scout_house_posture_sec, _iso_now_sec
except ImportError:
    try:
        from trust import scout_house_posture_sec, _iso_now_sec
    except ImportError:
        def _iso_now_sec():
            return datetime.now(timezone.utc).isoformat()
        def scout_house_posture_sec(context=None):
            return {"trusted": True, "recommended_action": SECURITY_OUTCOME_ALLOW}

try:
    from .stables import stables_validate_session_sec
except ImportError:
    try:
        from stables import stables_validate_session_sec
    except ImportError:
        def stables_validate_session_sec(**kw):
            return {"applied": False, "outcome": SECURITY_OUTCOME_ALLOW}

try:
    from .validation import validate_bucey_shunt_sec, validate_amip_payload_sec
except ImportError:
    try:
        from validation import validate_bucey_shunt_sec, validate_amip_payload_sec
    except ImportError:
        def validate_bucey_shunt_sec(env):
            return {"valid": True, "reason": "BUCEY:stub"}
        def validate_amip_payload_sec(req):
            return {"valid": True, "reason": "AMIP:stub"}

try:
    from .vault import security_incident_lifecycle_sec
except ImportError:
    try:
        from vault import security_incident_lifecycle_sec
    except ImportError:
        def security_incident_lifecycle_sec(**kw):
            return {"incident_id": "stub"}


def king_sovereignty_check(auth_token):
    """Minimal sovereign gate: returns True if auth is valid."""
    return auth_token == ROYAL_SIGNET


def evaluate_sovereignty_sec(
    auth_token: str = "",
    shunt_envelope: Optional[Dict[str, Any]] = None,
    amip_request: Optional[Dict[str, Any]] = None,
    session_id: str = "",
    environment: str = "local_only",
    host: str = "localhost",
    presented_token: str = "",
) -> Dict[str, Any]:
    """Evaluate identity, environment, session, envelope, and additive STABLES state with non-destructive outcomes."""
    envelope = dict(shunt_envelope or {})
    amip_payload = dict(amip_request or envelope.get("amip_payload") or {})
    resolved_session_id = session_id or envelope.get("request_id") or amip_payload.get("correlation_id") or ""
    posture = scout_house_posture_sec({
        "environment": environment,
        "host": host,
        "session_id": resolved_session_id,
    })
    stables = stables_validate_session_sec(
        shunt_envelope=envelope,
        amip_request=amip_payload,
        context={
            "session_id": resolved_session_id,
            "environment": environment,
            "host": host,
            "presented_token": presented_token,
        },
        metadata_only=True,
    )

    checks: Dict[str, Dict[str, Any]] = {
        "identity": {
            "ok": king_sovereignty_check(auth_token),
            "reason": "KING:sovereignty-check-passed" if king_sovereignty_check(auth_token) else "KING:sovereignty-check-failed",
        },
        "environment": {
            "ok": posture.get("trusted", False),
            "reason": "environment-trusted" if posture.get("trusted", False) else "environment-challenge-required",
        },
        "session": {
            "ok": bool(resolved_session_id),
            "reason": "session-present" if resolved_session_id else "session-missing",
        },
        "envelope": {
            "ok": True,
            "reason": "envelope-not-supplied",
        },
        "stables": {
            "ok": not stables.get("applied") or stables.get("outcome") == SECURITY_OUTCOME_ALLOW,
            "reason": stables.get("reason", "STABLES:not-applicable"),
            "hardness_state": stables.get("hardness_state", "NOT_APPLICABLE"),
            "rotation_window_status": stables.get("rotation_window_status", "not_applicable"),
        },
    }

    if envelope:
        envelope_validation = validate_bucey_shunt_sec(envelope)
        checks["envelope"] = {
            "ok": envelope_validation.get("valid", False),
            "reason": envelope_validation.get("reason", "BUCEY:unknown"),
            "errors": envelope_validation.get("errors", []),
        }
    elif amip_payload:
        amip_validation = validate_amip_payload_sec(amip_payload)
        checks["envelope"] = {
            "ok": amip_validation.get("valid", False),
            "reason": amip_validation.get("reason", "AMIP:unknown"),
            "errors": amip_validation.get("errors", []),
        }

    if not checks["identity"]["ok"]:
        outcome = SECURITY_OUTCOME_LOCKDOWN
        recommended_action = "freeze_control_and_reauth"
    elif stables.get("applied") and stables.get("outcome") == SECURITY_OUTCOME_QUARANTINE:
        outcome = SECURITY_OUTCOME_QUARANTINE
        recommended_action = "isolate_session_and_review"
    elif not checks["envelope"]["ok"]:
        outcome = SECURITY_OUTCOME_QUARANTINE
        recommended_action = "isolate_request_or_file"
    elif stables.get("applied") and stables.get("outcome") == SECURITY_OUTCOME_CHALLENGE:
        outcome = SECURITY_OUTCOME_CHALLENGE
        recommended_action = stables.get("recommended_action", "reauth_or_revalidate")
    elif not checks["environment"]["ok"] or not checks["session"]["ok"]:
        outcome = SECURITY_OUTCOME_CHALLENGE
        recommended_action = "reauth_or_revalidate"
    else:
        outcome = SECURITY_OUTCOME_ALLOW
        recommended_action = "proceed"

    _SECURITY_KEEP_STATE["last_outcome"] = outcome
    if outcome == SECURITY_OUTCOME_LOCKDOWN:
        _SECURITY_KEEP_STATE["control_lockdown"] = True
    elif outcome == SECURITY_OUTCOME_ALLOW:
        _SECURITY_KEEP_STATE["control_lockdown"] = False

    return {
        "ok": outcome == SECURITY_OUTCOME_ALLOW,
        "outcome": outcome,
        "recommended_action": recommended_action,
        "checks": checks,
        "posture": posture,
        "stables": stables,
        "vault_state": _SECURITY_KEEP_STATE.get("vault_state", "sealed"),
        "timestamp": _iso_now_sec(),
    }

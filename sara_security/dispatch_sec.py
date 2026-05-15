# sara_security/dispatch_sec.py
# Extracted from sara_securitygen1.py — FSM-based security dispatch and command handlers.
# Named dispatch_sec.py to avoid collision with stdlib dispatch.

import os
import re
import threading as _threading
import importlib.util as _ilu
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any

try:
    from sara_common.types import SecurityOutcome
except ImportError:
    pass

ROYAL_SIGNET = "USER_AUTH_CONFIRMED"

SECURITY_OUTCOME_ALLOW = "ALLOW"
SECURITY_OUTCOME_CHALLENGE = "CHALLENGE"
SECURITY_OUTCOME_QUARANTINE = "QUARANTINE"
SECURITY_OUTCOME_LOCKDOWN = "LOCKDOWN"
SECURITY_OUTCOME_ZEROIZE_SAFE = "ZEROIZE_SAFE"

SECURITY_CMD_SCAN_VNCE_ENVOY: str = "scan_vnce_envoy"
SECURITY_CMD_ATTEST_VNCE_SESSION: str = "attest_vnce_session"
SECURITY_CMD_TRUST_POSTURE: str = "trust_posture"
SECURITY_CMD_EVALUATE_SOVEREIGNTY: str = "evaluate_sovereignty"
SECURITY_CMD_VAULT_LIFECYCLE: str = "vault_lifecycle"
SECURITY_CMD_INCIDENT_LIFECYCLE: str = "incident_lifecycle"
SECURITY_CMD_SAFE_ZEROIZE: str = "safe_zeroize"

STABLES_CMD_INIT_SESSION: str = "stables_init_session"
STABLES_CMD_VALIDATE_SESSION: str = "stables_validate_session"
STABLES_CMD_MARK_SESSION_DROP: str = "stables_mark_session_drop"
STABLES_CMD_RESUME_SESSION: str = "stables_resume_session"
STABLES_CMD_CLOSE_SESSION: str = "stables_close_session"

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
    from .trust import _iso_now_sec, scout_house_posture_sec
except ImportError:
    try:
        from trust import _iso_now_sec, scout_house_posture_sec
    except ImportError:
        def _iso_now_sec():
            return datetime.now(timezone.utc).isoformat()
        def scout_house_posture_sec(context=None):
            return {"trusted": True}

try:
    from .king import king_sovereignty_check, evaluate_sovereignty_sec
except ImportError:
    try:
        from king import king_sovereignty_check, evaluate_sovereignty_sec
    except ImportError:
        def king_sovereignty_check(auth_token):
            return auth_token == ROYAL_SIGNET
        def evaluate_sovereignty_sec(**kw):
            return {"ok": True, "outcome": SECURITY_OUTCOME_ALLOW}

try:
    from .paladin import paladin_gate
except ImportError:
    try:
        from paladin import paladin_gate
    except ImportError:
        def paladin_gate(text):
            return True, "PALADIN:ALLOW:stub"

try:
    from .sheriff import sheriff_audit
except ImportError:
    try:
        from sheriff import sheriff_audit
    except ImportError:
        def sheriff_audit(event_type, actor, decision, reason, details=None, **extra):
            return {"event_type": event_type, "actor": actor, "decision": decision, "reason": reason}

try:
    from .stables import (
        stables_init_session_sec, stables_validate_session_sec,
        stables_mark_session_drop_sec, stables_close_session_sec,
    )
except ImportError:
    try:
        from stables import (
            stables_init_session_sec, stables_validate_session_sec,
            stables_mark_session_drop_sec, stables_close_session_sec,
        )
    except ImportError:
        def stables_init_session_sec(**kw):
            return {"applied": False}
        def stables_validate_session_sec(**kw):
            return {"applied": False}
        def stables_mark_session_drop_sec(**kw):
            return {"applied": False}
        def stables_close_session_sec(**kw):
            return {"applied": False}

try:
    from .validation import (
        validate_amip_payload_sec, validate_bucey_shunt_sec, validate_mail_transport_sec,
    )
except ImportError:
    try:
        from validation import (
            validate_amip_payload_sec, validate_bucey_shunt_sec, validate_mail_transport_sec,
        )
    except ImportError:
        def validate_amip_payload_sec(req):
            return {"valid": True}
        def validate_bucey_shunt_sec(env):
            return {"valid": True}
        def validate_mail_transport_sec(req):
            return {"valid": True}

try:
    from .vault import (
        safe_zeroize_sec, security_vault_lifecycle_sec, security_incident_lifecycle_sec,
    )
except ImportError:
    try:
        from vault import (
            safe_zeroize_sec, security_vault_lifecycle_sec, security_incident_lifecycle_sec,
        )
    except ImportError:
        def safe_zeroize_sec(**kw):
            return {"ok": True}
        def security_vault_lifecycle_sec(**kw):
            return {"ok": True}
        def security_incident_lifecycle_sec(**kw):
            return {"incident_id": "stub"}

try:
    from .platform import _sha256_file, _scan_with_windows_defender, _quarantine_file, _scan_file_policy
except ImportError:
    try:
        from platform import _sha256_file, _scan_with_windows_defender, _quarantine_file, _scan_file_policy
    except ImportError:
        pass

try:
    from .envoy import _validate_vnce_envoy_record
except ImportError:
    try:
        from envoy import _validate_vnce_envoy_record
    except ImportError:
        def _validate_vnce_envoy_record(rec):
            return rec

try:
    from .harness import run_security_harness_check
except ImportError:
    try:
        from harness import run_security_harness_check
    except ImportError:
        def run_security_harness_check(**kw):
            return {"status": "PASS", "reason": "stub"}


def audit_amip_event_sec(event_type: str, amip_request: Optional[Dict[str, Any]] = None, decision: str = "ALLOW", reason: str = "AMIP:event") -> Dict[str, Any]:
    request = dict(amip_request or {})
    route = str(request.get("routing_intent", "unknown"))
    correlation_id = str(request.get("correlation_id", "unknown"))
    audit_reason = f"{reason}|route={route}|correlation_id={correlation_id}"
    return sheriff_audit(event_type, "amip", decision, audit_reason)


# --- Load ShuntFSM from Gen1 core ---
def _load_shunt_fsm():
    _here = os.path.dirname(os.path.abspath(__file__))
    _candidates = [
        ("sara_coregen1_sec", os.path.join(_here, "..", "sara_core", "sara_coregen1.py")),
        ("sara_coregn1_sec", os.path.join(_here, "..", "sara_core", "sara_coregn1.py")),
    ]
    for _module_name, _path in _candidates:
        if not os.path.exists(_path):
            continue
        _spec = _ilu.spec_from_file_location(_module_name, _path)
        if _spec is None or _spec.loader is None:
            continue
        _mod = _ilu.module_from_spec(_spec)
        _spec.loader.exec_module(_mod)
        return _mod.ShuntFSM
    raise FileNotFoundError("Could not locate Gen1 CORE FSM module. Checked sara_coregen1.py and sara_coregn1.py")

ShuntFSM = _load_shunt_fsm()


# --- Command wrappers ---

def _cmd_gate_check(kwargs):
    """Run the full king->paladin->sheriff sequence on an arbitrary request."""
    token = kwargs.get("auth_token", "")
    text = str(kwargs.get("text", ""))
    if not king_sovereignty_check(token):
        event = sheriff_audit("gate_check", "king", "DENY", "KING:sovereignty-check-failed")
        return {"allowed": False, "reason": "KING:sovereignty-check-failed", "audit": event}
    allowed, reason = paladin_gate(text)
    decision = "ALLOW" if allowed else "DENY"
    event = sheriff_audit("gate_check", "sheriff" if allowed else "paladin", decision, reason)
    return {"allowed": allowed, "reason": reason, "audit": event}


def _cmd_trust_posture(kwargs):
    context = kwargs.get("context") or {}
    if not isinstance(context, dict):
        context = {"environment": kwargs.get("environment", "local_only"), "host": kwargs.get("host", "localhost")}
    context.setdefault("environment", kwargs.get("environment", context.get("environment", "local_only")))
    context.setdefault("host", kwargs.get("host", context.get("host", "localhost")))
    context.setdefault("session_id", kwargs.get("session_id", context.get("session_id", "")))
    return scout_house_posture_sec(context)


def _cmd_evaluate_sovereignty(kwargs):
    result = evaluate_sovereignty_sec(
        auth_token=kwargs.get("auth_token", ""),
        shunt_envelope=kwargs.get("shunt_envelope") or kwargs.get("envelope") or {},
        amip_request=kwargs.get("amip_request") or kwargs.get("payload") or {},
        session_id=str(kwargs.get("session_id", "") or ""),
        environment=str(kwargs.get("environment", "local_only") or "local_only"),
        host=str(kwargs.get("host", "localhost") or "localhost"),
    )
    if result.get("outcome") != SECURITY_OUTCOME_ALLOW:
        incident = security_incident_lifecycle_sec(
            event_type="security.sovereignty",
            actor="king",
            severity="high" if result.get("outcome") == SECURITY_OUTCOME_LOCKDOWN else "medium",
            reason=result.get("recommended_action", "review"),
            outcome=result.get("outcome", SECURITY_OUTCOME_CHALLENGE),
            envelope=kwargs.get("shunt_envelope") or kwargs.get("envelope") or kwargs.get("amip_request") or {},
            recommended_action=result.get("recommended_action", "review"),
        )
        result["incident"] = incident
    return result


def _cmd_vault_lifecycle(kwargs):
    return security_vault_lifecycle_sec(
        action=str(kwargs.get("action", "seal") or "seal"),
        reason=str(kwargs.get("reason", "") or ""),
        incident_id=str(kwargs.get("incident_id", "") or ""),
    )


def _cmd_safe_zeroize(kwargs):
    return safe_zeroize_sec(
        reason=str(kwargs.get("reason", "manual-safe-zeroize") or "manual-safe-zeroize"),
        scope=str(kwargs.get("scope", "volatile") or "volatile"),
    )


def _cmd_incident_lifecycle(kwargs):
    return security_incident_lifecycle_sec(
        event_type=str(kwargs.get("event_type", "security.incident") or "security.incident"),
        actor=str(kwargs.get("actor", "security") or "security"),
        severity=str(kwargs.get("severity", "medium") or "medium"),
        reason=str(kwargs.get("reason", "") or ""),
        outcome=str(kwargs.get("outcome", SECURITY_OUTCOME_ALLOW) or SECURITY_OUTCOME_ALLOW),
        envelope=kwargs.get("envelope") or kwargs.get("shunt_envelope") or {},
        recommended_action=str(kwargs.get("recommended_action", "monitor") or "monitor"),
    )

def _cmd_audit_write(kwargs):
    """Write an explicit audit record (for events originating outside normal gate flow)."""
    return sheriff_audit(
        kwargs.get("event_type", "manual"),
        kwargs.get("actor", "system"),
        kwargs.get("decision", "ALLOW"),
        kwargs.get("reason", ""),
    )

def _cmd_paladin_scan(kwargs):
    """Pure signature scan — no sovereignty check, no audit write."""
    allowed, reason = paladin_gate(str(kwargs.get("text", "")))
    return {"allowed": allowed, "reason": reason}


def _cmd_validate_amip(kwargs):
    amip_request = kwargs.get("amip_request") or kwargs.get("payload") or {}
    validation = validate_amip_payload_sec(amip_request)
    audit = audit_amip_event_sec(
        "security.validate_amip",
        amip_request=amip_request,
        decision="ALLOW" if validation.get("valid") else "DENY",
        reason=validation.get("reason", "AMIP:unknown"),
    )
    validation["audit"] = audit
    return validation


def _cmd_validate_bucey_shunt(kwargs):
    shunt_envelope = kwargs.get("shunt_envelope") or kwargs.get("envelope") or {}
    validation = validate_bucey_shunt_sec(shunt_envelope)
    validation["stables"] = stables_validate_session_sec(
        shunt_envelope=shunt_envelope,
        amip_request=shunt_envelope.get("amip_payload") if isinstance(shunt_envelope, dict) else {},
        context={
            "presented_token": kwargs.get("presented_token") or kwargs.get("stables_token") or "",
            "resume_requested": bool(kwargs.get("resume_requested", False)),
        },
        metadata_only=True,
    )

    amip_request = shunt_envelope.get("amip_payload") if isinstance(shunt_envelope, dict) else {}
    audit = audit_amip_event_sec(
        "security.validate_bucey_shunt",
        amip_request=amip_request if isinstance(amip_request, dict) else {},
        decision="ALLOW" if validation.get("valid") else "DENY",
        reason=validation.get("reason", "BUCEY:unknown"),
    )
    validation["audit"] = audit
    return validation


def _cmd_validate_mail_transport(kwargs):
    amip_request = kwargs.get("amip_request") or kwargs.get("payload") or {}
    validation = validate_mail_transport_sec(amip_request)
    audit = audit_amip_event_sec(
        "security.validate_mail_transport",
        amip_request=amip_request if isinstance(amip_request, dict) else {},
        decision="ALLOW" if validation.get("valid") else "DENY",
        reason=validation.get("reason", "MAIL:unknown"),
    )
    validation["audit"] = audit
    return validation


def _cmd_stables_init_session(kwargs):
    result = stables_init_session_sec(
        shunt_envelope=kwargs.get("shunt_envelope") or kwargs.get("envelope") or {},
        amip_request=kwargs.get("amip_request") or kwargs.get("payload") or {},
        context=kwargs.get("context") or kwargs,
    )
    result["audit"] = sheriff_audit("security.stables.init", "sheriff", result.get("outcome", SECURITY_OUTCOME_ALLOW), result.get("reason", "STABLES:init"), details=result)
    return result


def _cmd_stables_validate_session(kwargs):
    result = stables_validate_session_sec(
        shunt_envelope=kwargs.get("shunt_envelope") or kwargs.get("envelope") or {},
        amip_request=kwargs.get("amip_request") or kwargs.get("payload") or {},
        context=kwargs.get("context") or kwargs,
        metadata_only=bool(kwargs.get("metadata_only", False)),
    )
    if result.get("applied"):
        result["audit"] = sheriff_audit("security.stables.validate", "sheriff", result.get("outcome", SECURITY_OUTCOME_ALLOW), result.get("reason", "STABLES:validate"), details=result)
    return result


def _cmd_stables_mark_session_drop(kwargs):
    result = stables_mark_session_drop_sec(
        shunt_envelope=kwargs.get("shunt_envelope") or kwargs.get("envelope") or {},
        amip_request=kwargs.get("amip_request") or kwargs.get("payload") or {},
        context=kwargs.get("context") or kwargs,
    )
    if result.get("applied"):
        result["audit"] = sheriff_audit("security.stables.drop", "sheriff", result.get("outcome", SECURITY_OUTCOME_CHALLENGE), result.get("reason", "STABLES:await-resume"), details=result)
    return result


def _cmd_stables_resume_session(kwargs):
    context = dict(kwargs.get("context") or kwargs)
    context["resume_requested"] = True
    result = stables_validate_session_sec(
        shunt_envelope=kwargs.get("shunt_envelope") or kwargs.get("envelope") or {},
        amip_request=kwargs.get("amip_request") or kwargs.get("payload") or {},
        context=context,
    )
    if result.get("applied"):
        result["audit"] = sheriff_audit("security.stables.resume", "sheriff", result.get("outcome", SECURITY_OUTCOME_CHALLENGE), result.get("reason", "STABLES:resume"), details=result)
    return result


def _cmd_stables_close_session(kwargs):
    result = stables_close_session_sec(
        shunt_envelope=kwargs.get("shunt_envelope") or kwargs.get("envelope") or {},
        amip_request=kwargs.get("amip_request") or kwargs.get("payload") or {},
        context=kwargs.get("context") or kwargs,
    )
    if result.get("applied"):
        result["audit"] = sheriff_audit("security.stables.close", "sheriff", result.get("outcome", SECURITY_OUTCOME_ALLOW), result.get("reason", "STABLES:closed"), details=result)
    return result


def _cmd_scan_file(kwargs):
    """Scan a staged file with policy checks and optional Defender scan."""
    file_path = kwargs.get("file_path", "")
    file_ext = kwargs.get("file_ext", "")
    max_file_bytes = kwargs.get("max_file_bytes", 100 * 1024 * 1024)
    run_defender = bool(kwargs.get("use_windows_defender", True))

    policy = _scan_file_policy(
        file_path=file_path,
        file_ext=file_ext,
        is_envoy=False,
        max_file_bytes=max_file_bytes,
    )
    if not policy.get("allowed"):
        q = _quarantine_file(file_path, policy.get("reason", "SEC:DENY:policy"))
        sheriff_audit("security.scan_file", "sheriff", "DENY", q.get("reason", policy.get("reason", "deny")))
        return {
            "allowed": False,
            "reason": q.get("reason", policy.get("reason", "deny")),
            "quarantine": q,
            "policy": policy,
        }

    defender = {"available": False, "status": "disabled", "detail": "disabled by request"}
    if run_defender:
        defender = _scan_with_windows_defender(file_path)
        if defender.get("available") and defender.get("status") == "threat_found":
            q = _quarantine_file(file_path, "SEC:DENY:defender-threat")
            sheriff_audit("security.scan_file", "sheriff", "DENY", "SEC:DENY:defender-threat")
            return {
                "allowed": False,
                "reason": "SEC:DENY:defender-threat",
                "quarantine": q,
                "policy": policy,
                "defender": defender,
            }

    sheriff_audit("security.scan_file", "sheriff", "ALLOW", "SEC:ALLOW:file-clean")
    return {"allowed": True, "reason": "SEC:ALLOW:file-clean", "policy": policy, "defender": defender}


def _cmd_scan_envoy(kwargs):
    """Envoy intake scan: strict extension policy + optional Defender scan."""
    file_path = kwargs.get("file_path", "")
    file_ext = kwargs.get("file_ext", "")
    max_file_bytes = kwargs.get("max_file_bytes", 100 * 1024 * 1024)
    run_defender = bool(kwargs.get("use_windows_defender", True))

    policy = _scan_file_policy(
        file_path=file_path,
        file_ext=file_ext,
        is_envoy=True,
        max_file_bytes=max_file_bytes,
    )
    if not policy.get("allowed"):
        q = _quarantine_file(file_path, policy.get("reason", "SEC:DENY:envoy-policy"))
        sheriff_audit("security.scan_envoy", "sheriff", "DENY", q.get("reason", policy.get("reason", "deny")))
        return {
            "allowed": False,
            "reason": q.get("reason", policy.get("reason", "deny")),
            "quarantine": q,
            "policy": policy,
        }

    defender = {"available": False, "status": "disabled", "detail": "disabled by request"}
    if run_defender:
        defender = _scan_with_windows_defender(file_path)
        if defender.get("available") and defender.get("status") == "threat_found":
            q = _quarantine_file(file_path, "SEC:DENY:envoy-defender-threat")
            sheriff_audit("security.scan_envoy", "sheriff", "DENY", "SEC:DENY:envoy-defender-threat")
            return {
                "allowed": False,
                "reason": "SEC:DENY:envoy-defender-threat",
                "quarantine": q,
                "policy": policy,
                "defender": defender,
            }

    sheriff_audit("security.scan_envoy", "sheriff", "ALLOW", "SEC:ALLOW:envoy-clean")
    return {"allowed": True, "reason": "SEC:ALLOW:envoy-clean", "policy": policy, "defender": defender}


def _cmd_attest_vnce_session(kwargs: dict) -> dict:
    """
    SECURITY-only attestation for VNCE Envoy sessions.
    Performs sovereignty check, VNCE validation, and audit.
    """
    auth_token = kwargs.get("auth_token", "")
    envoy_record = kwargs.get("envoy_record") or {}

    sovereignty = evaluate_sovereignty_sec(
        auth_token=auth_token,
        session_id=str(envoy_record.get("session_id", "") or ""),
        environment=str(envoy_record.get("environment", "local_only") or "local_only"),
        host=str(envoy_record.get("host", "localhost") or "localhost"),
    )
    if sovereignty.get("outcome") == SECURITY_OUTCOME_LOCKDOWN:
        sheriff_audit("vnce_attest_denied", "king", "LOCKDOWN", "invalid_auth_token", details=sovereignty)
        return {"ok": False, "reason": "invalid_auth_token", "sovereignty": sovereignty}

    try:
        _validate_vnce_envoy_record(envoy_record)
    except Exception as exc:
        sheriff_audit("vnce_attest_denied", "sheriff", "DENY", str(exc), details={"envoy_record": envoy_record})
        return {"ok": False, "reason": str(exc), "sovereignty": sovereignty}

    session_id = str(envoy_record.get("session_id") or "")
    host = str(envoy_record.get("host") or "")
    is_resume_or_reconnect = bool(envoy_record.get("resume_requested") or envoy_record.get("reconnect_requested"))
    if is_resume_or_reconnect:
        last = _SECURITY_KEEP_STATE.setdefault("vnce_last_attested", {}).get(session_id)
        if isinstance(last, dict):
            last_host = str(last.get("host") or "")
            if last_host and host and host != last_host:
                sheriff_audit(
                    "vnce_attest_denied",
                    "sheriff",
                    "QUARANTINE",
                    "vnce_resume_reconnect_host_mismatch",
                    details={"session_id": session_id, "previous_host": last_host, "presented_host": host},
                )
                return {"ok": False, "reason": "vnce_resume_reconnect_host_mismatch", "sovereignty": sovereignty}

    if session_id:
        _SECURITY_KEEP_STATE.setdefault("vnce_last_attested", {})[session_id] = {
            "host": host,
            "attested_at": _iso_now_sec(),
        }

    sheriff_audit(
        "vnce_attest_approved",
        "sheriff",
        "ALLOW",
        "vnce-session-approved",
        details={"host": envoy_record.get("host"), "port": envoy_record.get("port")},
    )
    return {"ok": True, "reason": "approved", "sovereignty": sovereignty}

def _cmd_harness_proof(kwargs):
    """Run the full harness proof sequence."""
    return run_security_harness_check(
        auth_token=kwargs.get("auth_token", ROYAL_SIGNET),
        request_text=kwargs.get("request_text", "harness:proof:run"),
    )


# --- FSM instance for security pillar ---
_SECURITY_FSM_LOCK = _threading.Lock()

_SECURITY_FSM = ShuntFSM(
    states=["ready", "blocked"],
    transitions={
        ("ready",   "gate_check"):    ("ready",   _cmd_gate_check),
        ("ready",   "audit_write"):   ("ready",   _cmd_audit_write),
        ("ready",   "paladin_scan"):  ("ready",   _cmd_paladin_scan),
        ("ready",   SECURITY_CMD_TRUST_POSTURE): ("ready", _cmd_trust_posture),
        ("ready",   SECURITY_CMD_EVALUATE_SOVEREIGNTY): ("ready", _cmd_evaluate_sovereignty),
        ("ready",   SECURITY_CMD_VAULT_LIFECYCLE): ("ready", _cmd_vault_lifecycle),
        ("ready",   SECURITY_CMD_INCIDENT_LIFECYCLE): ("ready", _cmd_incident_lifecycle),
        ("ready",   SECURITY_CMD_SAFE_ZEROIZE): ("ready", _cmd_safe_zeroize),
        ("ready",   STABLES_CMD_INIT_SESSION): ("ready", _cmd_stables_init_session),
        ("ready",   STABLES_CMD_VALIDATE_SESSION): ("ready", _cmd_stables_validate_session),
        ("ready",   STABLES_CMD_MARK_SESSION_DROP): ("ready", _cmd_stables_mark_session_drop),
        ("ready",   STABLES_CMD_RESUME_SESSION): ("ready", _cmd_stables_resume_session),
        ("ready",   STABLES_CMD_CLOSE_SESSION): ("ready", _cmd_stables_close_session),
        ("ready",   "scan_file"):     ("ready",   _cmd_scan_file),
        ("ready",   "scan_envoy"):    ("ready",   _cmd_scan_envoy),
        ("ready",   "validate_amip"): ("ready",   _cmd_validate_amip),
        ("ready",   "validate_bucey_shunt"): ("ready", _cmd_validate_bucey_shunt),
        ("ready",   "validate_mail_transport"): ("ready", _cmd_validate_mail_transport),
        ("ready",   SECURITY_CMD_ATTEST_VNCE_SESSION): ("ready", _cmd_attest_vnce_session),
        ("ready",   "harness_proof"): ("ready",   _cmd_harness_proof),
        ("blocked", "reset"):         ("ready",   None),
    },
    initial_state="ready",
)


def dispatch_security(command: str, auth_token: str = "", **kwargs) -> dict:
    """
    Single entry point for all security pillar operations.
    Intended to be called only by Control (not by external callers directly).

    Args:
        command:    control-routed security command name
        auth_token: must equal ROYAL_SIGNET to pass king check
        **kwargs:   command-specific arguments

    Returns:
        dict with at minimum {"success": bool}.
    """
    with _SECURITY_FSM_LOCK:
        lockdown_exempt = {
            "audit_write",
            SECURITY_CMD_TRUST_POSTURE,
            SECURITY_CMD_EVALUATE_SOVEREIGNTY,
            SECURITY_CMD_VAULT_LIFECYCLE,
            SECURITY_CMD_INCIDENT_LIFECYCLE,
            SECURITY_CMD_SAFE_ZEROIZE,
            "harness_proof",
        }
        if _SECURITY_KEEP_STATE.get("control_lockdown") and command not in lockdown_exempt:
            audit_event = sheriff_audit("dispatch_security", "king", "LOCKDOWN", "KING:control-lockdown-active")
            return {
                "success": False,
                "status": SECURITY_OUTCOME_LOCKDOWN,
                "reason": "KING:control-lockdown-active",
                "security_audit": audit_event,
            }

        # Step 1 — sovereignty check
        if not king_sovereignty_check(auth_token):
            _SECURITY_KEEP_STATE["control_lockdown"] = True
            sheriff_audit("dispatch_security", "king", "DENY", "KING:sovereignty-check-failed")
            if _SECURITY_FSM.state == "ready":
                _SECURITY_FSM.state = "blocked"
            return {"success": False, "status": "DENY", "reason": "KING:sovereignty-check-failed"}

        # Step 2 — paladin gate (scan the command + relevant text payload)
        gate_text = " ".join([
            str(command),
            str(kwargs.get("text", "")),
            str(kwargs.get("request_text", "")),
            str(kwargs.get("reason", "")),
            str(kwargs.get("routing_intent", "")),
        ])
        allowed, reason = paladin_gate(gate_text)
        if not allowed:
            sheriff_audit("dispatch_security", "paladin", "DENY", reason)
            if _SECURITY_FSM.state == "ready":
                _SECURITY_FSM.state = "blocked"
            return {"success": False, "status": "DENY", "reason": reason}

        # Step 3 — audit clean path
        audit_event = sheriff_audit("dispatch_security", "sheriff", "ALLOW", reason)

        # Recover from blocked if needed
        if _SECURITY_FSM.state == "blocked":
            _SECURITY_FSM.handle("reset")

        # Step 4 — FSM dispatch
        fsm_kwargs = dict(kwargs)
        fsm_kwargs["auth_token"] = auth_token
        fsm_kwargs["_dispatch_auth_token"] = auth_token
        fsm_result = _SECURITY_FSM.handle(command, fsm_kwargs)
        if not fsm_result.get("success"):
            return {
                "success": False,
                "error": fsm_result.get("error", "unknown FSM error"),
                "security_audit": audit_event,
            }

        result = fsm_result.get("result")
        if isinstance(result, dict) and result.get("outcome") == SECURITY_OUTCOME_LOCKDOWN:
            _SECURITY_KEEP_STATE["control_lockdown"] = True

        return {
            "success": True,
            "command": command,
            "result": result,
            "fsm_state": _SECURITY_FSM.get_state(),
            "security_audit": audit_event,
        }

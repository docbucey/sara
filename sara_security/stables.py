# sara_security/stables.py
# Extracted from sara_securitygen1.py — STABLES session management.

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

ENVOY_PROTOCOL_VNCE: str = "vnce"

STABLES_ROTATION_WINDOW_SECONDS = 300
STABLES_RESUME_WINDOW_SECONDS = 1800
STABLES_ABANDON_TIMEOUT_SECONDS = 7 * 24 * 60 * 60

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
    from .trust import _iso_now_sec
except ImportError:
    try:
        from trust import _iso_now_sec
    except ImportError:
        def _iso_now_sec() -> str:
            return datetime.now(timezone.utc).isoformat()

try:
    from .sheriff import sheriff_audit
except ImportError:
    try:
        from sheriff import sheriff_audit
    except ImportError:
        def sheriff_audit(event_type, actor, decision, reason, details=None, **extra):  # type: ignore[misc]
            return {}


def _stables_now_ts_sec() -> int:
    return int(datetime.now(timezone.utc).timestamp())


def _get_stables_sessions_sec() -> Dict[str, Dict[str, Any]]:
    sessions = _SECURITY_KEEP_STATE.get("stables_sessions")
    if not isinstance(sessions, dict):
        sessions = {}
        _SECURITY_KEEP_STATE["stables_sessions"] = sessions
    return sessions


def _stables_extract_context_sec(
    shunt_envelope: Optional[Dict[str, Any]] = None,
    amip_request: Optional[Dict[str, Any]] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    envelope = dict(shunt_envelope or {})
    request = dict(amip_request or envelope.get("amip_payload") or {})
    context_block = dict(context or {})
    header = envelope.get("header") if isinstance(envelope.get("header"), dict) else {}
    payload = request.get("payload") if isinstance(request.get("payload"), dict) else {}
    machine_profile = request.get("machine_profile") if isinstance(request.get("machine_profile"), dict) else {}
    context_tags = [str(tag).strip().lower() for tag in (envelope.get("context_tags") or []) if tag is not None]
    routing_intent = str(request.get("routing_intent") or envelope.get("intent") or context_block.get("routing_intent") or "").strip().lower()
    workflow_lane = str(
        payload.get("workflow_lane")
        or request.get("workflow_lane")
        or context_block.get("workflow_lane")
        or payload.get("protocol")
        or context_block.get("protocol")
        or ""
    ).strip().lower()
    is_vnce = workflow_lane == "vnce" or "vnce" in routing_intent or payload.get("protocol") == ENVOY_PROTOCOL_VNCE
    is_envoy = bool(payload.get("envoy_mode") or context_block.get("envoy_mode") or any(tag in {"envoy", "vnce"} for tag in context_tags))
    applies = bool(context_block.get("stables_enabled") or payload.get("stables_enabled") or is_vnce or is_envoy)
    session_id = str(
        context_block.get("session_id")
        or payload.get("session_id")
        or envelope.get("request_id")
        or request.get("correlation_id")
        or ""
    ).strip()
    device_identity = str(
        context_block.get("device_identity")
        or context_block.get("device_fingerprint")
        or payload.get("device_identity")
        or payload.get("device_fingerprint")
        or machine_profile.get("profile_id")
        or machine_profile.get("ami_id")
        or envelope.get("ami_id")
        or "local_device"
    ).strip() or "local_device"
    envoy_instance_id = str(
        context_block.get("envoy_instance_id")
        or payload.get("envoy_instance_id")
        or payload.get("envoy_id")
        or header.get("shunt_id")
        or envelope.get("shunt_id")
        or "local_envoy"
    ).strip() or "local_envoy"
    presented_token = str(
        context_block.get("stables_token")
        or context_block.get("presented_token")
        or payload.get("stables_token")
        or payload.get("rotation_token")
        or envelope.get("stables_token")
        or ""
    ).strip()
    hard_enforcement = bool(
        context_block.get("stables_required")
        or payload.get("stables_required")
        or payload.get("rotation_required")
    )
    resume_requested = bool(
        context_block.get("resume_requested")
        or payload.get("resume_requested")
        or payload.get("session_resume")
    )
    session_key = "|".join([session_id or "unknown_session", device_identity, envoy_instance_id])
    return {
        "applies": applies,
        "session_id": session_id,
        "device_identity": device_identity,
        "envoy_instance_id": envoy_instance_id,
        "routing_intent": routing_intent,
        "workflow_lane": workflow_lane or ("vnce" if is_vnce else "control"),
        "presented_token": presented_token,
        "hard_enforcement": hard_enforcement,
        "resume_requested": resume_requested,
        "session_key": session_key,
        "context_tags": context_tags,
    }


def _stables_issue_token_sec(record: Dict[str, Any], presented_token: str = "", now_ts: Optional[int] = None) -> str:
    """Advance STABLES into ACTIVE_ROTATION deterministically without generating or modifying secrets."""
    now_ts = int(now_ts or _stables_now_ts_sec())
    record["current_window"] = now_ts // STABLES_ROTATION_WINDOW_SECONDS
    if str(presented_token or "").strip():
        record["current_token"] = str(presented_token).strip()
    else:
        record["current_token"] = str(record.get("current_token") or "")
    record["state"] = "ACTIVE_ROTATION"
    record["rotation_paused"] = False
    record["last_rotated_at"] = _iso_now_sec()
    record["window_expires_at"] = datetime.fromtimestamp(now_ts + STABLES_ROTATION_WINDOW_SECONDS, timezone.utc).isoformat()
    return str(record.get("current_token") or "")

def _stables_metadata_from_record_sec(record: Dict[str, Any], outcome: str = SECURITY_OUTCOME_ALLOW, reason: str = "STABLES:ok") -> Dict[str, Any]:
    state = str(record.get("state", "CLOSED") or "CLOSED")
    return {
        "applied": True,
        "outcome": outcome,
        "reason": reason,
        "session_id": str(record.get("session_id", "")),
        "device_identity": str(record.get("device_identity", "")),
        "envoy_instance_id": str(record.get("envoy_instance_id", "")),
        "hardness_state": state,
        "rotation_window_status": "paused" if record.get("rotation_paused") else ("inactive" if state == "CLOSED" else "active"),
        "last_verified_at": record.get("last_verified_at"),
        "last_rotated_at": record.get("last_rotated_at"),
        "window_expires_at": record.get("window_expires_at"),
        "resume_window_expires_at": record.get("resume_window_expires_at"),
        "challenge_required": outcome == SECURITY_OUTCOME_CHALLENGE,
        "pending_resume": bool(record.get("pending_resume_token")),
    }

def stables_init_session_sec(
    shunt_envelope: Optional[Dict[str, Any]] = None,
    amip_request: Optional[Dict[str, Any]] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    context_info = _stables_extract_context_sec(shunt_envelope=shunt_envelope, amip_request=amip_request, context=context)
    if not context_info.get("applies"):
        return {
            "applied": False,
            "outcome": SECURITY_OUTCOME_ALLOW,
            "reason": "STABLES:not-applicable",
            "hardness_state": "CLOSED",
            "rotation_window_status": "inactive",
            "challenge_required": False,
        }

    sessions = _get_stables_sessions_sec()
    session_key = context_info["session_key"]
    record = sessions.get(session_key)
    if not isinstance(record, dict):
        record = {
            "session_id": context_info["session_id"],
            "device_identity": context_info["device_identity"],
            "envoy_instance_id": context_info["envoy_instance_id"],
            "created_at": _iso_now_sec(),
            "created_at_epoch": _stables_now_ts_sec(),
            "state": "INIT",
            "rotation_paused": False,
            "current_token": "",
            "pending_resume_token": None,
            "resume_window_expires_at": None,
            "last_verified_at": None,
        }
        sessions[session_key] = record

    for key in ("session_id", "device_identity", "envoy_instance_id"):
        record[key] = context_info.get(key) or record.get(key)
    record["state"] = "INIT"
    _stables_issue_token_sec(record, presented_token=context_info.get("presented_token", ""))
    return _stables_metadata_from_record_sec(record, outcome=SECURITY_OUTCOME_ALLOW, reason="STABLES:init-active")

def stables_mark_session_drop_sec(
    shunt_envelope: Optional[Dict[str, Any]] = None,
    amip_request: Optional[Dict[str, Any]] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    context_info = _stables_extract_context_sec(shunt_envelope=shunt_envelope, amip_request=amip_request, context=context)
    init_result = stables_init_session_sec(shunt_envelope=shunt_envelope, amip_request=amip_request, context=context)
    if not init_result.get("applied"):
        return init_result
    sessions = _get_stables_sessions_sec()
    record = sessions.get(context_info["session_key"], {})
    record["state"] = "AWAIT_RESUME"
    record["rotation_paused"] = True
    record["pending_resume_token"] = context_info.get("presented_token") or record.get("current_token") or ""
    record["resume_window_expires_at"] = datetime.fromtimestamp(_stables_now_ts_sec() + STABLES_RESUME_WINDOW_SECONDS, timezone.utc).isoformat()
    return _stables_metadata_from_record_sec(record, outcome=SECURITY_OUTCOME_CHALLENGE, reason="STABLES:await-resume")

def stables_close_session_sec(
    shunt_envelope: Optional[Dict[str, Any]] = None,
    amip_request: Optional[Dict[str, Any]] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    context_info = _stables_extract_context_sec(shunt_envelope=shunt_envelope, amip_request=amip_request, context=context)
    if not context_info.get("applies"):
        return {
            "applied": False,
            "outcome": SECURITY_OUTCOME_ALLOW,
            "reason": "STABLES:not-applicable",
            "hardness_state": "CLOSED",
            "rotation_window_status": "inactive",
        }
    sessions = _get_stables_sessions_sec()
    record = sessions.get(context_info["session_key"], {
        "session_id": context_info["session_id"],
        "device_identity": context_info["device_identity"],
        "envoy_instance_id": context_info["envoy_instance_id"],
        "created_at": _iso_now_sec(),
    })
    record["state"] = "CLOSED"
    record["rotation_paused"] = True
    record["current_token"] = None
    record["pending_resume_token"] = None
    record["resume_window_expires_at"] = None
    record["closed_at"] = _iso_now_sec()
    sessions.pop(context_info["session_key"], None)
    return _stables_metadata_from_record_sec(record, outcome=SECURITY_OUTCOME_ALLOW, reason="STABLES:closed")


def stables_validate_session_sec(
    shunt_envelope: Optional[Dict[str, Any]] = None,
    amip_request: Optional[Dict[str, Any]] = None,
    context: Optional[Dict[str, Any]] = None,
    metadata_only: bool = False,
) -> Dict[str, Any]:
    context_info = _stables_extract_context_sec(shunt_envelope=shunt_envelope, amip_request=amip_request, context=context)
    if not context_info.get("applies"):
        return {
            "applied": False,
            "outcome": SECURITY_OUTCOME_ALLOW,
            "reason": "STABLES:not-applicable",
            "hardness_state": "CLOSED",
            "rotation_window_status": "inactive",
            "challenge_required": False,
        }

    sessions = _get_stables_sessions_sec()
    session_key = context_info["session_key"]
    record = sessions.get(session_key)
    if not isinstance(record, dict):
        init_result = stables_init_session_sec(shunt_envelope=shunt_envelope, amip_request=amip_request, context=context)
        record = sessions.get(session_key, {})
        if context_info.get("resume_requested"):
            init_result.update({
                "outcome": SECURITY_OUTCOME_CHALLENGE,
                "reason": "STABLES:resume-needs-existing-session",
                "challenge_required": True,
                "recommended_action": "start_new_session",
            })
            return init_result
        return init_result

    now_ts = _stables_now_ts_sec()
    created_epoch = int(record.get("created_at_epoch", now_ts) or now_ts)
    if now_ts - created_epoch >= STABLES_ABANDON_TIMEOUT_SECONDS and record.get("state") in {"AWAIT_RESUME", "EXPIRED"}:
        record["state"] = "ABANDONED"
        record["rotation_paused"] = True
        record["current_token"] = ""
        record["pending_resume_token"] = None
        record["resume_window_expires_at"] = None
        metadata = _stables_metadata_from_record_sec(record, outcome=SECURITY_OUTCOME_CHALLENGE, reason="STABLES:abandoned-human-verification-required")
        metadata["recommended_action"] = "initiate_new_session_after_human_verification"
        return metadata

    if record.get("state") == "INIT":
        _stables_issue_token_sec(record, presented_token=context_info.get("presented_token", ""), now_ts=now_ts)

    presented_token = context_info.get("presented_token", "")
    if record.get("state") == "AWAIT_RESUME":
        resume_expires_at = record.get("resume_window_expires_at")
        if resume_expires_at:
            try:
                resume_expired = datetime.fromisoformat(str(resume_expires_at)) <= datetime.now(timezone.utc)
            except Exception:
                resume_expired = True
        else:
            resume_expired = True

        if resume_expired:
            record["state"] = "EXPIRED"
            metadata = _stables_metadata_from_record_sec(record, outcome=SECURITY_OUTCOME_CHALLENGE, reason="STABLES:resume-window-expired")
            metadata["recommended_action"] = "reauth_or_start_new_session"
            return metadata

        if not context_info.get("resume_requested"):
            metadata = _stables_metadata_from_record_sec(record, outcome=SECURITY_OUTCOME_CHALLENGE, reason="STABLES:await-resume")
            metadata["recommended_action"] = "resume_or_expire"
            return metadata

        pending_token = str(record.get("pending_resume_token") or "")
        if not presented_token or not pending_token:
            metadata = _stables_metadata_from_record_sec(record, outcome=SECURITY_OUTCOME_CHALLENGE, reason="STABLES:pending-resume-token-required")
            metadata["recommended_action"] = "present_pending_resume_token"
            return metadata
        if presented_token != pending_token:
            sheriff_audit(
                "stables.vnce.resume", "stables", "QUARANTINE",
                "STABLES:pending-resume-token-mismatch",
                details={"session_key": session_key, "device_identity": record.get("device_identity"), "envoy_instance_id": record.get("envoy_instance_id")},
            )
            record["state"] = "ABANDONED"
            record["pending_resume_token"] = None
            record["resume_window_expires_at"] = None
            metadata = _stables_metadata_from_record_sec(record, outcome=SECURITY_OUTCOME_QUARANTINE, reason="STABLES:pending-resume-token-mismatch")
            metadata["recommended_action"] = "quarantine_and_review"
            return metadata

        _stables_issue_token_sec(record, presented_token=presented_token, now_ts=now_ts)
        record["pending_resume_token"] = None
        record["resume_window_expires_at"] = None
        record["last_verified_at"] = _iso_now_sec()
        metadata = _stables_metadata_from_record_sec(record, outcome=SECURITY_OUTCOME_ALLOW, reason="STABLES:resume-approved")
        metadata["rotation_window_status"] = "active"
        return metadata

    if record.get("state") == "EXPIRED":
        metadata = _stables_metadata_from_record_sec(record, outcome=SECURITY_OUTCOME_CHALLENGE, reason="STABLES:expired")
        metadata["recommended_action"] = "start_new_session"
        return metadata

    if record.get("state") == "ABANDONED":
        metadata = _stables_metadata_from_record_sec(record, outcome=SECURITY_OUTCOME_CHALLENGE, reason="STABLES:abandoned-human-verification-required")
        metadata["recommended_action"] = "initiate_new_session_after_human_verification"
        return metadata

    if record.get("state") == "CLOSED":
        return _stables_metadata_from_record_sec(record, outcome=SECURITY_OUTCOME_ALLOW, reason="STABLES:closed")

    if presented_token:
        current_token = str(record.get("current_token") or "")
        if current_token and presented_token != current_token:
            sheriff_audit(
                "stables.vnce.rotation", "stables", "QUARANTINE",
                "STABLES:rotation-token-mismatch",
                details={"session_key": session_key, "device_identity": record.get("device_identity"), "envoy_instance_id": record.get("envoy_instance_id")},
            )
            record["state"] = "ABANDONED"
            record["current_token"] = ""
            record["pending_resume_token"] = None
            metadata = _stables_metadata_from_record_sec(record, outcome=SECURITY_OUTCOME_QUARANTINE, reason="STABLES:rotation-token-mismatch")
            metadata["recommended_action"] = "quarantine_and_review"
            return metadata
        _stables_issue_token_sec(record, presented_token=presented_token, now_ts=now_ts)
        record["last_verified_at"] = _iso_now_sec()
        return _stables_metadata_from_record_sec(record, outcome=SECURITY_OUTCOME_ALLOW, reason="STABLES:active")

    metadata = _stables_metadata_from_record_sec(record, outcome=SECURITY_OUTCOME_ALLOW, reason="STABLES:metadata-only")
    metadata["metadata_only"] = bool(metadata_only)
    return metadata

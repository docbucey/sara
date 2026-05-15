"""
SARA Control — VNCE lifecycle, session start/resume, and STABLES security notification.
Extracted from sara_controlgen1.py.
"""
from datetime import datetime, timezone
from typing import Any, Dict, Optional

try:
    from sara_control.loader_con import _load_core_module, _load_gen1_security
    _core = _load_core_module()
    if _core is None:
        raise ImportError("Core module file not found")
    SYSTEM_CORE_PROJECT_NAME = _core.SYSTEM_CORE_PROJECT_NAME
except Exception:
    SYSTEM_CORE_PROJECT_NAME = "sara_core_project"

try:
    _sec = _load_gen1_security()
    dispatch_security = _sec.dispatch_security
except Exception:
    def dispatch_security(command, auth_token="", **kwargs):
        return {
            "success": True,
            "command": command,
            "result": {"allowed": True, "valid": True, "reason": "SEC:FALLBACK:ALLOW"},
        }


def _iso_now_con() -> str:
    return datetime.now(timezone.utc).isoformat()


def _notify_stables_security_con(action: str, session_payload: Optional[Dict[str, Any]] = None, auth_token: str = "") -> Dict[str, Any]:
    """Ask SECURITY/STABLES for deterministic, non-secret VNCE hardening metadata while CONTROL retains workflow ownership."""
    payload = dict(session_payload or {})
    if not auth_token:
        return {
            "applied": False,
            "reason": "STABLES:auth-token-missing",
            "hardness_state": "CLOSED",
            "rotation_window_status": "inactive",
        }

    session_id = str(payload.get("session_id") or payload.get("checkpoint_id") or f"vnce-{int(datetime.now(timezone.utc).timestamp())}")
    machine_profile = payload.get("machine_profile") if isinstance(payload.get("machine_profile"), dict) else {}
    context = {
        "session_id": session_id,
        "environment": payload.get("environment") or payload.get("environment_link") or "local_only",
        "host": payload.get("host") or payload.get("envoy_host") or "localhost",
        "envoy_instance_id": payload.get("envoy_instance_id") or payload.get("envoy_id") or payload.get("envoy_host") or "local_envoy",
        "device_identity": payload.get("device_identity") or payload.get("device_fingerprint") or machine_profile.get("profile_id") or "local_device",
        "workflow_lane": "vnce",
        "stables_enabled": True,
        "presented_token": payload.get("stables_token") or payload.get("rotation_token") or "",
        "resume_requested": bool(payload.get("resume_requested", False)),
    }

    action_map = {
        "start": "stables_init_session",
        "resume": "stables_resume_session",
        "drop": "stables_mark_session_drop",
        "close": "stables_close_session",
        "validate": "stables_validate_session",
    }
    command = action_map.get(str(action or "start").strip().lower(), "stables_validate_session")
    sec_result = dispatch_security(command, auth_token=auth_token, context=context, amip_request={"payload": payload, "routing_intent": "session.resume" if context["resume_requested"] else "session.start"})
    if not sec_result.get("success"):
        return {
            "applied": False,
            "reason": sec_result.get("reason") or sec_result.get("error", "STABLES:dispatch-failed"),
            "hardness_state": "CLOSED",
            "rotation_window_status": "inactive",
        }
    return dict(sec_result.get("result") or {})


def vnce_lifecycle_con(session_payload: Optional[Dict[str, Any]] = None, con_project: str = SYSTEM_CORE_PROJECT_NAME) -> Dict[str, Any]:
    """Build the canonical CONTROL-owned VNCE lifecycle and request additive STABLES metadata when auth is available."""
    from sara_control.routing_con import _build_control_work_state_con

    raw_payload = dict(session_payload or {})
    session_id = str(raw_payload.get("session_id") or raw_payload.get("checkpoint_id") or f"vnce-{int(datetime.now(timezone.utc).timestamp())}")
    action = "resume" if bool(raw_payload.get("resume_requested", False)) else "start"
    security_hardening = _notify_stables_security_con(action, raw_payload, auth_token=str(raw_payload.get("auth_token") or ""))
    return {
        "workflow_lane": "vnce",
        "project": con_project,
        "session_id": session_id,
        "environment_link": raw_payload.get("environment") or raw_payload.get("environment_link") or "local_only",
        "start": {"status": "ready", "owner": "CONTROL", "security_notice": "STABLES metadata only"},
        "resume": {"status": "ready", "owner": "CONTROL", "pending_resume_validation": "SECURITY/STABLES"},
        "checkpoint": {"status": "ready", "owner": "CONTROL"},
        "close": {"status": "ready", "owner": "CONTROL"},
        "security_hardening": security_hardening,
        "work_state": _build_control_work_state_con(
            stage="vnce_resume_ready" if action == "resume" else "vnce_lifecycle_ready",
            workflow_lane="vnce",
            additional={"stables_state": security_hardening.get("hardness_state", "CLOSED")},
        ),
    }


def start_vnce_session_con(session_payload: Optional[Dict[str, Any]] = None, con_project: str = SYSTEM_CORE_PROJECT_NAME, con_auth_token: str = "") -> Dict[str, Any]:
    payload = dict(session_payload or {})
    if con_auth_token:
        payload["auth_token"] = con_auth_token
    payload["resume_requested"] = False
    return vnce_lifecycle_con(payload, con_project=con_project)


def resume_vnce_session_con(session_payload: Optional[Dict[str, Any]] = None, con_project: str = SYSTEM_CORE_PROJECT_NAME, con_auth_token: str = "") -> Dict[str, Any]:
    payload = dict(session_payload or {})
    if con_auth_token:
        payload["auth_token"] = con_auth_token
    payload["resume_requested"] = True
    return vnce_lifecycle_con(payload, con_project=con_project)

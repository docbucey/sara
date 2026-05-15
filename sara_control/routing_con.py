"""
SARA Control — Routing: route_io_con, route_bucey_shunt_con, workflow lane inference,
operator flow builders, wfh/abbucey protocols, and mail transport.
Extracted from sara_controlgen1.py.
"""
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

try:
    from sara_control.loader_con import _load_core_module, _load_gen1_security
    _core = _load_core_module()
    if _core is None:
        raise ImportError("Core module file not found")
    NBS_BASE_DIR = _core.NBS_BASE_DIR
    SYSTEM_CORE_PROJECT_NAME = _core.SYSTEM_CORE_PROJECT_NAME
    _to_proto_lingua = _core._to_proto_lingua
    validate_resonance = _core.validate_resonance
except Exception:
    _core = None
    NBS_BASE_DIR = os.path.join(os.path.expanduser("~"), "sara_nbs")
    SYSTEM_CORE_PROJECT_NAME = "sara_core_project"
    def _to_proto_lingua(obj, **kwargs): return obj
    def validate_resonance(obj): return True, "OK"

try:
    _sec = _load_gen1_security()
    king_sovereignty_check = _sec.king_sovereignty_check
    paladin_gate = _sec.paladin_gate
    sheriff_audit = _sec.sheriff_audit
    dispatch_security = _sec.dispatch_security
except Exception:
    def king_sovereignty_check(token): return True
    def paladin_gate(text): return True, "PALADIN:ALLOW:shunt-fallback"
    def sheriff_audit(event_type, actor, decision, reason):
        return {"ts": None, "event_type": event_type, "actor": actor, "decision": decision, "reason": reason}
    def dispatch_security(command, auth_token="", **kwargs):
        return {
            "success": True,
            "command": command,
            "result": {"allowed": True, "valid": True, "reason": "SEC:FALLBACK:ALLOW"},
            "security_audit": sheriff_audit("dispatch_security", "fallback", "ALLOW", "SEC:FALLBACK:ALLOW"),
        }


def _iso_now_con() -> str:
    return datetime.now(timezone.utc).isoformat()


def _pick_proto_field_con(con_payload: Optional[Dict[str, Any]], key: str, default: Any = None) -> Any:
    """Read plain or Proto-Lingua-suffixed keys without losing CONTROL routing fields."""
    if not isinstance(con_payload, dict):
        return default
    for candidate in (key, f"{key}_puppy", f"{key}_breed", f"{key}_dog_array"):
        if candidate in con_payload:
            return con_payload.get(candidate)
    return default


def _build_control_work_state_con(
    stage: str = "intake",
    status: str = "ready",
    workflow_lane: str = "control",
    additional: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    state = {
        "status": str(status or "ready"),
        "stage": str(stage or "intake"),
        "owner_pillar": "CONTROL",
        "workflow_lane": str(workflow_lane or "control"),
        "last_transition_at": _iso_now_con(),
        "activation_state": "held",
        "deterministic": True,
    }
    if isinstance(additional, dict):
        state.update({k: v for k, v in additional.items() if v is not None})
    return state


def _infer_workflow_lane_con(con_payload: Optional[Dict[str, Any]]) -> str:
    if not isinstance(con_payload, dict):
        return "control"
    lane_hint = str(
        _pick_proto_field_con(con_payload, "workflow", "")
        or _pick_proto_field_con(con_payload, "workflow_lane", "")
        or _pick_proto_field_con(con_payload, "operating_mode", "")
        or ""
    ).strip().lower()
    routing_intent = str(
        _pick_proto_field_con(con_payload, "routing_intent", "")
        or _pick_proto_field_con(con_payload, "intent", "")
        or ""
    ).strip().lower()
    text_hint = " ".join([
        lane_hint,
        routing_intent,
        str(_pick_proto_field_con(con_payload, "goal", "") or ""),
        str(_pick_proto_field_con(con_payload, "input", "") or ""),
    ]).lower()
    if "abbucey" in text_hint or "spec_sheet" in text_hint:
        return "abbucey"
    if "vnce" in text_hint or "session" in routing_intent:
        return "vnce"
    if lane_hint in {"wfh", "work_for_hire"} or any(token in text_hint for token in ["job", "deliverable", "client"]):
        return "wfh"
    return "control"


def wfh_protocol_con(work_item: Optional[Dict[str, Any]] = None, con_project: str = SYSTEM_CORE_PROJECT_NAME) -> Dict[str, Any]:
    """Build the canonical CONTROL-owned WFH pipeline without activating it."""
    from sara_control.session_con import array_normalize_con

    raw_item = dict(work_item or {})
    summary = str(raw_item.get("summary") or raw_item.get("goal") or raw_item.get("input") or "wfh_job").strip()
    client_name = str(raw_item.get("client_name") or raw_item.get("client") or "unassigned_client").strip() or "unassigned_client"
    task_tree = array_normalize_con(raw_item.get("tasks") or raw_item.get("task_tree") or [])
    if not task_tree:
        task_tree = [
            {"step": 1, "label": "intake", "status": "ready"},
            {"step": 2, "label": "breakdown", "status": "ready"},
            {"step": 3, "label": "deliverable_generation", "status": "ready"},
            {"step": 4, "label": "closeout", "status": "ready"},
        ]
    return {
        "workflow_lane": "wfh",
        "project": con_project,
        "job_summary": summary,
        "client_name": client_name,
        "job_intake": {
            "status": "ready",
            "single_entry_point": "route_io_con",
            "difficulty": raw_item.get("difficulty", "unscored"),
        },
        "job_breakdown": {
            "status": "ready",
            "task_tree": task_tree,
            "spec_sheet_ready": bool(raw_item.get("spec_sheet") or raw_item.get("specification")),
        },
        "deliverable_generation": {
            "status": "ready",
            "accuracy_tracking": {
                "status": "ready",
                "score": raw_item.get("accuracy_score", "pending"),
            },
        },
        "closeout": {
            "status": "ready",
            "nbs_write": "planned",
            "activation_state": "held",
        },
        "work_state": _build_control_work_state_con(stage="wfh_pipeline_ready", workflow_lane="wfh"),
    }


def abbucey_protocol_con(job_payload: Optional[Dict[str, Any]] = None, con_project: str = SYSTEM_CORE_PROJECT_NAME) -> Dict[str, Any]:
    """Build the canonical CONTROL-owned ABBucey process scaffold without activation."""
    from sara_control.jobs_con import refinement_loop_executor

    raw_payload = dict(job_payload or {})
    summary = str(raw_payload.get("summary") or raw_payload.get("goal") or raw_payload.get("input") or "abbucey_job").strip()
    refinement = refinement_loop_executor(job_payload=raw_payload)
    return {
        "workflow_lane": "abbucey",
        "project": con_project,
        "job_summary": summary,
        "job_selection": {"status": "ready", "owner": "CONTROL"},
        "spec_sheet_loop": {
            "status": "ready",
            "spec_sheet": raw_payload.get("spec_sheet") or raw_payload.get("specification") or {},
        },
        "accuracy_correction_loop": {
            "status": "ready",
            "accuracy_target": raw_payload.get("accuracy_target", "pending"),
            "refinement": refinement,
        },
        "deliverable_assembly": {"status": "ready", "activation_state": "held"},
        "work_state": _build_control_work_state_con(stage="abbucey_ready", workflow_lane="abbucey"),
    }


def _build_operator_flow_con(workflow_lane: str, con_payload: Optional[Dict[str, Any]], con_project: str) -> Dict[str, Any]:
    from sara_control.vnce_con import vnce_lifecycle_con

    lane = str(workflow_lane or "control").strip().lower()
    if lane == "wfh":
        return wfh_protocol_con(con_payload, con_project=con_project)
    if lane == "vnce":
        return vnce_lifecycle_con(con_payload, con_project=con_project)
    if lane == "abbucey":
        return abbucey_protocol_con(con_payload, con_project=con_project)
    return {
        "workflow_lane": "control",
        "project": con_project,
        "operator_flow": ["intake", "plan", "route", "execute", "update_nbs", "closeout"],
        "work_state": _build_control_work_state_con(stage="route_ready", workflow_lane="control"),
    }


def route_io_con(con_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    CONTROL-first routing surface for all inbound work.
    Keeps workflow ownership in CONTROL, normalizes Proto-Lingua safely,
    and prepares deterministic CORE/SECURITY handoff envelopes without activation.
    """
    from sara_control.session_con import array_normalize_con
    from sara_control.identity_con import identity_resolve_con, ensure_narrative_profile_con

    if not isinstance(con_payload, dict):
        return {"success": False, "error": "con_payload must be a dict"}

    valid, status = validate_resonance(con_payload)
    if not valid:
        return {"success": False, "error": f"Payload exceeds resonance radius: {status}"}

    raw_payload = dict(con_payload)
    auth_token = str(_pick_proto_field_con(raw_payload, "auth_token", "") or "")
    request_text = str(
        _pick_proto_field_con(raw_payload, "input", "")
        or _pick_proto_field_con(raw_payload, "text", "")
        or _pick_proto_field_con(raw_payload, "goal", "")
        or ""
    )
    con_project = str(_pick_proto_field_con(raw_payload, "project", SYSTEM_CORE_PROJECT_NAME) or SYSTEM_CORE_PROJECT_NAME)
    con_goal = str(_pick_proto_field_con(raw_payload, "goal", "") or "")
    routing_intent = str(
        _pick_proto_field_con(raw_payload, "routing_intent", "")
        or _pick_proto_field_con(raw_payload, "intent", "")
        or "local.search"
    ).strip() or "local.search"
    workflow_lane = _infer_workflow_lane_con(raw_payload)
    con_input = array_normalize_con(_pick_proto_field_con(raw_payload, "input", request_text))
    con_outputs = array_normalize_con(
        _pick_proto_field_con(raw_payload, "draft_outputs", [])
        or _pick_proto_field_con(raw_payload, "outputs", [])
        or []
    )

    already_gated = bool(raw_payload.get("_routed_by_fsm"))
    if already_gated:
        sec_reason = "FSM_PREAUTHORIZED"
        sec_event = {"status": "ALLOW", "reason": sec_reason, "source": "dispatch"}
    else:
        if not king_sovereignty_check(auth_token):
            sheriff_audit("route_io", "king", "DENY", "KING:sovereignty-check-failed")
            return {"success": False, "status": "DENY", "reason": "KING:sovereignty-check-failed"}

        sec_allowed, sec_reason = paladin_gate(request_text)
        if not sec_allowed:
            sheriff_audit("route_io", "paladin", "DENY", sec_reason)
            return {"success": False, "status": "DENY", "reason": sec_reason}

        sec_event = sheriff_audit("route_io", "sheriff", "ALLOW", sec_reason)

    proto_payload = _to_proto_lingua(raw_payload)
    identities = identity_resolve_con(con_project)
    narrative_profile = ensure_narrative_profile_con(con_project)
    operator_flow = _build_operator_flow_con(workflow_lane, raw_payload, con_project=con_project)

    con_actions: List[Dict[str, Any]] = [
        {"step": 0, "action": "security_gate", "status": "ALLOW", "reason": sec_reason},
        {
            "step": 1,
            "action": "ensure_identities",
            "status": "done",
            "identity_roles": sorted(list(identities.keys())),
        },
        {
            "step": 2,
            "action": "plan_and_route",
            "status": "done",
            "workflow_lane": workflow_lane,
            "routing_intent": routing_intent,
        },
    ]

    route_result: Dict[str, Any] = {
        "success": True,
        "status": "CONTROL_ROUTE_STAGED",
        "route_class": "CONTROL_LOCAL",
        "routing_intent": routing_intent,
        "note": "CONTROL retained ownership of the request and staged execution locally.",
    }

    shunt_envelope = raw_payload.get("shunt_envelope") if isinstance(raw_payload.get("shunt_envelope"), dict) else None
    amip_payload = raw_payload.get("amip_payload") if isinstance(raw_payload.get("amip_payload"), dict) else None

    if amip_payload is None and hasattr(_core, "build_amip_payload_core"):
        amip_payload = _core.build_amip_payload_core(
            routing_intent=routing_intent,
            payload=dict(_pick_proto_field_con(raw_payload, "payload", {}) or {"input": request_text, "goal": con_goal, "workflow_lane": workflow_lane}),
            mode=str(_pick_proto_field_con(raw_payload, "mode", "interactive") or "interactive"),
            machine_profile=_pick_proto_field_con(raw_payload, "machine_profile", {}) or _pick_proto_field_con(raw_payload, "profile_ref", {}),
            correlation_id=str(_pick_proto_field_con(raw_payload, "correlation_id", "") or ""),
            resource_budget=_pick_proto_field_con(raw_payload, "resource_budget", {}) or {},
        )

    if shunt_envelope is None and isinstance(amip_payload, dict) and hasattr(_core, "build_bucey_shunt_envelope_core"):
        shunt_envelope = _core.build_bucey_shunt_envelope_core(
            amip_payload=amip_payload,
            ami_id=str(_pick_proto_field_con(raw_payload, "ami_id", "") or ""),
            profile_ref=_pick_proto_field_con(raw_payload, "profile_ref", {}) or _pick_proto_field_con(raw_payload, "machine_profile", {}),
            correlation_id=str(_pick_proto_field_con(raw_payload, "correlation_id", "") or ""),
            request_id=str(_pick_proto_field_con(raw_payload, "request_id", "") or ""),
        )

    if isinstance(shunt_envelope, dict) and shunt_envelope:
        route_result = route_bucey_shunt_con(shunt_envelope, auth_token=auth_token)

    con_actions.append({
        "step": 3,
        "action": "execute_route",
        "status": "done" if route_result.get("success") else "blocked",
        "route_class": route_result.get("route_class") or route_result.get("status", "CONTROL_LOCAL"),
    })
    con_actions.append({
        "step": 4,
        "action": "update_nbs",
        "status": "ready",
        "narrative_profile": narrative_profile.get("reference", {}).get("file_path"),
    })
    con_actions.append({"step": 5, "action": "closeout", "status": "ready", "activation_state": "held"})

    result = {
        "success": bool(route_result.get("success", True)),
        "status": route_result.get("status", "READY"),
        "control_entry": "route_io_con",
        "project": con_project,
        "workflow_lane": workflow_lane,
        "input": con_input,
        "goal": con_goal,
        "outputs": con_outputs,
        "actions": con_actions,
        "identity_links": identities,
        "narrative_profile": narrative_profile.get("reference", {}),
        "workflow_plan": operator_flow,
        "normalized_payload": proto_payload,
        "route_result": route_result,
        "security_audit": route_result.get("security_audit", sec_event),
        "workflow_state": _build_control_work_state_con(
            stage="route_complete" if route_result.get("success", True) else "route_blocked",
            status="ready" if route_result.get("success", True) else "blocked",
            workflow_lane=workflow_lane,
            additional={"routing_intent": routing_intent},
        ),
    }
    if isinstance(amip_payload, dict):
        result["amip_payload"] = amip_payload
    if isinstance(shunt_envelope, dict):
        result["shunt_envelope"] = shunt_envelope
    return result


def route_bucey_shunt_con(shunt_envelope: Dict[str, Any], auth_token: str = "") -> Dict[str, Any]:
    """Validate and route a Bucey Shunt envelope through SECURITY, CONTROL FSM, optional STABLES checks, and AMIPI hooks."""
    from sara_control.amip_con import (
        _normalize_amip_request_con, _control_route_guard_con,
        dispatch_amipi_con, _phase1_pipeline_con, _phase1_outcome_from_status_con,
        AMIP_PROTOCOL_VERSION,
    )

    if not isinstance(shunt_envelope, dict):
        return {
            "success": False,
            "status": "ERROR",
            "error": "shunt_envelope must be a dict",
            "phase1_outcome": "deny",
            "osh_pipeline": _phase1_pipeline_con("OSH-1", "ERROR", "shunt_envelope must be a dict"),
        }

    sec_shunt = dispatch_security(
        "validate_bucey_shunt",
        auth_token=auth_token,
        shunt_envelope=shunt_envelope,
    )
    if not sec_shunt.get("success"):
        status = sec_shunt.get("status", "DENY")
        error = sec_shunt.get("error") or sec_shunt.get("reason", "Bucey Shunt validation failed")
        return {
            "success": False,
            "status": status,
            "error": error,
            "security_audit": sec_shunt.get("security_audit"),
            "phase1_outcome": _phase1_outcome_from_status_con(status, error),
            "osh_pipeline": _phase1_pipeline_con("OSH-1", status, error),
        }
    shunt_validation = sec_shunt.get("result") if isinstance(sec_shunt.get("result"), dict) else {}
    if shunt_validation and not bool(shunt_validation.get("valid", False)):
        err = "SECURITY rejected Bucey Shunt envelope"
        return {
            "success": False,
            "status": "DENY",
            "error": err,
            "security_validation": shunt_validation,
            "security_audit": sec_shunt.get("security_audit"),
            "phase1_outcome": _phase1_outcome_from_status_con("DENY", err),
            "osh_pipeline": _phase1_pipeline_con("OSH-4", "DENY", err),
        }

    normalized = _normalize_amip_request_con(shunt_envelope.get("amip_payload") or {})
    sec_amip = dispatch_security(
        "validate_amip",
        auth_token=auth_token,
        amip_request=normalized,
        shunt_envelope=shunt_envelope,
    )
    if not sec_amip.get("success"):
        status = sec_amip.get("status", "DENY")
        error = sec_amip.get("error") or sec_amip.get("reason", "AMIP validation failed")
        return {
            "success": False,
            "status": status,
            "error": error,
            "security_audit": sec_amip.get("security_audit"),
            "phase1_outcome": _phase1_outcome_from_status_con(status, error),
            "osh_pipeline": _phase1_pipeline_con("OSH-3", status, error),
        }
    amip_validation = sec_amip.get("result") if isinstance(sec_amip.get("result"), dict) else {}
    if amip_validation and not bool(amip_validation.get("valid", False)):
        err = "SECURITY rejected AMIP payload"
        return {
            "success": False,
            "status": "DENY",
            "error": err,
            "security_validation": amip_validation,
            "security_audit": sec_amip.get("security_audit"),
            "phase1_outcome": _phase1_outcome_from_status_con("DENY", err),
            "osh_pipeline": _phase1_pipeline_con("OSH-4", "DENY", err),
        }

    route_guard = _control_route_guard_con(shunt_envelope=shunt_envelope, normalized=normalized)
    if not route_guard.get("ok"):
        status = route_guard.get("status", "QUARANTINE")
        reason = route_guard.get("reason", "CONTROL route guard blocked the request")
        return {
            "success": False,
            "status": status,
            "error": reason,
            "security_audit": sec_amip.get("security_audit") or sec_shunt.get("security_audit"),
            "phase1_outcome": _phase1_outcome_from_status_con(status, reason),
            "osh_pipeline": _phase1_pipeline_con("OSH-3", status, reason),
        }

    stables_route = dispatch_security(
        "stables_validate_session",
        auth_token=auth_token,
        shunt_envelope=shunt_envelope,
        amip_request=normalized,
        metadata_only=False,
        presented_token=(normalized.get("payload", {}) or {}).get("stables_token", "") if isinstance(normalized.get("payload", {}), dict) else "",
        resume_requested=bool((normalized.get("payload", {}) or {}).get("resume_requested", False)) if isinstance(normalized.get("payload", {}), dict) else False,
    )
    stables_metadata = dict(stables_route.get("result") or {}) if stables_route.get("success") else {}
    stables_outcome = str(stables_metadata.get("outcome", "ALLOW")).upper()
    if stables_metadata.get("applied") and stables_outcome in {"CHALLENGE", "QUARANTINE", "LOCKDOWN"}:
        reason = stables_metadata.get("reason", "STABLES session hardening blocked the route")
        return {
            "success": False,
            "status": stables_outcome,
            "error": reason,
            "stables": stables_metadata,
            "security_audit": stables_route.get("security_audit") or sec_amip.get("security_audit") or sec_shunt.get("security_audit"),
            "phase1_outcome": _phase1_outcome_from_status_con(stables_outcome, reason),
            "osh_pipeline": _phase1_pipeline_con("OSH-3", stables_outcome, reason),
        }

    routing_intent = str(normalized.get("routing_intent", "local.search")).strip().lower()
    if routing_intent in {"sdk.invoke", "amipi.invoke", "internal_ai.route", "local.ai.route"}:
        route_result = dispatch_amipi_con(normalized, shunt_envelope=shunt_envelope)
        route_class = "AMIPI"
    else:
        route_result = {
            "status": "CONTROL_ROUTE_READY",
            "routing_intent": routing_intent,
            "mode": normalized.get("mode", "interactive"),
            "resource_budget": normalized.get("resource_budget", {}),
            "note": "CONTROL prepared the Bucey Shunt request for local pillar execution.",
        }
        route_class = "CONTROL_LOCAL"

    resolved_status = "READY"
    resolved_error = ""
    if isinstance(route_result, dict) and route_result.get("status"):
        resolved_status = str(route_result.get("status") or "READY")
    pipeline = _phase1_pipeline_con("OSH-5", resolved_status, resolved_error)
    return {
        "success": True,
        "status": "READY",
        "route_class": route_class,
        "ami_id": str(shunt_envelope.get("ami_id") or ""),
        "correlation_id": normalized.get("correlation_id", ""),
        "request_id": str(shunt_envelope.get("request_id") or ""),
        "amip_payload": normalized,
        "result": route_result,
        "stables": stables_metadata,
        "security_audit": stables_route.get("security_audit") if stables_route.get("success") else sec_amip.get("security_audit") or sec_shunt.get("security_audit"),
        "phase1_outcome": pipeline.get("phase1_outcome", "allow"),
        "osh_pipeline": pipeline,
    }


def route_mail_transport_con(
    con_transport_intent: str,
    con_payload: Optional[Dict[str, Any]] = None,
    con_auth_token: str = "",
) -> Dict[str, Any]:
    from sara_control.amip_con import AMIP_PROTOCOL_VERSION

    payload = dict(con_payload or {})
    routing_intent = str(con_transport_intent or "").strip().lower()

    amip_request = {
        "amip_version": AMIP_PROTOCOL_VERSION,
        "mode": "interactive",
        "routing_intent": routing_intent,
        "resource_budget": {"strain": "low", "tokens": 2048, "runtime_ms": 10000},
        "machine_profile": {},
        "correlation_id": str(payload.get("correlation_id", "")),
        "payload": payload,
    }

    sec_res = dispatch_security(
        "validate_mail_transport",
        auth_token=con_auth_token,
        amip_request=amip_request,
        routing_intent=routing_intent,
        text=str(payload.get("text", "")),
    )
    if not sec_res.get("success"):
        return {
            "success": False,
            "status": sec_res.get("status", "DENY"),
            "error": sec_res.get("error") or sec_res.get("reason", "SECURITY mail transport validation failed"),
            "security_audit": sec_res.get("security_audit"),
        }

    validation = sec_res.get("result") if isinstance(sec_res.get("result"), dict) else {}
    if validation and not bool(validation.get("valid", False)):
        return {
            "success": False,
            "status": "DENY",
            "error": validation.get("reason", "SECURITY denied mail transport request"),
            "security_validation": validation,
            "security_audit": sec_res.get("security_audit"),
        }

    core_config = payload.get("core_config") if isinstance(payload.get("core_config"), dict) else {}
    if routing_intent == "mail.smtp.send":
        if not hasattr(_core, "core_smtp_send_email"):
            return {"success": False, "status": "ERROR", "error": "CORE SMTP transport primitive unavailable"}
        email_data = payload.get("email_data") if isinstance(payload.get("email_data"), dict) else {}
        core_result = _core.core_smtp_send_email(
            smtp_host=str(core_config.get("smtp_host", "")).strip(),
            smtp_port=int(core_config.get("smtp_port", 587)),
            username=str(core_config.get("username", "")).strip(),
            password=str(core_config.get("password", "")),
            email_data=email_data,
            use_tls=bool(core_config.get("use_tls", True)),
            use_ssl=bool(core_config.get("use_ssl", False)),
            timeout=int(core_config.get("timeout", 20)),
        )
    elif routing_intent == "mail.imap.fetch":
        if not hasattr(_core, "core_imap_fetch_inbox"):
            return {"success": False, "status": "ERROR", "error": "CORE IMAP transport primitive unavailable"}
        core_result = _core.core_imap_fetch_inbox(
            imap_host=str(core_config.get("imap_host", "")).strip(),
            username=str(core_config.get("username", "")).strip(),
            password=str(core_config.get("password", "")),
            mailbox=str(core_config.get("mailbox", "INBOX")),
            limit=int(core_config.get("limit", 20)),
            use_ssl=bool(core_config.get("use_ssl", True)),
            port=core_config.get("port"),
            criteria=str(core_config.get("criteria", "ALL")),
        )
    else:
        return {"success": False, "status": "DENY", "error": "Unsupported mail transport intent"}

    return {
        "success": True,
        "status": "PASS" if str(core_result.get("status", "")).upper() == "PASS" else "ERROR",
        "routing_intent": routing_intent,
        "security_validation": validation,
        "security_audit": sec_res.get("security_audit"),
        "result": core_result,
    }

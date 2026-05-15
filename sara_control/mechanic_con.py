"""
SARA Control — Mechanic adapter wrappers for calendar, email, sheets, export, voice, model, smoke check.
Extracted from sara_controlgen1.py.

External desktop client (Project Mechanic / MechanicUI); not shipped with SARA — optional hooks when `mechanic_adapter_contract.py` is present in the NBS tree.
"""
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

try:
    from sara_control.loader_con import _load_core_module, _load_gen1_security, _load_mechanic_adapter_contract
    _core = _load_core_module()
    if _core is None:
        raise ImportError("Core module file not found")
    create_nbs_file = _core.create_nbs_file
    SYSTEM_CORE_PROJECT_NAME = _core.SYSTEM_CORE_PROJECT_NAME
except Exception:
    _core = None
    def create_nbs_file(project_name, relative_path, content, meta=None):
        return {"success": False, "error": "Core not loaded"}
    SYSTEM_CORE_PROJECT_NAME = "sara_core_project"

try:
    _sec = _load_gen1_security()
    dispatch_security = _sec.dispatch_security
except Exception:
    def dispatch_security(command, auth_token="", **kwargs):
        return {"success": True, "command": command, "result": {"allowed": True, "valid": True, "reason": "SEC:FALLBACK:ALLOW"}}

from sara_control.session_con import append_event_con, array_normalize_con


def _iso_now_con() -> str:
    return datetime.now(timezone.utc).isoformat()


def _mechanic_run_con(
    con_operation: str,
    con_client_name: str,
    con_payload: Dict[str, Any],
    con_project: str = SYSTEM_CORE_PROJECT_NAME,
    con_auth_token: str = "",
) -> Dict[str, Any]:
    """Vertical-slice integration for Project Mechanic operations."""
    payload = dict(con_payload or {})
    command_name = f"mechanic_{con_operation}"

    sec_probe_text = f"{command_name} client={con_client_name} payload_keys={sorted(list(payload.keys()))}"
    sec_res = dispatch_security("paladin_scan", auth_token=con_auth_token, text=sec_probe_text)
    sec_allowed = bool(sec_res.get("result", {}).get("allowed", False))
    sec_reason = str(sec_res.get("result", {}).get("reason", "SEC:unknown"))
    if not sec_res.get("success") or not sec_allowed:
        return {"success": False, "status": "DENY", "reason": sec_reason, "security": sec_res}

    adapter_mod = _load_mechanic_adapter_contract()
    if adapter_mod is None or not hasattr(adapter_mod, "run_adapter_operation"):
        return {"success": False, "error": "mechanic_adapter_contract unavailable"}

    adapter_result = adapter_mod.run_adapter_operation(provider="project_mechanic", operation=con_operation, payload=payload)

    ts = int(datetime.now(timezone.utc).timestamp())
    rel = os.path.join("artifacts", f"mechanic_{con_operation}_{ts}_gen0_1.0_nbs.json")
    artifact_content = {
        "timestamp": _iso_now_con(),
        "command": command_name,
        "operation": con_operation,
        "client_name": con_client_name,
        "payload": payload,
        "security": {"allowed": sec_allowed, "reason": sec_reason},
        "adapter_result": adapter_result,
    }

    write_res = create_nbs_file(
        project_name=con_project,
        relative_path=rel,
        content=artifact_content,
        meta={"nbs_type": "artifact_wrapper", "project_name": con_project, "tags": ["mechanic", con_operation, "adapter", "vertical_slice"], "source": "control"},
    )
    if not write_res.get("success"):
        return {"success": False, "error": "artifact_write_failed", "adapter_result": adapter_result, "security": sec_res, "write": write_res}

    return {"success": True, "status": "PASS", "security": sec_res, "adapter_result": adapter_result, "artifact": {"relative_path": rel, "reference": write_res.get("reference")}}


def mechanic_calendar_run_con(con_client_name: str, con_payload: Dict[str, Any], con_project: str = SYSTEM_CORE_PROJECT_NAME, con_auth_token: str = "") -> Dict[str, Any]:
    return _mechanic_run_con("calendar_run", con_client_name, con_payload, con_project, con_auth_token)


def mechanic_email_run_con(con_client_name: str, con_payload: Dict[str, Any], con_project: str = SYSTEM_CORE_PROJECT_NAME, con_auth_token: str = "") -> Dict[str, Any]:
    return _mechanic_run_con("email_run", con_client_name, con_payload, con_project, con_auth_token)


def mechanic_sheets_run_con(con_client_name: str, con_payload: Dict[str, Any], con_project: str = SYSTEM_CORE_PROJECT_NAME, con_auth_token: str = "") -> Dict[str, Any]:
    return _mechanic_run_con("sheets_run", con_client_name, con_payload, con_project, con_auth_token)


def mechanic_export_run_con(con_client_name: str, con_payload: Dict[str, Any], con_project: str = SYSTEM_CORE_PROJECT_NAME, con_auth_token: str = "") -> Dict[str, Any]:
    return _mechanic_run_con("export_run", con_client_name, con_payload, con_project, con_auth_token)


def mechanic_voice_run_con(con_client_name: str, con_payload: Dict[str, Any], con_project: str = SYSTEM_CORE_PROJECT_NAME, con_auth_token: str = "") -> Dict[str, Any]:
    return _mechanic_run_con("voice_run", con_client_name, con_payload, con_project, con_auth_token)


def mechanic_model_run_con(con_client_name: str, con_payload: Dict[str, Any], con_project: str = SYSTEM_CORE_PROJECT_NAME, con_auth_token: str = "") -> Dict[str, Any]:
    return _mechanic_run_con("model_run", con_client_name, con_payload, con_project, con_auth_token)


def mechanic_smoke_check_con(
    con_client_name: str,
    con_project: str = SYSTEM_CORE_PROJECT_NAME,
    con_auth_token: str = "",
    con_overrides: Optional[Dict[str, Dict[str, Any]]] = None,
    con_auto_append_narrative: bool = True,
    con_narrative_path: str = "narrative/mechanic_readiness_log_gen0_1.0_nbs.json",
) -> Dict[str, Any]:
    """Run a non-destructive smoke check across all mechanic vertical slices."""
    defaults: Dict[str, Dict[str, Any]] = {
        "calendar_run": {"action": "list", "max_results": 3},
        "email_run": {"to": "", "subject": "", "body": ""},
        "sheets_run": {"action": "list"},
        "export_run": {"kind": "csv"},
        "voice_run": {"action": "status"},
        "model_run": {"action": "status"},
    }
    overrides = dict(con_overrides or {})
    operations = ["calendar_run", "email_run", "sheets_run", "export_run", "voice_run", "model_run"]

    checks: List[Dict[str, Any]] = []
    for op in operations:
        payload = dict(defaults.get(op, {}))
        payload.update(dict(overrides.get(op, {})))
        res = _mechanic_run_con(con_operation=op, con_client_name=con_client_name, con_payload=payload, con_project=con_project, con_auth_token=con_auth_token)
        adapter = res.get("adapter_result", {}) if isinstance(res, dict) else {}
        checks.append({
            "operation": op,
            "command_success": bool(res.get("success", False)) if isinstance(res, dict) else False,
            "adapter_success": bool(adapter.get("success", False)) if isinstance(adapter, dict) else False,
            "error": adapter.get("error") if isinstance(adapter, dict) else res.get("error"),
            "artifact": res.get("artifact") if isinstance(res, dict) else None,
        })

    adapter_pass = sum(1 for c in checks if c.get("adapter_success"))
    overall_status = "PASS" if adapter_pass == len(checks) else "DEGRADED"

    ts = int(datetime.now(timezone.utc).timestamp())
    rel = os.path.join("artifacts", f"mechanic_smoke_check_{ts}_gen0_1.0_nbs.json")
    report_content = {
        "timestamp": _iso_now_con(),
        "command": "mechanic_smoke_check",
        "client_name": con_client_name,
        "overall_status": overall_status,
        "adapter_pass_count": adapter_pass,
        "total_operations": len(checks),
        "checks": checks,
    }

    write_res = create_nbs_file(
        project_name=con_project,
        relative_path=rel,
        content=report_content,
        meta={"nbs_type": "artifact_wrapper", "project_name": con_project, "tags": ["mechanic", "smoke_check", "adapter", "vertical_slice"], "source": "control"},
    )

    narrative_res = None
    if con_auto_append_narrative:
        try:
            narrative_res = append_event_con(
                con_project=con_project,
                con_narrative_path=con_narrative_path,
                con_event={
                    "when": _iso_now_con(),
                    "event_type": "mechanic_smoke_check",
                    "status": overall_status,
                    "client_name": con_client_name,
                    "adapter_pass_count": adapter_pass,
                    "total_operations": len(checks),
                    "report_path": rel,
                },
            )
        except Exception as e:
            narrative_res = {"success": False, "error": f"narrative_append_failed:{type(e).__name__}:{e}"}

    return {
        "success": True,
        "status": overall_status,
        "report": {"relative_path": rel, "reference": write_res.get("reference") if isinstance(write_res, dict) else None},
        "summary": {"adapter_pass_count": adapter_pass, "total_operations": len(checks)},
        "checks": checks,
        "narrative": narrative_res,
    }

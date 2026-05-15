"""OSH (Operational Safety/Health) phase-1 pipeline surface helpers for MAMA."""

from typing import Any, Dict, Optional


def _phase1_outcome_from_result_mama(result: Optional[Dict[str, Any]]) -> str:
    if not isinstance(result, dict):
        return "pending"
    explicit = str(result.get("phase1_outcome") or "").strip().lower()
    if explicit in {"allow", "deny", "constrain", "schema_fail", "boundary_blocked", "pending"}:
        return explicit

    status_u = str(result.get("status") or "").strip().upper()
    error_l = str(result.get("error") or result.get("reason") or "").strip().lower()
    if "schema" in error_l or status_u in {"SCHEMA_FAIL", "SCHEMA-FAIL"}:
        return "schema_fail"
    if status_u in {"DENY", "ERROR", "FAIL"}:
        return "deny"
    if status_u in {"CHALLENGE", "CONSTRAIN", "CONSTRAINED"} or "constrain" in error_l:
        return "constrain"
    if status_u in {"QUARANTINE", "LOCKDOWN", "HOLD"}:
        return "boundary_blocked"
    if status_u in {"ALLOW", "READY", "PASS"}:
        return "allow"
    return "pending"


def _phase1_osh_surface_mama(result: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    base_pipeline = result.get("osh_pipeline") if isinstance(result, dict) and isinstance(result.get("osh_pipeline"), dict) else {}
    stages = base_pipeline.get("stages") if isinstance(base_pipeline.get("stages"), list) else []
    if not stages:
        current = str(base_pipeline.get("current_stage") or "OSH-1")
        stage_codes = ["OSH-1", "OSH-2", "OSH-3", "OSH-4", "OSH-5"]
        labels = {
            "OSH-1": "Intake",
            "OSH-2": "Normalization",
            "OSH-3": "Boundary",
            "OSH-4": "Schema",
            "OSH-5": "Non-Authority",
        }
        if current not in stage_codes:
            current = "OSH-1"
        current_index = stage_codes.index(current)
        for idx, code in enumerate(stage_codes):
            state = "pending"
            if idx < current_index:
                state = "complete"
            elif idx == current_index:
                state = "active"
            stages.append({"code": code, "label": labels.get(code, code), "state": state})
    outcome = _phase1_outcome_from_result_mama(result)
    return {
        "current_stage": str(base_pipeline.get("current_stage") or "OSH-1"),
        "stages": stages,
        "phase1_outcome": outcome,
        "security_outcome_set": ["allow", "deny", "constrain", "schema_fail"],
    }

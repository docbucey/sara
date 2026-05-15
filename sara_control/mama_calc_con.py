"""
SARA Control — MAMA calculator routes: research, traditional, business, real-world Excel, unified.
Extracted from sara_controlgen1.py.
"""
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

try:
    from sara_control.loader_con import _load_core_module, _load_mama_module, _load_gen1_security
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


def _iso_now_con() -> str:
    return datetime.now(timezone.utc).isoformat()


def mama_research_calc_run_con(
    con_formula: str,
    con_samples: int = 500,
    con_project: str = SYSTEM_CORE_PROJECT_NAME,
    con_auth_token: str = "",
) -> Dict[str, Any]:
    """Route Mama research calculator run through control, with security scan and artifact write."""
    sec_probe_text = f"mama_research_calc_run formula={str(con_formula)[:300]}"
    sec_res = dispatch_security("paladin_scan", auth_token=con_auth_token, text=sec_probe_text)
    sec_allowed = bool(sec_res.get("result", {}).get("allowed", False))
    sec_reason = str(sec_res.get("result", {}).get("reason", "SEC:unknown"))
    if not sec_res.get("success") or not sec_allowed:
        return {"success": False, "status": "DENY", "reason": sec_reason, "security": sec_res}

    mama_mod = _load_mama_module()
    if mama_mod is None or not hasattr(mama_mod, "PlainJainMama"):
        return {"success": False, "error": "sara_mamagen1 unavailable"}

    try:
        mama = mama_mod.PlainJainMama()
        run_res = mama.run_research_calc(formula=con_formula, samples=int(con_samples))
    except Exception as e:
        return {"success": False, "error": f"mama_research_calc_exception:{type(e).__name__}:{e}"}

    blocks = run_res.get("blocks", {}) if isinstance(run_res, dict) else {}
    summary_blocks: Dict[str, Any] = {}
    if isinstance(blocks, dict):
        for name, block in blocks.items():
            if isinstance(block, dict):
                summary_blocks[name] = {"falsifiable": bool(block.get("falsifiable", False)), "boundary_count": int(block.get("boundary_count", 0)), "row_count": int(block.get("row_count", 0))}

    artifact_content = {
        "timestamp": _iso_now_con(),
        "command": "mama_research_calc_run",
        "formula": con_formula,
        "samples": int(con_samples),
        "security": {"allowed": sec_allowed, "reason": sec_reason},
        "result": {
            "status": run_res.get("status") if isinstance(run_res, dict) else "ERROR",
            "formula_translated": run_res.get("formula_translated") if isinstance(run_res, dict) else None,
            "vars": run_res.get("vars") if isinstance(run_res, dict) else [],
            "blocks": summary_blocks,
            "error": run_res.get("error") if isinstance(run_res, dict) else "invalid_result",
        },
    }
    ts = int(datetime.now(timezone.utc).timestamp())
    rel = os.path.join("artifacts", f"mama_research_calc_run_{ts}_gen0_1.0_nbs.json")
    write_res = create_nbs_file(project_name=con_project, relative_path=rel, content=artifact_content,
        meta={"nbs_type": "artifact_wrapper", "project_name": con_project, "tags": ["mama", "research_calc", "control_route"], "source": "control"})
    return {
        "success": True,
        "status": run_res.get("status", "UNKNOWN") if isinstance(run_res, dict) else "ERROR",
        "security": sec_res,
        "result": artifact_content["result"],
        "artifact": {"relative_path": rel, "reference": write_res.get("reference") if isinstance(write_res, dict) else None},
    }


def mama_validate_real_world_excel_con(
    con_formula: str, con_excel_path: str, con_observed_col: str,
    con_sheet_name: Optional[str] = None, con_abs_tolerance: float = 0.05, con_rel_tolerance: float = 0.05,
    con_scenario_label: Optional[str] = None, con_units_map: Optional[Dict[str, str]] = None,
    con_report_output_path: Optional[str] = None, con_uncertainty_col: Optional[str] = None,
    con_uncertainty_abs_default: float = 0.0, con_uncertainty_rel_default: float = 0.0,
    con_strict_units: bool = False, con_outlier_policy: str = "none",
    con_baseline_formula: Optional[str] = None, con_verdict_version: str = "v1",
    con_run_id: Optional[str] = None, con_project: str = SYSTEM_CORE_PROJECT_NAME, con_auth_token: str = "",
) -> Dict[str, Any]:
    """Route real-world Excel validation through control, with security scan and artifact write."""
    sec_probe_text = f"mama_validate_real_world_excel file={con_excel_path} observed_col={con_observed_col}"
    sec_res = dispatch_security("paladin_scan", auth_token=con_auth_token, text=sec_probe_text)
    sec_allowed = bool(sec_res.get("result", {}).get("allowed", False))
    sec_reason = str(sec_res.get("result", {}).get("reason", "SEC:unknown"))
    if not sec_res.get("success") or not sec_allowed:
        return {"success": False, "status": "DENY", "reason": sec_reason, "security": sec_res}

    mama_mod = _load_mama_module()
    if mama_mod is None or not hasattr(mama_mod, "PlainJainMama"):
        return {"success": False, "error": "sara_mamagen1 unavailable"}

    try:
        mama = mama_mod.PlainJainMama()
        run_res = mama.validate_real_world_formula_from_excel(
            formula=con_formula, excel_path=con_excel_path, observed_col=con_observed_col,
            sheet_name=con_sheet_name, abs_tolerance=float(con_abs_tolerance), rel_tolerance=float(con_rel_tolerance),
            scenario_label=con_scenario_label, units_map=con_units_map, report_output_path=con_report_output_path,
            uncertainty_col=con_uncertainty_col, uncertainty_abs_default=float(con_uncertainty_abs_default),
            uncertainty_rel_default=float(con_uncertainty_rel_default), strict_units=bool(con_strict_units),
            outlier_policy=con_outlier_policy, baseline_formula=con_baseline_formula,
            verdict_version=con_verdict_version, run_id=con_run_id,
        )
    except Exception as e:
        return {"success": False, "error": f"mama_validate_excel_exception:{type(e).__name__}:{e}"}

    summary = run_res.get("summary", {}) if isinstance(run_res, dict) else {}
    compact_result = {
        "status": run_res.get("status") if isinstance(run_res, dict) else "ERROR",
        "scenario": run_res.get("scenario") if isinstance(run_res, dict) else None,
        "formula_translated": run_res.get("formula_translated") if isinstance(run_res, dict) else None,
        "source": run_res.get("source") if isinstance(run_res, dict) else None,
        "summary": {
            "verdict": summary.get("verdict"), "confirmation_ratio": summary.get("confirmation_ratio"),
            "total_rows": summary.get("total_rows"), "evaluated_rows": summary.get("evaluated_rows"),
            "confirmed_rows": summary.get("confirmed_rows"), "boundary_rows": summary.get("boundary_rows"),
            "missing_input_rows": summary.get("missing_input_rows"),
        },
        "report_export": run_res.get("report_export") if isinstance(run_res, dict) else None,
        "error": run_res.get("error") if isinstance(run_res, dict) else "invalid_result",
    }

    artifact_content = {
        "timestamp": _iso_now_con(), "command": "mama_validate_real_world_excel",
        "formula": con_formula, "excel_path": con_excel_path, "observed_col": con_observed_col,
        "sheet_name": con_sheet_name, "tolerance": {"abs": float(con_abs_tolerance), "rel": float(con_rel_tolerance)},
        "security": {"allowed": sec_allowed, "reason": sec_reason}, "result": compact_result,
    }
    ts = int(datetime.now(timezone.utc).timestamp())
    rel = os.path.join("artifacts", f"mama_validate_real_world_excel_{ts}_gen0_1.0_nbs.json")
    write_res = create_nbs_file(project_name=con_project, relative_path=rel, content=artifact_content,
        meta={"nbs_type": "artifact_wrapper", "project_name": con_project, "tags": ["mama", "research_calc", "real_world", "excel", "control_route"], "source": "control"})
    return {
        "success": True, "status": compact_result.get("status", "UNKNOWN"), "security": sec_res,
        "result": compact_result, "artifact": {"relative_path": rel, "reference": write_res.get("reference") if isinstance(write_res, dict) else None},
    }


def mama_traditional_calc_run_con(
    con_expression: str, con_variables: Optional[Dict[str, Any]] = None,
    con_rows: Optional[List[Dict[str, Any]]] = None, con_project: str = SYSTEM_CORE_PROJECT_NAME, con_auth_token: str = "",
) -> Dict[str, Any]:
    """Route Mama traditional calculator through control with security + artifact write."""
    sec_probe_text = f"mama_traditional_calc_run expr={str(con_expression)[:300]}"
    sec_res = dispatch_security("paladin_scan", auth_token=con_auth_token, text=sec_probe_text)
    sec_allowed = bool(sec_res.get("result", {}).get("allowed", False))
    sec_reason = str(sec_res.get("result", {}).get("reason", "SEC:unknown"))
    if not sec_res.get("success") or not sec_allowed:
        return {"success": False, "status": "DENY", "reason": sec_reason, "security": sec_res}

    mama_mod = _load_mama_module()
    if mama_mod is None or not hasattr(mama_mod, "PlainJainMama"):
        return {"success": False, "error": "sara_mamagen1 unavailable"}

    try:
        mama = mama_mod.PlainJainMama()
        run_res = mama.run_traditional_calc(expression=con_expression, variables=con_variables, rows=con_rows)
    except Exception as e:
        return {"success": False, "error": f"mama_traditional_calc_exception:{type(e).__name__}:{e}"}

    artifact_content = {
        "timestamp": _iso_now_con(), "command": "mama_traditional_calc_run",
        "expression": con_expression, "variables": con_variables or {}, "row_count": len(con_rows or []),
        "security": {"allowed": sec_allowed, "reason": sec_reason}, "result": run_res,
    }
    ts = int(datetime.now(timezone.utc).timestamp())
    rel = os.path.join("artifacts", f"mama_traditional_calc_run_{ts}_gen0_1.0_nbs.json")
    write_res = create_nbs_file(project_name=con_project, relative_path=rel, content=artifact_content,
        meta={"nbs_type": "artifact_wrapper", "project_name": con_project, "tags": ["mama", "traditional_calc", "control_route"], "source": "control"})
    return {
        "success": True, "status": run_res.get("status", "UNKNOWN") if isinstance(run_res, dict) else "ERROR",
        "security": sec_res, "result": run_res,
        "artifact": {"relative_path": rel, "reference": write_res.get("reference") if isinstance(write_res, dict) else None},
    }


def mama_business_calc_run_con(
    con_operation: str, con_inputs: Dict[str, Any],
    con_project: str = SYSTEM_CORE_PROJECT_NAME, con_auth_token: str = "",
) -> Dict[str, Any]:
    """Route Mama business calculator through control with security + artifact write."""
    sec_probe_text = f"mama_business_calc_run op={con_operation}"
    sec_res = dispatch_security("paladin_scan", auth_token=con_auth_token, text=sec_probe_text)
    sec_allowed = bool(sec_res.get("result", {}).get("allowed", False))
    sec_reason = str(sec_res.get("result", {}).get("reason", "SEC:unknown"))
    if not sec_res.get("success") or not sec_allowed:
        return {"success": False, "status": "DENY", "reason": sec_reason, "security": sec_res}

    mama_mod = _load_mama_module()
    if mama_mod is None or not hasattr(mama_mod, "PlainJainMama"):
        return {"success": False, "error": "sara_mamagen1 unavailable"}

    try:
        mama = mama_mod.PlainJainMama()
        run_res = mama.run_business_calc(operation=con_operation, inputs=con_inputs)
    except Exception as e:
        return {"success": False, "error": f"mama_business_calc_exception:{type(e).__name__}:{e}"}

    artifact_content = {
        "timestamp": _iso_now_con(), "command": "mama_business_calc_run",
        "operation": con_operation, "inputs": con_inputs,
        "security": {"allowed": sec_allowed, "reason": sec_reason}, "result": run_res,
    }
    ts = int(datetime.now(timezone.utc).timestamp())
    rel = os.path.join("artifacts", f"mama_business_calc_run_{ts}_gen0_1.0_nbs.json")
    write_res = create_nbs_file(project_name=con_project, relative_path=rel, content=artifact_content,
        meta={"nbs_type": "artifact_wrapper", "project_name": con_project, "tags": ["mama", "business_calc", "control_route"], "source": "control"})
    return {
        "success": True, "status": run_res.get("status", "UNKNOWN") if isinstance(run_res, dict) else "ERROR",
        "security": sec_res, "result": run_res,
        "artifact": {"relative_path": rel, "reference": write_res.get("reference") if isinstance(write_res, dict) else None},
    }


def mama_calc_run_con(
    con_mode: str, con_payload: Dict[str, Any],
    con_project: str = SYSTEM_CORE_PROJECT_NAME, con_auth_token: str = "",
) -> Dict[str, Any]:
    """Unified calculator route for Mama. Modes: research, traditional, business, real_world_excel."""
    mode = str(con_mode or "").strip().lower()
    payload = dict(con_payload or {})
    if mode == "research":
        return mama_research_calc_run_con(con_formula=str(payload.get("formula", "")), con_samples=int(payload.get("samples", 500)), con_project=con_project, con_auth_token=con_auth_token)
    if mode == "traditional":
        return mama_traditional_calc_run_con(con_expression=str(payload.get("expression", "")), con_variables=payload.get("variables"), con_rows=payload.get("rows"), con_project=con_project, con_auth_token=con_auth_token)
    if mode == "business":
        return mama_business_calc_run_con(con_operation=str(payload.get("operation", "")), con_inputs=dict(payload.get("inputs", {})), con_project=con_project, con_auth_token=con_auth_token)
    if mode in ("real_world_excel", "realworld_excel", "excel_validation"):
        return mama_validate_real_world_excel_con(
            con_formula=str(payload.get("formula", "")), con_excel_path=str(payload.get("excel_path", "")),
            con_observed_col=str(payload.get("observed_col", "")), con_sheet_name=payload.get("sheet_name"),
            con_abs_tolerance=float(payload.get("abs_tolerance", 0.05)), con_rel_tolerance=float(payload.get("rel_tolerance", 0.05)),
            con_scenario_label=payload.get("scenario_label"), con_units_map=payload.get("units_map"),
            con_report_output_path=payload.get("report_output_path"), con_uncertainty_col=payload.get("uncertainty_col"),
            con_uncertainty_abs_default=float(payload.get("uncertainty_abs_default", 0.0)),
            con_uncertainty_rel_default=float(payload.get("uncertainty_rel_default", 0.0)),
            con_strict_units=bool(payload.get("strict_units", False)), con_outlier_policy=str(payload.get("outlier_policy", "none")),
            con_baseline_formula=payload.get("baseline_formula"), con_verdict_version=str(payload.get("verdict_version", "v1")),
            con_run_id=payload.get("run_id"), con_project=con_project, con_auth_token=con_auth_token,
        )
    return {"success": False, "status": "ERROR", "error": "unsupported_mode", "supported_modes": ["research", "traditional", "business", "real_world_excel"], "mode": mode}

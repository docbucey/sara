"""Presentation-layer summary and result normalization for MAMA."""

from typing import Any, Dict, Optional

from .ux_adapt_mama import adapt_amip_ux_mama, _apply_native_runtime_policy_mama
from .osh_mama import _phase1_osh_surface_mama


def summarize_bucey_shunt_mama(shunt_response: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Summarize a shunt-wrapped response for ADA-friendly display surfaces."""
    envelope = dict(shunt_response or {})
    amip_payload = envelope.get("amip_payload") if isinstance(envelope.get("amip_payload"), dict) else {}
    result = envelope.get("result") if isinstance(envelope.get("result"), dict) else {}
    summary = adapt_amip_ux_mama(amip_payload=amip_payload, result=result)
    runtime_applied = _apply_native_runtime_policy_mama(summary=summary, ai_result=result, amip_payload=amip_payload)
    summary["native_runtime"] = runtime_applied["runtime_knobs"]
    if not summary.get("reasoning_visible"):
        summary["reasoning_visibility"] = "hidden_until_control_and_security_validation"
    phase1_surface = summary.get("phase1_surface") if isinstance(summary.get("phase1_surface"), dict) else _phase1_osh_surface_mama(result)
    summary.update({
        "ami_id": str(envelope.get("ami_id") or ""),
        "request_id": str(envelope.get("request_id") or ""),
        "phase1_outcome": str(phase1_surface.get("phase1_outcome") or "pending"),
        "osh_pipeline": phase1_surface,
        "message": "AMIP-aware summary prepared for low-strain MAMA presentation.",
    })
    return summary


def present_amipi_result_mama(amip_payload: Optional[Dict[str, Any]] = None, ai_result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Normalize AMIPI results for low-strain presentation without changing backend behavior."""
    summary = adapt_amip_ux_mama(amip_payload=amip_payload, result=ai_result)
    runtime_applied = _apply_native_runtime_policy_mama(summary=summary, ai_result=ai_result, amip_payload=amip_payload)
    summary["native_runtime"] = runtime_applied["runtime_knobs"]
    if not summary.get("reasoning_visible"):
        summary["reasoning_visibility"] = "hidden_until_control_and_security_validation"
    phase1_surface = summary.get("phase1_surface") if isinstance(summary.get("phase1_surface"), dict) else _phase1_osh_surface_mama(ai_result)
    summary["message"] = "Internal AI result normalized for MAMA display."
    summary["amipi_result"] = runtime_applied["result"]
    summary["phase1_outcome"] = str(phase1_surface.get("phase1_outcome") or "pending")
    summary["osh_pipeline"] = phase1_surface
    return summary

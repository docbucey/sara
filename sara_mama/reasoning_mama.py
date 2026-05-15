"""Reasoning validation and overlay helpers for MAMA."""

from typing import Any, Dict, Optional

try:
    from reasoning_protocols import list_reasoning_models  # type: ignore
    _ALLOWED_REASONING_MODELS = {row.get("model", "") for row in list_reasoning_models() if isinstance(row, dict)}
except Exception:
    _ALLOWED_REASONING_MODELS = set()


def _extract_validated_reasoning(result: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not isinstance(result, dict):
        return {}

    candidate = result
    if isinstance(result.get("reasoning"), dict):
        candidate = result["reasoning"]

    selected_by = str(candidate.get("selected_by") or "")
    selected_model = str(candidate.get("selected_model") or candidate.get("protocol") or "")
    security_validated = bool(candidate.get("security_validated"))
    envelope_validated = bool(candidate.get("envelope_validated"))
    advisory_only = bool(candidate.get("advisory_only"))
    presentation_only = bool(candidate.get("presentation_only"))
    schema_safe = bool(candidate.get("schema_safe"))

    if selected_by != "CONTROL":
        return {}
    if not security_validated or not envelope_validated:
        return {}
    if not advisory_only or not presentation_only or not schema_safe:
        return {}
    if _ALLOWED_REASONING_MODELS and selected_model not in _ALLOWED_REASONING_MODELS:
        return {}

    output = candidate.get("model_output")
    if not isinstance(output, dict):
        output = {}

    return {
        "selected_by": selected_by,
        "selected_model": selected_model,
        "domain": str(candidate.get("domain") or ""),
        "security_validated": security_validated,
        "envelope_validated": envelope_validated,
        "advisory_only": advisory_only,
        "presentation_only": presentation_only,
        "schema_safe": schema_safe,
        "model_output": output,
    }


def _build_reasoning_overlay(request: Dict[str, Any], result: Optional[Dict[str, Any]], mode: str, strain: str) -> Dict[str, Any]:
    validated = _extract_validated_reasoning(result)
    profile = request.get("machine_profile") if isinstance(request.get("machine_profile"), dict) else {}
    profile_id = str(profile.get("profile_id") or "default")

    overlay = {
        "visible": bool(validated),
        "profile_adaptation": {
            "profile_id": profile_id,
            "mode": mode,
            "strain": strain,
            "voice_first": True,
            "low_click": True,
        },
        "accessibility": {
            "advisory_only": True,
            "presentation_only": True,
            "security_gate_before_visibility": True,
        },
        "generative_surface": {
            "style": "guided" if mode == "interactive" else "quiet",
            "reasoning_lens": str(validated.get("selected_model") or "none"),
            "reasoning_domain": str(validated.get("domain") or "none"),
            "reasoning_summary": str((validated.get("model_output") or {}).get("notes") or "No validated reasoning overlay."),
        },
    }
    if validated:
        overlay["validated_reasoning"] = validated
    return overlay

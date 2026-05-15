"""
SARA Control — AMIP protocol: dispatch, normalization, SHI governor, generation profiles, OSH pipeline.
Extracted from sara_controlgen1.py.
"""
import os
import uuid
from typing import Any, Dict, List, Optional

try:
    from sara_control.loader_con import _load_core_module, _load_sdk_gen1_module_con
    _core = _load_core_module()
except Exception:
    _core = None

from sara_control.routing_con import _pick_proto_field_con

AMIP_PROTOCOL_VERSION = "0.1"
AMIPI_LOCAL_TARGETS: Dict[str, str] = {
    "nano": "0001 00000001 0001",
    "copilot": "0001 00000002 0001",
    "gemini_local": "0001 00000003 0001",
    "ollama_local": "0001 00000004 0001",
    "openai_local": "0001 00000005 0001",
}


def _ollama_enabled_con() -> bool:
    raw = str(os.getenv("SARA_ALLOW_OLLAMA", "")).strip().lower()
    return raw in {"1", "true", "yes", "on", "enabled"}


def _ollama_policy_mode_con() -> str:
    raw = str(os.getenv("SARA_OLLAMA_POLICY", "")).strip().lower()
    if raw in {"full", "allow", "on", "enabled"}:
        return "full"
    if raw in {"backup", "fallback", "limited"}:
        return "backup"
    if _ollama_enabled_con():
        return "full"
    return "off"


def _default_non_ollama_backend_con(mode: str = "interactive") -> str:
    mode_l = str(mode or "interactive").strip().lower()
    if mode_l == "night_shift":
        return "nano"
    return "copilot"


def _ollama_backup_requested_con(amip_request: Dict[str, Any]) -> bool:
    payload = (amip_request or {}).get("payload") if isinstance(amip_request, dict) else {}
    if not isinstance(payload, dict):
        return False
    if bool(payload.get("allow_ollama_backup", False)):
        return True
    if str(payload.get("fallback_backend") or "").strip().lower() == "ollama_local":
        return True
    backup_backends = payload.get("backup_backends")
    if isinstance(backup_backends, list):
        for item in backup_backends:
            if str(item or "").strip().lower() == "ollama_local":
                return True
    return False


_SHI_HISTORY_CON: List[float] = []
_SHI_HISTORY_MAXLEN_CON = 8


def _safe_float_con(value: Any, default: float) -> float:
    try:
        parsed = float(value)
        if parsed != parsed or parsed in {float("inf"), float("-inf")}:
            return float(default)
        return parsed
    except Exception:
        return float(default)


def _compute_shi_metrics_con(payload_block: Dict[str, Any], resource_budget: Dict[str, Any]) -> Dict[str, float]:
    runtime_ms = _safe_float_con(payload_block.get("runtime_ms", resource_budget.get("runtime_ms", 15000)), 15000.0)
    token_budget = _safe_float_con(resource_budget.get("tokens", 4096), 4096.0)

    memory = _safe_float_con(payload_block.get("memory", token_budget / 1024.0), token_budget / 1024.0)
    footprint = _safe_float_con(payload_block.get("footprint", max(0.1, token_budget / 4096.0)), max(0.1, token_budget / 4096.0))
    runtime = max(0.001, _safe_float_con(payload_block.get("runtime", runtime_ms / 1000.0), runtime_ms / 1000.0))
    enumerator = max(0.0, _safe_float_con(payload_block.get("enumerator", 1.0), 1.0))
    denominator = max(0.001, runtime + enumerator)
    shi_value = (memory + footprint) / denominator

    return {
        "memory": float(memory),
        "footprint": float(footprint),
        "runtime": float(runtime),
        "enumerator": float(enumerator),
        "shi": float(shi_value),
    }


def _evaluate_shi_governor_con(mode: str, strain: str, shi_metrics: Dict[str, float]) -> Dict[str, Any]:
    global _SHI_HISTORY_CON

    shi_value = float(shi_metrics.get("shi", 0.0))
    prev = _SHI_HISTORY_CON[-1] if _SHI_HISTORY_CON else shi_value
    prev2 = _SHI_HISTORY_CON[-2] if len(_SHI_HISTORY_CON) >= 2 else prev
    d1_shi = shi_value - prev
    d2_shi = d1_shi - (prev - prev2)

    _SHI_HISTORY_CON.append(shi_value)
    if len(_SHI_HISTORY_CON) > _SHI_HISTORY_MAXLEN_CON:
        _SHI_HISTORY_CON = _SHI_HISTORY_CON[-_SHI_HISTORY_MAXLEN_CON:]

    mode_l = str(mode or "interactive").strip().lower()
    strain_l = str(strain or "medium").strip().lower()

    warn = 1.8
    clamp = 2.6
    deny = 4.2
    if mode_l == "night_shift":
        warn, clamp, deny = 2.1, 3.2, 5.0
    if strain_l in {"constrained", "critical", "high"}:
        warn -= 0.2
        clamp -= 0.25
        deny -= 0.5

    derivative_risk = d1_shi > 0.25 and d2_shi > 0.08
    if shi_value >= deny:
        decision = "deny"
        reason = "shi_too_high"
    elif shi_value >= clamp or (derivative_risk and shi_value >= warn):
        decision = "clamp"
        reason = "shi_rising"
    elif shi_value >= warn:
        decision = "warn"
        reason = "shi_elevated"
    else:
        decision = "allow"
        reason = "shi_ok"

    return {
        "decision": decision,
        "reason": reason,
        "shi": shi_value,
        "d1_shi": float(d1_shi),
        "d2_shi": float(d2_shi),
        "thresholds": {"warn": warn, "clamp": clamp, "deny": deny},
    }


def _apply_shi_governor_con(mode: str, resource_budget: Dict[str, Any], payload_block: Dict[str, Any]) -> Dict[str, Any]:
    strain = str(resource_budget.get("strain", "medium") or "medium")
    shi_metrics = _compute_shi_metrics_con(payload_block, resource_budget)
    governor = _evaluate_shi_governor_con(mode=mode, strain=strain, shi_metrics=shi_metrics)

    adjusted_budget = dict(resource_budget)
    adjusted_payload = dict(payload_block)
    decision = governor.get("decision")
    if decision == "clamp":
        adjusted_budget["tokens"] = max(512, int(_safe_float_con(adjusted_budget.get("tokens", 4096), 4096.0) * 0.7))
        adjusted_budget["runtime_ms"] = max(1000, int(_safe_float_con(adjusted_budget.get("runtime_ms", 15000), 15000.0) * 0.7))
        adjusted_payload["lightweight_mode"] = True
        adjusted_payload["max_depth"] = min(2, int(_safe_float_con(adjusted_payload.get("max_depth", 3), 3.0)))
    elif decision == "deny":
        adjusted_payload["dry_run"] = True
        adjusted_payload["metadata_only"] = True

    return {
        "resource_budget": adjusted_budget,
        "payload": adjusted_payload,
        "state": {
            **shi_metrics,
            **governor,
            "mode": mode,
            "strain": strain,
        },
    }


GENERATION_PROFILE_PRESETS_CON: Dict[str, Dict[str, Any]] = {
    "strict_deterministic": {
        "temperature": 0.0,
        "top_p": 1.0,
        "seed": 7,
        "max_variance": "minimal",
        "style": "precise",
    },
    "stable_probabilistic": {
        "temperature": 0.22,
        "top_p": 0.9,
        "seed": None,
        "max_variance": "low",
        "style": "balanced",
    },
    "creative_probabilistic": {
        "temperature": 0.68,
        "top_p": 0.95,
        "seed": None,
        "max_variance": "medium",
        "style": "expressive",
    },
}


def _resolve_generation_profile_request_con(mode: str, payload_block: Dict[str, Any]) -> str:
    requested = str(
        payload_block.get("generation_profile")
        or payload_block.get("response_profile")
        or payload_block.get("creativity_mode")
        or ""
    ).strip().lower()
    aliases = {
        "strict": "strict_deterministic",
        "deterministic": "strict_deterministic",
        "stable": "stable_probabilistic",
        "balanced": "stable_probabilistic",
        "creative": "creative_probabilistic",
        "expressive": "creative_probabilistic",
    }
    normalized = aliases.get(requested, requested)
    if normalized in GENERATION_PROFILE_PRESETS_CON:
        return normalized
    if str(mode or "interactive").strip().lower() == "night_shift":
        return "stable_probabilistic"
    return "creative_probabilistic"


def _apply_generation_profile_policy_con(
    mode: str,
    resource_budget: Dict[str, Any],
    payload_block: Dict[str, Any],
    shi_governor_state: Dict[str, Any],
) -> Dict[str, Any]:
    requested = _resolve_generation_profile_request_con(mode, payload_block)
    selected = requested
    reasons: List[str] = []
    fallback_chain: List[str] = [requested]

    strain = str(resource_budget.get("strain", "medium") or "medium").strip().lower()
    shi_decision = str(shi_governor_state.get("decision", "allow") or "allow").strip().lower()
    requires_repeatability = bool(payload_block.get("requires_repeatability", False))

    if requires_repeatability and selected != "strict_deterministic":
        selected = "strict_deterministic"
        reasons.append("repeatability_requested")

    if shi_decision == "warn" and selected == "creative_probabilistic":
        selected = "stable_probabilistic"
        reasons.append("shi_warn_downgrade")

    if shi_decision == "clamp" and selected != "strict_deterministic":
        selected = "stable_probabilistic"
        reasons.append("shi_clamp_downgrade")

    if shi_decision == "deny":
        selected = "strict_deterministic"
        reasons.append("shi_deny_forced_strict")

    if strain in {"constrained", "critical", "high"} and selected == "creative_probabilistic":
        selected = "stable_probabilistic"
        reasons.append("strain_constrained_downgrade")

    if selected not in fallback_chain:
        fallback_chain.append(selected)

    controls = dict(GENERATION_PROFILE_PRESETS_CON[selected])
    effective_payload = dict(payload_block)
    effective_payload["generation_profile"] = selected
    effective_payload["generation_controls"] = controls

    return {
        "payload": effective_payload,
        "state": {
            "requested_profile": requested,
            "selected_profile": selected,
            "fallback_chain": fallback_chain,
            "reasons": reasons,
            "mode": mode,
            "strain": strain,
            "shi_decision": shi_decision,
            "probabilistic_enabled": selected != "strict_deterministic",
            "effective_controls": controls,
        },
    }


def _normalize_amip_request_con(amip_payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    envelope = dict(amip_payload or {})
    routing_intent = str(
        _pick_proto_field_con(envelope, "routing_intent", "")
        or _pick_proto_field_con(envelope, "intent", "local.search")
    ).strip() or "local.search"
    mode = str(_pick_proto_field_con(envelope, "mode", "interactive") or "interactive").strip().lower()
    if mode not in {"interactive", "night_shift"}:
        mode = "interactive"
    profile_ref = _pick_proto_field_con(envelope, "machine_profile", {}) or _pick_proto_field_con(envelope, "profile_ref", {}) or {}
    if _core is not None and hasattr(_core, "resolve_machine_profile_core"):
        profile_ref = _core.resolve_machine_profile_core(profile_ref)
    resource_budget = dict(_pick_proto_field_con(envelope, "resource_budget", {}) or {})
    resource_budget.setdefault("strain", "medium")
    resource_budget.setdefault("tokens", 4096)
    resource_budget.setdefault("runtime_ms", 15000)
    payload_block = _pick_proto_field_con(envelope, "payload", {}) or {}
    if not isinstance(payload_block, dict):
        payload_block = {"value": payload_block}
    document_context = payload_block.get("document_context") if isinstance(payload_block.get("document_context"), dict) else {}
    if not document_context:
        document_context = {
            "document_id": str(payload_block.get("document_id") or ""),
            "document_version": str(payload_block.get("document_version") or ""),
            "traversal_mode": str(payload_block.get("traversal_mode") or "single_pass"),
            "focus_scope": str(payload_block.get("focus_scope") or "document"),
            "hierarchy": payload_block.get("hierarchy") if isinstance(payload_block.get("hierarchy"), dict) else {},
        }
    payload_block["document_context"] = document_context
    if routing_intent == "self.evolve":
        payload_block.setdefault("dry_run", True)
    shi_governed = _apply_shi_governor_con(mode=mode, resource_budget=resource_budget, payload_block=payload_block)
    resource_budget = shi_governed["resource_budget"]
    payload_block = shi_governed["payload"]
    generation_policy = _apply_generation_profile_policy_con(
        mode=mode,
        resource_budget=resource_budget,
        payload_block=payload_block,
        shi_governor_state=shi_governed["state"],
    )
    payload_block = generation_policy["payload"]
    envelope.update({
        "amip_version": str(_pick_proto_field_con(envelope, "amip_version", AMIP_PROTOCOL_VERSION) or AMIP_PROTOCOL_VERSION),
        "mode": mode,
        "routing_intent": routing_intent,
        "resource_budget": resource_budget,
        "payload": payload_block,
        "shi_governor": shi_governed["state"],
        "generation_policy": generation_policy["state"],
        "machine_profile": profile_ref,
        "correlation_id": str(_pick_proto_field_con(envelope, "correlation_id", "") or uuid.uuid4()),
    })
    return envelope


def _control_route_guard_con(shunt_envelope: Dict[str, Any], normalized: Dict[str, Any]) -> Dict[str, Any]:
    source_pillar = str(shunt_envelope.get("source_pillar") or "CORE").strip().upper()
    target_pillar = str(shunt_envelope.get("target_pillar") or "CONTROL").strip().upper()
    if target_pillar != "CONTROL":
        return {"ok": False, "status": "QUARANTINE", "reason": "CONTROL:target-pillar-must-be-control"}
    if source_pillar not in {"CORE", "CONTROL", "SECURITY", "MAMA", "SDK", "WEB_UI", "SMITHY"}:
        return {"ok": False, "status": "QUARANTINE", "reason": "CONTROL:unknown-source-pillar"}

    payload = normalized.get("payload") if isinstance(normalized.get("payload"), dict) else {}
    shi_governor = normalized.get("shi_governor") if isinstance(normalized.get("shi_governor"), dict) else {}
    if str(shi_governor.get("decision", "allow")).lower() == "deny":
        return {
            "ok": False,
            "status": "HOLD",
            "reason": "CONTROL:shi-governor-deny",
            "shi_governor": shi_governor,
        }
    environment = str(payload.get("environment") or payload.get("network_mode") or "").strip().lower()
    if environment and environment not in {"local", "local_only", "trusted_local", "interactive", "night_shift", "lan", "internet_strict"}:
        return {"ok": False, "status": "HOLD", "reason": "CONTROL:unknown-environment-state"}

    if str(normalized.get("routing_intent") or "").strip().lower() == "self.evolve":
        if bool(payload.get("dry_run", True)) is not True:
            return {"ok": False, "status": "DENY", "reason": "CONTROL:self-evolve-requires-dry-run"}

    return {"ok": True}


def _resolve_ami_target_con(shunt_envelope: Optional[Dict[str, Any]], amip_request: Dict[str, Any]) -> str:
    envelope = dict(shunt_envelope or {})
    explicit_ami = str(
        _pick_proto_field_con(envelope, "target_ami_id", "")
        or _pick_proto_field_con(envelope, "ami_id", "")
        or ""
    ).strip()
    if explicit_ami:
        return explicit_ami
    payload = _pick_proto_field_con(amip_request, "payload", {}) if isinstance(amip_request, dict) else {}
    backend = str((payload or {}).get("backend") or "").strip().lower()
    if not backend and isinstance(payload, dict):
        doc_ctx = payload.get("document_context") if isinstance(payload.get("document_context"), dict) else {}
        doc_scope = str(doc_ctx.get("focus_scope") or "").strip().lower()
        persona = str(payload.get("persona") or payload.get("narrative_mode") or "").strip().lower()
        memory_hint = str(payload.get("memory_hint") or payload.get("memory_state") or "").strip().lower()
        ensemble = payload.get("ensemble_backends")
        if isinstance(ensemble, list) and ensemble:
            backend = str(ensemble[0]).strip().lower()
        elif "code" in doc_scope or persona in {"coder", "engineering"}:
            backend = "copilot"
        elif "research" in doc_scope or memory_hint in {"research", "archive"}:
            backend = "gemini_local"
        else:
            backend = "nano"
    normalized_mode = str((amip_request or {}).get("mode") or "interactive").strip().lower()
    ollama_policy = _ollama_policy_mode_con()
    if backend == "ollama_local":
        if ollama_policy == "off":
            backend = _default_non_ollama_backend_con(normalized_mode)
        elif ollama_policy == "backup" and not _ollama_backup_requested_con(amip_request):
            backend = _default_non_ollama_backend_con(normalized_mode)
    resolved = AMIPI_LOCAL_TARGETS.get(backend, "")
    if resolved:
        return resolved
    return AMIPI_LOCAL_TARGETS.get(_default_non_ollama_backend_con(normalized_mode), "")


def dispatch_amipi_con(amip_request: Dict[str, Any], shunt_envelope: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Route a validated AMIP request into the local-only AMIPI interface layer."""
    normalized = _normalize_amip_request_con(amip_request)
    target_ami = _resolve_ami_target_con(shunt_envelope, normalized)

    try:
        sdk_mod = _load_sdk_gen1_module_con()
    except Exception:
        sdk_mod = None
    if sdk_mod is not None and hasattr(sdk_mod, "dispatch_amipi_backend"):
        return sdk_mod.dispatch_amipi_backend(
            backend_ami=target_ami,
            action=normalized.get("routing_intent", "amipi.invoke"),
            payload=normalized.get("payload", {}),
            correlation_id=normalized.get("correlation_id", ""),
            machine_profile=normalized.get("machine_profile", {}),
            mode=normalized.get("mode", "interactive"),
        )
    return {
        "success": True,
        "status": "AMIPI_ROUTE_READY",
        "target_ami_id": target_ami,
        "routing_intent": normalized.get("routing_intent"),
        "correlation_id": normalized.get("correlation_id"),
        "note": "AMIPI routing hook prepared in CONTROL; SDK backend dispatch remains local-only stubbed.",
    }


_PHASE1_OSH_CODES_CON = ["OSH-1", "OSH-2", "OSH-3", "OSH-4", "OSH-5"]


def _phase1_outcome_from_status_con(status: str, error: str = "") -> str:
    status_u = str(status or "").strip().upper()
    error_l = str(error or "").strip().lower()
    if "schema" in error_l or status_u in {"SCHEMA_FAIL", "SCHEMA-FAIL"}:
        return "schema_fail"
    if status_u in {"DENY", "FAIL", "ERROR"}:
        return "deny"
    if status_u in {"CHALLENGE", "CONSTRAIN", "CONSTRAINED"} or "constrain" in error_l:
        return "constrain"
    if status_u in {"QUARANTINE", "LOCKDOWN", "HOLD"}:
        return "boundary_blocked"
    if status_u in {"ALLOW", "READY", "PASS"}:
        return "allow"
    return "pending"


def _phase1_pipeline_con(stage_code: str, status: str, error: str = "") -> Dict[str, Any]:
    code = str(stage_code or "OSH-1").strip().upper()
    if code not in _PHASE1_OSH_CODES_CON:
        code = "OSH-1"
    index = _PHASE1_OSH_CODES_CON.index(code)
    outcome = _phase1_outcome_from_status_con(status=status, error=error)
    labels = {
        "OSH-1": "Intake",
        "OSH-2": "Normalization",
        "OSH-3": "Boundary",
        "OSH-4": "Schema",
        "OSH-5": "Non-Authority",
    }
    stages = []
    for i, item in enumerate(_PHASE1_OSH_CODES_CON):
        if i < index:
            state = "complete"
        elif i == index:
            state = "active"
        else:
            state = "pending"
        stages.append({"code": item, "label": labels.get(item, item), "state": state})
    return {
        "current_stage": code,
        "stages": stages,
        "phase1_outcome": outcome,
        "status": str(status or "PENDING").upper(),
    }

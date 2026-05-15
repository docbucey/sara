"""CORE AMIP/Shunt: machine profiles, payload builders, envelope construction."""
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from .proto_lingua import _to_proto_lingua, validate_resonance

import re

# -------------------------
# Helpers
# -------------------------

def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _build_core_work_state(
    stage: str = "created",
    status: str = "ready",
    owner_pillar: str = "CORE",
    additional: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build a stable work-state record for CORE-owned wrappers, profiles, and envelopes."""
    state = {
        "status": str(status or "ready"),
        "stage": str(stage or "created"),
        "owner_pillar": str(owner_pillar or "CORE"),
        "last_transition_at": _iso_now(),
        "deterministic": True,
    }
    if isinstance(additional, dict):
        state.update({k: v for k, v in additional.items() if v is not None})
    return state


# -------------------------
# Constants
# -------------------------

AMI_ID_PATTERN = re.compile(r"^[0-9A-Fa-f]{4}\s[0-9A-Fa-f]{8}\s[0-9A-Fa-f]{4}$")
CORE_DEFAULT_AMIP_VERSION = "0.1"
CORE_DEFAULT_AMI_IDS: Dict[str, str] = {
    "sara": "0100 00000000 0001",
    "user": "0010 00000000 0001",
    "machine": "0011 00000000 0001",
    "nano": "0001 00000001 0001",
    "copilot": "0001 00000002 0001",
    "gemini_local": "0001 00000003 0001",
    "ollama_local": "0001 00000004 0001",
    "openai_local": "0001 00000005 0001",
}
CORE_DEFAULT_MACHINE_PROFILE: Dict[str, Any] = {
    "profile_id": "default_local_machine",
    "profile_version": "v1",
    "hardware_class": "pc",
    "default_mode": "interactive",
    "night_shift_available": True,
    "allowed_automation_level": "bounded_batch",
    "allowed_routing_intents": [
        "document.read",
        "document.write",
        "document.validate",
        "document.transform",
        "local.search",
        "local.ingest",
        "security.scan",
        "sdk.invoke",
        "amipi.invoke",
    ],
    "resource_budget": {
        "strain": "medium",
        "tokens": 4096,
        "runtime_ms": 15000,
    },
}

CORE_LITE_CONTRACT_VERSION = "gen1-core-lite-2026-04-11"


# -------------------------
# Functions
# -------------------------

def core_validate_ami_id(ami_id: str) -> bool:
    return bool(AMI_ID_PATTERN.match(str(ami_id or "").strip()))


def core_default_ami_id(actor: str = "sara") -> str:
    return CORE_DEFAULT_AMI_IDS.get(str(actor or "sara").strip().lower(), CORE_DEFAULT_AMI_IDS["sara"])


def resolve_machine_profile_core(profile_ref: Optional[Dict[str, Any]] = None, ami_id: str = "") -> Dict[str, Any]:
    """Resolve the effective CORE-owned machine profile for a local Gen1 request."""
    resolved = dict(CORE_DEFAULT_MACHINE_PROFILE)
    if isinstance(profile_ref, dict):
        resolved.update({k: v for k, v in profile_ref.items() if v is not None})
    resolved.setdefault("ami_id", ami_id or core_default_ami_id("machine"))
    resolved.setdefault("profile_id", CORE_DEFAULT_MACHINE_PROFILE["profile_id"])
    resolved.setdefault("profile_version", CORE_DEFAULT_MACHINE_PROFILE["profile_version"])
    return resolved


def build_amip_payload_core(
    routing_intent: str,
    payload: Optional[Dict[str, Any]] = None,
    mode: Optional[str] = None,
    machine_profile: Optional[Dict[str, Any]] = None,
    correlation_id: Optional[str] = None,
    resource_budget: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build a deterministic AMIP v0.1 payload using CORE defaults and profile context."""
    import uuid

    resolved_profile = resolve_machine_profile_core(machine_profile)
    resolved_mode = str(mode or resolved_profile.get("default_mode", "interactive")).strip().lower()
    if resolved_mode not in {"interactive", "night_shift"}:
        resolved_mode = "interactive"
    resolved_budget = dict(resolved_profile.get("resource_budget", {}))
    if isinstance(resource_budget, dict):
        resolved_budget.update(resource_budget)
    resolved_routing = str(routing_intent or "local.search").strip() or "local.search"
    resolved_payload = dict(payload or {})
    if "document_context" not in resolved_payload or not isinstance(resolved_payload.get("document_context"), dict):
        resolved_payload["document_context"] = {
            "document_id": str(resolved_payload.get("document_id") or ""),
            "document_version": str(resolved_payload.get("document_version") or ""),
            "traversal_mode": str(resolved_payload.get("traversal_mode") or "single_pass"),
            "focus_scope": str(resolved_payload.get("focus_scope") or "document"),
            "hierarchy": resolved_payload.get("hierarchy") if isinstance(resolved_payload.get("hierarchy"), dict) else {},
        }
    return {
        "amip_version": CORE_DEFAULT_AMIP_VERSION,
        "source_pillar": "CORE",
        "target_pillar": "CONTROL",
        "deterministic": True,
        "mode": resolved_mode,
        "routing_intent": resolved_routing,
        "resource_budget": {
            "strain": str(resolved_budget.get("strain", "medium")),
            "tokens": int(resolved_budget.get("tokens", 4096) or 0),
            "runtime_ms": int(resolved_budget.get("runtime_ms", 15000) or 1),
        },
        "payload": resolved_payload,
        "machine_profile": {
            "profile_id": resolved_profile.get("profile_id", CORE_DEFAULT_MACHINE_PROFILE["profile_id"]),
            "profile_version": resolved_profile.get("profile_version", CORE_DEFAULT_MACHINE_PROFILE["profile_version"]),
            "ami_id": resolved_profile.get("ami_id", core_default_ami_id("machine")),
            "allowed_automation_level": resolved_profile.get("allowed_automation_level", "bounded_batch"),
        },
        "workflow_state": _build_core_work_state(
            stage="amip_built",
            status="ready",
            additional={
                "routing_intent": resolved_routing,
                "automation_allowed": resolved_mode == "night_shift",
            },
        ),
        "correlation_id": str(correlation_id or uuid.uuid4()),
    }


def build_bucey_shunt_envelope_core(
    amip_payload: Dict[str, Any],
    ami_id: str = "",
    profile_ref: Optional[Dict[str, Any]] = None,
    correlation_id: Optional[str] = None,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Build a deterministic Bucey Shunt envelope for local C#/Python or internal AI traffic."""
    import uuid

    resolved_ami = ami_id if core_validate_ami_id(ami_id) else core_default_ami_id("sara")
    resolved_profile = resolve_machine_profile_core(profile_ref, ami_id=resolved_ami)
    resolved_correlation = str(correlation_id or amip_payload.get("correlation_id") or uuid.uuid4())
    resolved_request_id = str(request_id or uuid.uuid4())
    resolved_shunt_id = str(uuid.uuid4())
    timestamp_utc = _iso_now()
    routing_intent = str(amip_payload.get("routing_intent") or "local.search").strip() or "local.search"
    payload_block = dict(amip_payload.get("payload") or {})
    return {
        "shunt_id": resolved_shunt_id,
        "source_pillar": "CORE",
        "target_pillar": "CONTROL",
        "timestamp": timestamp_utc,
        "intent": routing_intent,
        "payload": payload_block,
        "context_tags": ["core", "bucey", str(amip_payload.get("mode", "interactive")), "local_only"],
        "requires_response": True,
        "header": {
            "shunt_version": "gen1",
            "protocol_family": "bucey_shunt",
            "shunt_id": resolved_shunt_id,
            "timestamp_utc": timestamp_utc,
        },
        "fsm_bits": {
            "state": str(amip_payload.get("mode", "interactive")),
            "routing_policy": "local_only",
            "strain_policy": str(amip_payload.get("resource_budget", {}).get("strain", "medium")),
        },
        "ami_id": resolved_ami,
        "profile_ref": {
            "profile_id": resolved_profile.get("profile_id"),
            "profile_version": resolved_profile.get("profile_version"),
        },
        "correlation_id": resolved_correlation,
        "request_id": resolved_request_id,
        "transport_policy": {
            "local_only": True,
            "response_expected": True,
            "allow_automation": amip_payload.get("mode") == "night_shift",
        },
        "workflow_state": _build_core_work_state(
            stage="shunt_built",
            status="ready",
            additional={"routing_intent": routing_intent},
        ),
        "amip_payload": dict(amip_payload or {}),
    }


def unwrap_bucey_shunt_core(envelope: Dict[str, Any]) -> Dict[str, Any]:
    """Return normalized shunt metadata for CONTROL/SECURITY without mutating the original envelope."""
    if not isinstance(envelope, dict):
        return {"success": False, "error": "Bucey Shunt envelope must be a dict"}
    if "amip_payload" not in envelope:
        return {"success": False, "error": "Missing amip_payload in Bucey Shunt envelope"}
    header = dict(envelope.get("header") or {})
    amip_payload = dict(envelope.get("amip_payload") or {})
    resolved_profile = resolve_machine_profile_core(envelope.get("profile_ref"), ami_id=str(envelope.get("ami_id", "")))
    return {
        "success": True,
        "ami_id": str(envelope.get("ami_id") or core_default_ami_id("sara")),
        "profile_ref": {
            "profile_id": resolved_profile.get("profile_id"),
            "profile_version": resolved_profile.get("profile_version"),
        },
        "correlation_id": str(envelope.get("correlation_id") or amip_payload.get("correlation_id") or ""),
        "request_id": str(envelope.get("request_id") or ""),
        "amip_payload": amip_payload,
    }


def build_core_lite_bundle_core(
    routing_intent: str,
    payload: Optional[Dict[str, Any]] = None,
    mode: Optional[str] = None,
    machine_profile: Optional[Dict[str, Any]] = None,
    correlation_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Bounded CORE-Lite export wrapper; builders only, no routing authority."""
    amip_payload = build_amip_payload_core(
        routing_intent=routing_intent,
        payload=payload,
        mode=mode,
        machine_profile=machine_profile,
        correlation_id=correlation_id,
    )
    shunt_envelope = build_bucey_shunt_envelope_core(
        amip_payload=amip_payload,
        ami_id=str((machine_profile or {}).get("ami_id") or ""),
        profile_ref=machine_profile,
        correlation_id=str(amip_payload.get("correlation_id") or ""),
    )
    return {
        "contract_version": CORE_LITE_CONTRACT_VERSION,
        "deterministic": True,
        "routing_authority": "CONTROL",
        "builders_only": True,
        "amip_payload": amip_payload,
        "shunt_envelope": shunt_envelope,
        "state_binding": {
            "schema_store": "/var/lib/sara-lite/nbs/schemas/",
            "state_store": "/var/lib/sara-lite/runtime/core-state.json",
        },
    }

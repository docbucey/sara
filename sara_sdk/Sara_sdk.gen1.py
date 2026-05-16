#!/usr/bin/env python3
"""
SARA SDK Gen1 — Pillar 5 skeleton.

Purpose:
- Active Gen1 SDK pillar for special-case protocols.
- Home for device, ARMs, server/service, IDE, TV, and related integration lanes.
- Stub-only for now: no security logic and no cross-pillar runtime imports.

Architecture rule:
    SDK / MAMA / Security -> Control -> Core

This file is intentionally limited to placeholders so the folder can expand
cleanly without changing other pillars.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import os
import importlib.util
import uuid

SDK_PILLAR_NAME = "SDK"
SDK_VERSION = "gen1-minimal-runtime"
SDK_PROTOCOL_LANES = [
    "android",
    "ios",
    "arm",
    "tv",
    "device",
    "server",
    "ide",
    "special_case",
]
SDK_INTERNAL_AMI_LANES: Dict[str, str] = {
    "nano": "0001 00000001 0001",
    "copilot": "0001 00000002 0001",
    "gemini_local": "0001 00000003 0001",
    "ollama_local": "0001 00000004 0001",
    "openai_local": "0001 00000005 0001",
}

SDK_OLLAMA_AMI = SDK_INTERNAL_AMI_LANES["ollama_local"]


def _sdk_ollama_enabled() -> bool:
    raw = str(os.getenv("SARA_ALLOW_OLLAMA", "")).strip().lower()
    return raw in {"1", "true", "yes", "on", "enabled"}


def _sdk_ollama_policy_mode() -> str:
    raw = str(os.getenv("SARA_OLLAMA_POLICY", "")).strip().lower()
    if raw in {"full", "allow", "on", "enabled"}:
        return "full"
    if raw in {"backup", "fallback", "limited"}:
        return "backup"
    if _sdk_ollama_enabled():
        return "full"
    return "off"


def _sdk_default_ami() -> str:
    return SDK_INTERNAL_AMI_LANES.get("copilot", next(iter(SDK_INTERNAL_AMI_LANES.values()), ""))


def _normalize_document_context(payload: Dict[str, Any]) -> Dict[str, Any]:
    doc_ctx = payload.get("document_context") if isinstance(payload.get("document_context"), dict) else {}
    if doc_ctx:
        return dict(doc_ctx)
    return {
        "document_id": str(payload.get("document_id") or ""),
        "document_version": str(payload.get("document_version") or ""),
        "traversal_mode": str(payload.get("traversal_mode") or "single_pass"),
        "focus_scope": str(payload.get("focus_scope") or "document"),
        "hierarchy": payload.get("hierarchy") if isinstance(payload.get("hierarchy"), dict) else {},
    }


def _local_backend_execute(backend_ami: str, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    # Deterministic local adapter response; no external execution side effects.
    doc_ctx = _normalize_document_context(payload)
    response = {
        "backend_ami": backend_ami,
        "action": action,
        "document_context": doc_ctx,
        "advisory": True,
        "deterministic": True,
    }
    if str(action).strip().lower() in {"amipi.invoke", "local.ai.route", "internal_ai.route"}:
        response["result_text"] = "Local adapter executed deterministic placeholder inference."
    else:
        response["result_text"] = "Local adapter accepted request."
    return response


def _load_micro_ai_installer_sdk():
    installer_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "common", "micro_ai_installer.py")
    if not os.path.exists(installer_path):
        return None
    spec = importlib.util.spec_from_file_location("sara_sdk_micro_ai_installer", installer_path)
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def sdk_identity_catalog() -> Dict[str, str]:
    """Return the SDK-facing AMI lane catalog for local internal AI targets."""
    return dict(SDK_INTERNAL_AMI_LANES)


@dataclass
class SDKRequest:
    """Placeholder request shape for future SDK routing and AMIPI-aware dispatch."""

    protocol: str = ""
    action: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    source: str = "sdk"
    requires_response: bool = True
    context_tags: List[str] = field(default_factory=list)
    ami_id: str = ""
    correlation_id: str = ""
    machine_profile: Dict[str, Any] = field(default_factory=dict)
    mode: str = "interactive"
    resource_budget: Dict[str, Any] = field(default_factory=dict)


def sdk_status() -> Dict[str, Any]:
    """Return stub metadata for the Gen1 SDK pillar."""
    return {
        "success": True,
        "pillar": SDK_PILLAR_NAME,
        "version": SDK_VERSION,
        "supported_protocols": list(SDK_PROTOCOL_LANES),
        "internal_ami_lanes": sdk_identity_catalog(),
        "status": "ADAPTER_RUNTIME_READY",
        "note": "SDK exposes deterministic local adapter behavior under CONTROL governance.",
    }


def build_amipi_dispatch_record(
    backend_ami: str,
    action: str,
    payload: Optional[Dict[str, Any]] = None,
    correlation_id: str = "",
    machine_profile: Optional[Dict[str, Any]] = None,
    mode: str = "interactive",
) -> Dict[str, Any]:
    return {
        "dispatch_id": str(uuid.uuid4()),
        "backend_ami": str(backend_ami or ""),
        "action": str(action or "").strip(),
        "payload": dict(payload or {}),
        "document_context": _normalize_document_context(dict(payload or {})),
        "correlation_id": str(correlation_id or ""),
        "machine_profile": dict(machine_profile or {}),
        "mode": str(mode or "interactive"),
        "status": "AMIPI_RECORD_READY",
    }


def dispatch_amipi_backend(
    backend_ami: str,
    action: str,
    payload: Optional[Dict[str, Any]] = None,
    correlation_id: str = "",
    machine_profile: Optional[Dict[str, Any]] = None,
    mode: str = "interactive",
) -> Dict[str, Any]:
    """Local-only AMIPI routing stub for internal AI backends addressed by AMI."""
    selected_ami = str(backend_ami or "").strip()
    if not selected_ami:
        selected_ami = _sdk_default_ami()

    payload_dict = dict(payload or {})
    backup_requested = bool(payload_dict.get("allow_ollama_backup", False))
    ollama_policy = _sdk_ollama_policy_mode()
    ollama_blocked = False
    if selected_ami == SDK_OLLAMA_AMI:
        if ollama_policy == "off":
            ollama_blocked = True
        elif ollama_policy == "backup" and not backup_requested:
            ollama_blocked = True
    if ollama_blocked:
        selected_ami = _sdk_default_ami()

    normalized_payload = payload_dict
    local_result = _local_backend_execute(selected_ami, str(action or "").strip(), normalized_payload)
    return {
        "success": True,
        "status": "AMIPI_ROUTE_EXECUTED_LOCAL",
        "backend_ami": selected_ami,
        "record": build_amipi_dispatch_record(
            selected_ami,
            action,
            payload=normalized_payload,
            correlation_id=correlation_id,
            machine_profile=machine_profile,
            mode=mode,
        ),
        "local_result": local_result,
        "policy": {
            "ollama_enabled": _sdk_ollama_enabled(),
            "ollama_policy": ollama_policy,
            "backup_requested": backup_requested,
            "ollama_blocked": ollama_blocked,
            "selected_ami": selected_ami,
        },
        "note": "AMIPI local backend dispatch executed through deterministic SDK adapter.",
    }


def build_sdk_header(protocol: str, action: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """BuceyShunt-compliant header shape for SDK-to-CONTROL dispatch metadata."""
    import uuid as _uuid
    from datetime import datetime as _dt, timezone as _tz
    envelope = dict(payload or {})
    return {
        "shunt_id": str(envelope.get("shunt_id") or _uuid.uuid4()),
        "source_pillar": "SDK",
        "target_pillar": "CONTROL",
        "timestamp": envelope.get("timestamp") or _dt.now(_tz.utc).isoformat(),
        "intent": action,
        "payload": envelope,
        "context_tags": list(envelope.get("context_tags") or []),
        "requires_response": bool(envelope.get("requires_response", True)),
        "sdk_protocol": protocol,
        "document_context": _normalize_document_context(envelope),
        "ami_id": envelope.get("ami_id") or SDK_INTERNAL_AMI_LANES.get(str(protocol or "").strip().lower(), ""),
        "correlation_id": envelope.get("correlation_id", ""),
        "machine_profile": envelope.get("machine_profile") or envelope.get("profile_ref") or {},
        "mode": envelope.get("mode", "interactive"),
        "status": "HEADER_READY",
    }


def dispatch_sdk_protocol(protocol: str, action: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Deterministic adapter dispatch surface for Gen1 SDK protocol lanes."""
    normalized_protocol = str(protocol or "").strip().lower()
    header = build_sdk_header(protocol, action, payload)
    if normalized_protocol in {"device", "arm", "server", "ide", "special_case", "tv", "android", "ios"}:
        payload_dict = dict(payload or {})
        local_result = _local_backend_execute(
            backend_ami=str(header.get("ami_id") or next(iter(SDK_INTERNAL_AMI_LANES.values()), "")),
            action=str(action or "").strip(),
            payload=payload_dict,
        )
        action_l = str(action or "").strip().lower()
        if action_l in {"install_micro_ai", "prepare_install", "install_plan"}:
            installer_mod = _load_micro_ai_installer_sdk()
            if installer_mod is not None and hasattr(installer_mod, "apply_micro_ai_install_dry_run"):
                install_target = str(payload_dict.get("install_target") or normalized_protocol)
                install_dry_run = installer_mod.apply_micro_ai_install_dry_run(
                    target=install_target,
                    payload=payload_dict,
                    machine_profile=header.get("machine_profile") if isinstance(header.get("machine_profile"), dict) else {},
                )
                local_result["install_dry_run"] = install_dry_run
        return {
            "success": True,
            "status": "ADAPTER_EXECUTED_LOCAL",
            "protocol": normalized_protocol,
            "action": str(action or "").strip(),
            "header": header,
            "ami_id": header.get("ami_id", ""),
            "correlation_id": header.get("correlation_id", ""),
            "amipi_ready": normalized_protocol in SDK_INTERNAL_AMI_LANES,
            "local_result": local_result,
            "note": "Executed by deterministic SDK adapter without route ownership.",
        }
    return {
        "success": False,
        "status": "NOT_IMPLEMENTED",
        "protocol": normalized_protocol,
        "action": str(action or "").strip(),
        "header": header,
        "ami_id": header.get("ami_id", ""),
        "correlation_id": header.get("correlation_id", ""),
        "amipi_ready": normalized_protocol in SDK_INTERNAL_AMI_LANES,
        "note": "SDK runtime behavior has not been implemented yet, but Gen1 AMIPI routing metadata is now present.",
    }


def device_protocol(action: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return dispatch_sdk_protocol("device", action, payload)


def arms_protocol(action: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return dispatch_sdk_protocol("arm", action, payload)


def server_protocol(action: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return dispatch_sdk_protocol("server", action, payload)


def ide_protocol(action: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return dispatch_sdk_protocol("ide", action, payload)


class SaraSdkGen1:
    """Minimal wrapper for future Gen1 SDK expansion."""

    def __init__(self) -> None:
        self.pillar = SDK_PILLAR_NAME
        self.version = SDK_VERSION

    def status(self) -> Dict[str, Any]:
        return sdk_status()

    def dispatch(self, protocol: str, action: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return dispatch_sdk_protocol(protocol, action, payload)

    def dispatch_amipi(self, backend_ami: str, action: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return dispatch_amipi_backend(backend_ami, action, payload)


__all__ = [
    "SDK_PILLAR_NAME",
    "SDK_VERSION",
    "SDK_PROTOCOL_LANES",
    "SDK_INTERNAL_AMI_LANES",
    "SDKRequest",
    "SaraSdkGen1",
    "sdk_identity_catalog",
    "sdk_status",
    "build_amipi_dispatch_record",
    "dispatch_amipi_backend",
    "build_sdk_header",
    "dispatch_sdk_protocol",
    "device_protocol",
    "arms_protocol",
    "server_protocol",
    "ide_protocol",
]


# --- Artifact JSON writers (result.meta.json, distant_end.json, master_result.json) ---
def _write_sdk_artifacts(status: str, reached: bool, reason: str) -> None:
    """Write/update the three pillar artifact JSON files for SDK."""
    import json as _json
    from datetime import datetime as _dt, timezone as _tz
    _here = os.path.dirname(os.path.abspath(__file__))
    _local = {
        "pillar": "sara_sdk",
        "file": "Sara_sdk.gen1.py",
        "status": status,
        "reached": reached,
        "reason": reason,
        "updated_at": _dt.now(_tz.utc).isoformat(),
    }
    _distant = {
        "pillar": "sara_sdk",
        "file": "Sara_sdk.gen1.py",
        "status": status,
        "reached": reached,
        "note": reason,
        "updated_at": _dt.now(_tz.utc).isoformat(),
    }
    _master = {"pillar": "sara_sdk", "final_status": status, "local": _local, "distant": _distant}
    for fname, obj in [("result.meta.json", _local), ("distant_end.json", _distant), ("master_result.json", _master)]:
        try:
            with open(os.path.join(_here, fname), "w", encoding="utf-8") as f:
                _json.dump(obj, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

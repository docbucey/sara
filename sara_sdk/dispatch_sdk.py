"""SDK Dispatch: main protocol dispatch, AMIPI backend routing, and header building."""
from __future__ import annotations

import os
import importlib.util
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

try:
    from sara_sdk.identity_sdk import SDK_INTERNAL_AMI_LANES
except ImportError:
    from .identity_sdk import SDK_INTERNAL_AMI_LANES

try:
    from sara_sdk.ollama_sdk import _sdk_ollama_enabled, _sdk_ollama_policy_mode, _sdk_default_ami
except ImportError:
    from .ollama_sdk import _sdk_ollama_enabled, _sdk_ollama_policy_mode, _sdk_default_ami

SDK_OLLAMA_AMI = SDK_INTERNAL_AMI_LANES["ollama_local"]


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
    from sara_sdk.ai_backend_sdk import ai_backend

    doc_ctx = _normalize_document_context(payload)
    response: Dict[str, Any] = {
        "backend_ami": backend_ami,
        "action": action,
        "document_context": doc_ctx,
        "advisory": True,
    }

    if str(action).strip().lower() in {"amipi.invoke", "local.ai.route", "internal_ai.route"}:
        prompt = str(
            payload.get("prompt")
            or payload.get("text")
            or payload.get("input")
            or payload.get("goal")
            or ""
        ).strip()
        if prompt:
            context = {
                "model": payload.get("model"),
                "system_prompt": payload.get("system_prompt"),
            }
            text = ai_backend.ask(prompt, context=context)
            response["text"] = text
            response["response"] = text
        else:
            response["text"] = "[No prompt provided in payload]"
    else:
        response["text"] = "Local adapter accepted request."
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
    envelope = dict(payload or {})
    return {
        "shunt_id": str(envelope.get("shunt_id") or uuid.uuid4()),
        "source_pillar": "SDK",
        "target_pillar": "CONTROL",
        "timestamp": envelope.get("timestamp") or datetime.now(timezone.utc).isoformat(),
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

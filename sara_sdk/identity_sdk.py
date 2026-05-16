"""SDK Identity: identity lane catalog, request shape, and status."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

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

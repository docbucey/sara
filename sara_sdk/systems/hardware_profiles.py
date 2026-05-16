"""Hardware profile stubs for SARA SDK Gen1."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


DEFAULT_SDK_MACHINE_PROFILE: Dict[str, Any] = {
    "status": "consumer_stub",
    "profile_id": "default_local_machine",
    "profile_version": "v1",
    "hardware_class": "pc",
    "ownership": "CORE",
    "note": "SDK consumes machine profiles but does not own canonical profile resolution.",
}


def list_hardware_profiles() -> List[Dict[str, Any]]:
    """Return placeholder hardware profile metadata."""
    return [
        {
            **DEFAULT_SDK_MACHINE_PROFILE,
            "profile": "default_pc_server",
            "target": "pc",
            "continuity_tier": "balanced",
        },
        {
            **DEFAULT_SDK_MACHINE_PROFILE,
            "profile": "default_arm_edge",
            "hardware_class": "arm",
            "target": "arm",
            "continuity_tier": "compact",
        },
        {
            **DEFAULT_SDK_MACHINE_PROFILE,
            "profile": "default_wearable",
            "hardware_class": "wearable",
            "target": "wearable",
            "continuity_tier": "compact",
        },
        {
            **DEFAULT_SDK_MACHINE_PROFILE,
            "profile": "default_tv",
            "hardware_class": "tv",
            "target": "tv",
            "continuity_tier": "balanced",
        },
        {
            **DEFAULT_SDK_MACHINE_PROFILE,
            "profile": "default_backend_os",
            "hardware_class": "server",
            "target": "backend_os",
            "continuity_tier": "extended",
        },
    ]


def resolve_hardware_profile_reference(profile_ref: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Return an SDK-safe machine profile reference while keeping CORE as the owner of profile truth."""
    resolved = dict(DEFAULT_SDK_MACHINE_PROFILE)
    if isinstance(profile_ref, dict):
        resolved.update({k: v for k, v in profile_ref.items() if v is not None})
    return resolved

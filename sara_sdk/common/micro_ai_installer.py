"""Unified micro-AI install planner for SARA SDK Gen1 targets."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict
import copy
import uuid


TARGET_PROFILE_PRESETS: Dict[str, Dict[str, Any]] = {
    "wearable": {
        "runtime_class": "ultra_light",
        "min_ram_mb": 256,
        "storage_budget_mb": 256,
        "continuity_tier": "compact",
        "inference_mode": "stable_probabilistic",
    },
    "arm": {
        "runtime_class": "edge_light",
        "min_ram_mb": 512,
        "storage_budget_mb": 1024,
        "continuity_tier": "compact",
        "inference_mode": "stable_probabilistic",
    },
    "tv": {
        "runtime_class": "edge_balanced",
        "min_ram_mb": 1024,
        "storage_budget_mb": 2048,
        "continuity_tier": "balanced",
        "inference_mode": "stable_probabilistic",
    },
    "pc": {
        "runtime_class": "balanced",
        "min_ram_mb": 2048,
        "storage_budget_mb": 4096,
        "continuity_tier": "balanced",
        "inference_mode": "creative_probabilistic",
    },
    "server": {
        "runtime_class": "service",
        "min_ram_mb": 4096,
        "storage_budget_mb": 8192,
        "continuity_tier": "extended",
        "inference_mode": "stable_probabilistic",
    },
    "android": {
        "runtime_class": "edge_light",
        "min_ram_mb": 512,
        "storage_budget_mb": 1024,
        "continuity_tier": "compact",
        "inference_mode": "stable_probabilistic",
    },
    "ios": {
        "runtime_class": "edge_light",
        "min_ram_mb": 512,
        "storage_budget_mb": 1024,
        "continuity_tier": "compact",
        "inference_mode": "stable_probabilistic",
    },
    "backend_os": {
        "runtime_class": "service",
        "min_ram_mb": 1024,
        "storage_budget_mb": 2048,
        "continuity_tier": "balanced",
        "inference_mode": "stable_probabilistic",
    },
}

TARGET_ALIASES: Dict[str, str] = {
    "laptop": "pc",
    "desktop": "pc",
    "wear": "wearable",
    "watch": "wearable",
    "arm_board": "arm",
    "backend": "backend_os",
}


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical_target(target: str) -> str:
    t = str(target or "").strip().lower()
    if not t:
        return "pc"
    return TARGET_ALIASES.get(t, t)


def _choose_profile(target: str, payload: Dict[str, Any], machine_profile: Dict[str, Any]) -> Dict[str, Any]:
    canonical = _canonical_target(target)
    base = copy.deepcopy(TARGET_PROFILE_PRESETS.get(canonical, TARGET_PROFILE_PRESETS["pc"]))

    requested_tier = str(payload.get("continuity_tier") or machine_profile.get("continuity_tier") or "").strip().lower()
    if requested_tier in {"compact", "balanced", "extended"}:
        base["continuity_tier"] = requested_tier

    if bool(payload.get("requires_repeatability", False)):
        base["inference_mode"] = "strict_deterministic"

    ram_mb = int(payload.get("ram_mb") or machine_profile.get("ram_mb") or 0)
    storage_mb = int(payload.get("storage_mb") or machine_profile.get("storage_mb") or 0)
    if ram_mb and ram_mb < base["min_ram_mb"]:
        base["runtime_class"] = "ultra_light"
        base["inference_mode"] = "strict_deterministic"
    if storage_mb and storage_mb < base["storage_budget_mb"]:
        base["continuity_tier"] = "compact"

    base["target"] = canonical
    return base


def plan_micro_ai_install(
    target: str,
    payload: Dict[str, Any] | None = None,
    machine_profile: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    payload = dict(payload or {})
    machine_profile = dict(machine_profile or {})

    profile = _choose_profile(target=target, payload=payload, machine_profile=machine_profile)
    plan_id = str(uuid.uuid4())

    return {
        "success": True,
        "status": "INSTALL_PLAN_READY",
        "plan_id": plan_id,
        "created_at": _iso_now(),
        "target": profile["target"],
        "runtime_profile": profile,
        "steps": [
            "detect_host_capabilities",
            "provision_micro_ai_runtime",
            "apply_continuity_profile",
            "enable_replay_ledger",
            "bind_control_mama_sdk",
            "run_post_install_self_check",
        ],
        "post_install": {
            "replay_mode_default": True,
            "ollama_policy_default": "backup",
            "self_tuning": True,
        },
        "note": "Plan is dry-run safe and intended for host-adaptive micro-AI installation.",
    }


def apply_micro_ai_install_dry_run(
    target: str,
    payload: Dict[str, Any] | None = None,
    machine_profile: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    plan = plan_micro_ai_install(target=target, payload=payload, machine_profile=machine_profile)
    return {
        "success": True,
        "status": "INSTALL_DRY_RUN_COMPLETE",
        "plan": plan,
        "artifacts": {
            "runtime_dir": "<host>/sara_micro_ai/runtime",
            "continuity_dir": "<host>/sara_micro_ai/continuity",
            "ledger_path": "<host>/sara_micro_ai/logs/plainjain_replay_ledger.ndjson",
        },
    }

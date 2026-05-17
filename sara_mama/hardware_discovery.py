"""
sara_mama/hardware_discovery.py

SARA MAMA — Hardware discovery orchestrator.

MAMA owns the human interface layer.  When SARA starts, MAMA needs to know
what physical input devices are present so it can adapt accordingly.

Five-pillar pipeline
────────────────────
  SDK      enumerate_hardware() + fetch_device_spec() + build_default_mapping()
             └─ classifies HMI devices, pre-maps HOTAS / joysticks as 3D mice
  SECURITY  paladin_scan → sanitize device names against injection
             sheriff_audit → writes hardware_discovery audit event to logs
  MAMA      (this file) orchestrates; presents results; owns the entry point
  CONTROL   receives the finished profile via BuceyShunt HTTP POST
             └─ _cmd_input_device_profile writes machine_profile.json + NBS
  CORE      persists via CONTROL (CONTROL is sole routing authority to CORE)

Usage
─────
  # Standalone (runs once, prints JSON)
  python -m sara_mama.hardware_discovery [output_path] [--offline]

  # From another module
  from sara_mama.hardware_discovery import discover
  profile = discover()
"""
from __future__ import annotations

import json
import os
import platform
import re
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# ── Pillar imports (all graceful — discovery still works fully offline/isolated)

# SDK — enumerates hardware, fetches specs, builds 3D-mouse mappings
try:
    from sara_sdk.systems.hardware_profiles import (
        build_device_entry,
        enumerate_hardware,
    )
    _SDK_OK = True
except ImportError:
    try:
        import importlib.util, pathlib
        _hw_path = pathlib.Path(__file__).resolve().parents[1] / "sara_sdk" / "systems" / "hardware_profiles.py"
        _spec = importlib.util.spec_from_file_location("sara_sdk_hw", str(_hw_path))
        _hw_mod = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(_hw_mod)
        enumerate_hardware = _hw_mod.enumerate_hardware
        build_device_entry = _hw_mod.build_device_entry
        _SDK_OK = True
    except Exception:
        _SDK_OK = False
        def enumerate_hardware():  # type: ignore[misc]
            return []
        def build_device_entry(raw, fetch_web=True):  # type: ignore[misc]
            return {**raw, "category": "other", "is_hmi": False, "sara_device_role": "unassigned"}

# SECURITY — paladin scan + sheriff audit
_paladin_scan   = None
_sheriff_audit  = None
try:
    from sara_security.dispatch_sec import dispatch_security as _dispatch_sec
    def _paladin_scan(text: str) -> Dict[str, Any]:
        return _dispatch_sec("paladin_scan", text=text)
except ImportError:
    pass

try:
    from sara_security.sheriff import sheriff_audit as _sheriff_audit_fn
    _sheriff_audit = _sheriff_audit_fn
except ImportError:
    pass

# ── CONTROL shunt endpoint ────────────────────────────────────────────────────
# CONTROL is sole routing authority.  We POST a BuceyShunt envelope here;
# CONTROL's _cmd_input_device_profile handler writes machine_profile.json
# and appends to the NBS narrative — that is the CORE persistence path.

def _control_base_url() -> str:
    host = os.environ.get("SARA_HOST", "127.0.0.1:5050")
    if not host.startswith("http"):
        host = f"http://{host}"
    return host.rstrip("/")


def _shunt_to_control(profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    POST the hardware profile to CONTROL via BuceyShunt HTTP.
    CONTROL routes it to CORE for NBS persistence.
    Returns the CONTROL response dict (or error dict if unreachable).
    """
    envelope = {
        "intent":  "input_device_profile",
        "act":     "00",
        "source":  "MAMA",
        "target":  "CONTROL",
        "payload": profile,
    }
    url  = f"{_control_base_url()}/shunt"
    body = json.dumps(envelope).encode("utf-8")
    try:
        req = urllib.request.Request(
            url, data=body,
            headers={"Content-Type": "application/json", "User-Agent": "SARA-MAMA/1.0"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            return json.loads(resp.read().decode("utf-8", errors="replace"))
    except urllib.error.URLError as exc:
        return {"success": False, "error": f"CONTROL unreachable: {exc}"}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


# ── SECURITY helpers ──────────────────────────────────────────────────────────

_INJECT_PATTERN = re.compile(r"[<>{};`$|&\x00-\x1f]")

def _sanitize_name(name: str) -> str:
    """Strip characters that could be used for injection from a device name."""
    return _INJECT_PATTERN.sub("", name).strip()[:128]


def _security_gate(profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    SECURITY pillar gate.
    1. Sanitize all device name strings.
    2. Paladin scan the concatenated names for hostile signatures.
    3. Sheriff audit the discovery event.
    Returns the (possibly sanitized) profile.
    """
    # Sanitize
    for device in profile.get("devices", []):
        if isinstance(device.get("name"), str):
            device["name"] = _sanitize_name(device["name"])

    # Paladin scan
    scan_text = " | ".join(
        d.get("name", "") for d in profile.get("devices", [])
    )
    paladin_result: Dict[str, Any] = {"result": {"allowed": True, "reason": "SEC:LOCAL_SANITIZE_ONLY"}}
    if _paladin_scan is not None:
        try:
            paladin_result = _paladin_scan(scan_text) or paladin_result
        except Exception:
            pass

    profile["_security"] = {
        "paladin": paladin_result.get("result", {}),
        "sanitized": True,
    }

    # Sheriff audit
    if _sheriff_audit is not None:
        try:
            _sheriff_audit(
                event_type="hardware_discovery",
                actor="sara_mama.hardware_discovery",
                decision=paladin_result.get("result", {}).get("allowed", True),
                reason=paladin_result.get("result", {}).get("reason", "ok"),
                details={
                    "device_count": profile.get("device_count", 0),
                    "hmi_count":    profile.get("hmi_count", 0),
                    "machine_id":   profile.get("machine_id", ""),
                },
            )
        except Exception:
            pass

    return profile


# ── Profile Assembly ──────────────────────────────────────────────────────────

def _machine_id() -> str:
    try:
        return f"{socket.gethostname()}_{platform.node()}"
    except Exception:
        return "unknown_machine"


def _build_profile(raw_devices: List[Dict[str, Any]], fetch_web: bool) -> Dict[str, Any]:
    device_entries: List[Dict[str, Any]] = []
    for raw in raw_devices:
        try:
            entry = build_device_entry(raw, fetch_web=fetch_web)
            device_entries.append(entry)
        except Exception as exc:
            device_entries.append({
                "name":     raw.get("name", "unknown"),
                "category": "error",
                "error":    str(exc),
                "is_hmi":   False,
            })

    hmi_devices = [d for d in device_entries if d.get("is_hmi")]

    return {
        "schema":        "sara_machine_profile_v2",
        "generated_by":  "sara_mama.hardware_discovery",
        "machine_id":    _machine_id(),
        "os":            platform.platform(),
        "scan_time":     datetime.now(timezone.utc).isoformat(),
        "sdk_available": _SDK_OK,
        "device_count":  len(device_entries),
        "hmi_count":     len(hmi_devices),
        "devices":       device_entries,
        # Quick-reference summary of HMI devices for MAMA / VALANCE UI
        "hmi_summary": [
            {
                "name":         d["name"],
                "category":     d["category"],
                "manufacturer": d.get("spec", {}).get("manufacturer", ""),
                "spec_source":  d.get("spec", {}).get("spec_source", "unknown"),
                "buttons":      d.get("spec", {}).get("buttons", 0),
                "axes":         d.get("spec", {}).get("axes", []),
                "povs":         d.get("spec", {}).get("povs", 0),
                "mapping_type": d.get("default_mapping", {}).get("mapping_type", ""),
                "sara_device_role": d.get("sara_device_role", "unassigned"),
            }
            for d in hmi_devices
        ],
    }


# ── Main Entry Point ──────────────────────────────────────────────────────────

def discover(
    output_path: Optional[str] = None,
    fetch_web: bool = True,
    route_to_control: bool = True,
) -> Dict[str, Any]:
    """
    Discover all hardware on the local terminal.

    Pipeline
    --------
    SDK      → enumerate + classify + fetch specs + pre-map HMI as 3D mouse
    SECURITY → sanitize device names, paladin scan, sheriff audit
    MAMA     → assemble profile (this function)
    CONTROL  → shunt profile to NBS via HTTP (route_to_control=True by default)
    CORE     → persists via CONTROL's _cmd_input_device_profile handler

    :param output_path:       If set, also write machine_profile.json here locally.
    :param fetch_web:         If False, skip web spec lookups (fully offline mode).
    :param route_to_control:  If False, skip the CONTROL shunt (useful for unit tests).
    :return:                  Complete machine profile dict.
    """
    # ── SDK: enumerate hardware ───────────────────────────────────────────────
    raw_devices = enumerate_hardware()

    # ── MAMA: assemble structured profile ────────────────────────────────────
    profile = _build_profile(raw_devices, fetch_web=fetch_web)

    # ── SECURITY: sanitize + audit ────────────────────────────────────────────
    profile = _security_gate(profile)

    # ── optional local write (before shunting so it survives CONTROL being down)
    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        _safe = {k: v for k, v in profile.items() if not k.startswith("_")}
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(_safe, f, indent=2, ensure_ascii=False)

    # ── CONTROL → CORE: shunt profile through routing authority ──────────────
    if route_to_control:
        ctrl_result = _shunt_to_control(profile)
        profile["_control_route"] = ctrl_result

    return profile


# ── CLI entry ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    _out     = next((a for a in sys.argv[1:] if not a.startswith("--")), None)
    _offline = "--offline" in sys.argv
    _no_ctrl = "--no-control" in sys.argv

    result = discover(
        output_path=_out,
        fetch_web=not _offline,
        route_to_control=not _no_ctrl,
    )

    # Print without internal _keys
    print(json.dumps({k: v for k, v in result.items() if not k.startswith("_")}, indent=2))

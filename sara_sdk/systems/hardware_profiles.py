"""
sara_sdk/systems/hardware_profiles.py

SARA SDK — Hardware profile adapter for the local terminal.

SDK role: enumerate + classify + spec-fetch + pre-map.
This module does the platform-specific heavy lifting so MAMA can orchestrate
without knowing anything about OS APIs or web fetching.

Does NOT persist. Does NOT route. Does NOT audit.
MAMA calls this; SECURITY validates; CONTROL routes; CORE persists.
"""
from __future__ import annotations

import json
import platform
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

# ── HMI classification keywords ──────────────────────────────────────────────
# These trigger 3D-mouse treatment (full 6-DOF spatial input)
_HMI_3D_KEYWORDS: List[str] = [
    "hotas", "flight stick", "flightstick", "joystick",
    "rudder pedals", "rudder", "yoke", "flight controller",
    "t.flight", "t-flight", "tflight",
    "warthog", "cougar", "viper tqs",
    "x52", "x55", "x56",
    "extreme 3d", "force 3d",
    "pro flight", "pro-flight",
    "fighterstick", "combat stick", "aviator",
    "gladiator", "gunfighter", "black mamba",
    "vkb", "virpil", "winwing", "deltasim",
    "ch fighterstick", "ch pro throttle", "ch eclipse",
    "saitek", "twist of", "twist grip",
    "t16000m", "t.16000m", "tfcs throttle",
]

_GAMEPAD_KEYWORDS: List[str] = [
    "gamepad", "controller", "dualshock", "dual shock",
    "xbox", "xinput", "x-input",
    "playstation", "ds4", "ds5",
    "switch pro", "steam controller", "8bitdo",
    "rumble pad", "rumblepad",
    "logitech f310", "logitech f710", "logitech f510",
]

# ── Windows device class GUIDs (without braces, lowercase) ───────────────────
_GUID_HID      = "745a17a0-74d3-11d0-b6fe-00a0c90f57da"
_GUID_KEYBOARD = "4d36e96b-e325-11ce-bfc1-08002be10318"
_GUID_MOUSE    = "4d36e96f-e325-11ce-bfc1-08002be10318"
_GUID_DISPLAY  = "4d36e968-e325-11ce-bfc1-08002be10318"
_GUID_DISK     = "4d36e967-e325-11ce-bfc1-08002be10318"
_GUID_AUDIO    = "4d36e96c-e325-11ce-bfc1-08002be10318"
_GUID_NET      = "4d36e972-e325-11ce-bfc1-08002be10318"

# ── Known-device spec table ───────────────────────────────────────────────────
# Keyed by lowercase name fragment → spec dict.  Fast path: no web fetch needed.
_KNOWN_SPECS: Dict[str, Dict[str, Any]] = {
    # ── Thrustmaster ──────────────────────────────────────────────────────────
    "t.flight hotas x":    {"buttons": 14, "axes": ["X","Y","Z","RZ","Slider0"],
                            "povs": 1, "hmi_class": "hotas", "manufacturer": "Thrustmaster"},
    "t-flight hotas x":    {"buttons": 14, "axes": ["X","Y","Z","RZ","Slider0"],
                            "povs": 1, "hmi_class": "hotas", "manufacturer": "Thrustmaster"},
    "hotas warthog":       {"buttons": 19, "axes": ["X","Y","Z","RZ","Slider0","Slider1"],
                            "povs": 1, "hmi_class": "hotas", "manufacturer": "Thrustmaster"},
    "hotas cougar":        {"buttons": 19, "axes": ["X","Y","Z","RZ"],
                            "povs": 1, "hmi_class": "hotas", "manufacturer": "Thrustmaster"},
    "viper tqs":           {"buttons": 16, "axes": ["X","Y","Z","RX","RY","RZ","Slider0"],
                            "povs": 1, "hmi_class": "hotas", "manufacturer": "Thrustmaster"},
    "t16000m":             {"buttons": 16, "axes": ["X","Y","Z","RZ"],
                            "povs": 1, "hmi_class": "joystick", "manufacturer": "Thrustmaster"},
    "t.16000m":            {"buttons": 16, "axes": ["X","Y","Z","RZ"],
                            "povs": 1, "hmi_class": "joystick", "manufacturer": "Thrustmaster"},
    "tfcs":                {"buttons": 5,  "axes": ["X","Y","Z","RZ"],
                            "povs": 0, "hmi_class": "joystick", "manufacturer": "Thrustmaster"},
    # ── Logitech / Saitek ─────────────────────────────────────────────────────
    "extreme 3d pro":      {"buttons": 12, "axes": ["X","Y","Z","RZ"],
                            "povs": 1, "hmi_class": "joystick", "manufacturer": "Logitech"},
    "force 3d pro":        {"buttons": 12, "axes": ["X","Y","Z","RZ"],
                            "povs": 1, "hmi_class": "joystick", "manufacturer": "Logitech"},
    "x52 pro":             {"buttons": 32, "axes": ["X","Y","Z","RX","RY","RZ","Slider0","Slider1"],
                            "povs": 2, "hmi_class": "hotas", "manufacturer": "Logitech/Saitek"},
    "x52":                 {"buttons": 24, "axes": ["X","Y","Z","RX","RY","RZ","Slider0","Slider1"],
                            "povs": 2, "hmi_class": "hotas", "manufacturer": "Logitech/Saitek"},
    "x55":                 {"buttons": 32, "axes": ["X","Y","Z","RX","RY","RZ","Slider0","Slider1"],
                            "povs": 3, "hmi_class": "hotas", "manufacturer": "Saitek"},
    "x56":                 {"buttons": 32, "axes": ["X","Y","Z","RX","RY","RZ","Slider0","Slider1"],
                            "povs": 3, "hmi_class": "hotas", "manufacturer": "Logitech"},
    "pro flight yoke":     {"buttons": 14, "axes": ["X","Y","Z","RZ"],
                            "povs": 1, "hmi_class": "yoke", "manufacturer": "Logitech"},
    "pro flight rudder":   {"buttons": 3,  "axes": ["X","RZ"],
                            "povs": 0, "hmi_class": "rudder", "manufacturer": "Logitech"},
    # ── CH Products ───────────────────────────────────────────────────────────
    "ch fighterstick":     {"buttons": 24, "axes": ["X","Y","Z","RZ"],
                            "povs": 4, "hmi_class": "joystick", "manufacturer": "CH Products"},
    "ch pro throttle":     {"buttons": 18, "axes": ["Z","Slider0"],
                            "povs": 1, "hmi_class": "throttle", "manufacturer": "CH Products"},
    "ch eclipse":          {"buttons": 10, "axes": ["X","Y","Z"],
                            "povs": 1, "hmi_class": "joystick", "manufacturer": "CH Products"},
    # ── VKB ───────────────────────────────────────────────────────────────────
    "gladiator nxt":       {"buttons": 20, "axes": ["X","Y","Z","RZ"],
                            "povs": 2, "hmi_class": "joystick", "manufacturer": "VKB"},
    "gunfighter":          {"buttons": 20, "axes": ["X","Y","Z","RZ"],
                            "povs": 2, "hmi_class": "joystick", "manufacturer": "VKB"},
    # ── Virpil ────────────────────────────────────────────────────────────────
    "virpil":              {"buttons": 28, "axes": ["X","Y","Z","RX","RY","RZ","Slider0"],
                            "povs": 2, "hmi_class": "hotas", "manufacturer": "Virpil"},
    # ── WinWing ───────────────────────────────────────────────────────────────
    "winwing":             {"buttons": 32, "axes": ["X","Y","Z","RX","RY","RZ","Slider0","Slider1"],
                            "povs": 2, "hmi_class": "hotas", "manufacturer": "WinWing"},
    # ── Microsoft ─────────────────────────────────────────────────────────────
    "sidewinder precision":{"buttons": 8,  "axes": ["X","Y","Z","RZ"],
                            "povs": 1, "hmi_class": "joystick", "manufacturer": "Microsoft"},
    "microsoft sidewinder":{"buttons": 8,  "axes": ["X","Y","Z","RZ"],
                            "povs": 1, "hmi_class": "joystick", "manufacturer": "Microsoft"},
}

# ── 3D-mouse axis pre-map (HOTAS / joystick / flight stick) ──────────────────
# These are the SARA input roles when the device is treated as a spatial 3D mouse.
AXIS_MAP_3D_MOUSE: Dict[str, Dict[str, str]] = {
    "X":       {"sara_role": "look_horizontal",  "description": "Left/right pan or look"},
    "Y":       {"sara_role": "look_vertical",    "description": "Up/down pan or look"},
    "Z":       {"sara_role": "zoom_depth",       "description": "Twist / depth / zoom"},
    "RX":      {"sara_role": "tilt_roll",        "description": "Roll / bank"},
    "RY":      {"sara_role": "tilt_pitch",       "description": "Pitch"},
    "RZ":      {"sara_role": "yaw_rotate",       "description": "Rudder / yaw rotation"},
    "Slider0": {"sara_role": "throttle_speed",   "description": "Primary throttle / speed"},
    "Slider1": {"sara_role": "aux_throttle",     "description": "Secondary throttle / mixture"},
}

POV_MAP_3D_MOUSE: Dict[str, Dict[str, str]] = {
    "POV0_N": {"sara_role": "dpad_up",    "description": "View hat North"},
    "POV0_E": {"sara_role": "dpad_right", "description": "View hat East"},
    "POV0_S": {"sara_role": "dpad_down",  "description": "View hat South"},
    "POV0_W": {"sara_role": "dpad_left",  "description": "View hat West"},
}

BUTTON_ROLE_HINTS: Dict[int, Dict[str, str]] = {
    0: {"sara_role": "primary_action",   "description": "Trigger / primary fire"},
    1: {"sara_role": "secondary_action", "description": "Thumb / secondary"},
    2: {"sara_role": "tertiary_action",  "description": "Button 3"},
    3: {"sara_role": "menu_toggle",      "description": "Menu / start"},
}

# Gamepad axis pre-map
AXIS_MAP_GAMEPAD: Dict[str, Dict[str, str]] = {
    "X":       {"sara_role": "left_stick_x",   "description": "Left stick horizontal"},
    "Y":       {"sara_role": "left_stick_y",   "description": "Left stick vertical"},
    "Z":       {"sara_role": "right_stick_x",  "description": "Right stick horizontal"},
    "RZ":      {"sara_role": "right_stick_y",  "description": "Right stick vertical"},
    "Slider0": {"sara_role": "left_trigger",   "description": "Left analog trigger"},
    "Slider1": {"sara_role": "right_trigger",  "description": "Right analog trigger"},
}

# ── OS Hardware Enumeration ───────────────────────────────────────────────────

def _run_powershell(script: str, timeout: int = 15) -> Optional[str]:
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
            capture_output=True, text=True, timeout=timeout,
        )
        return r.stdout.strip() if r.returncode == 0 else None
    except Exception:
        return None


def _enumerate_windows() -> List[Dict[str, Any]]:
    """Query Windows PnP database via PowerShell Get-PnpDevice."""
    script = (
        "Get-PnpDevice -Status OK "
        "| Select-Object -Property FriendlyName,InstanceId,Class,ClassGuid "
        "| ConvertTo-Json -Depth 3"
    )
    output = _run_powershell(script)
    if not output:
        return []
    try:
        raw = json.loads(output)
    except json.JSONDecodeError:
        return []
    if isinstance(raw, dict):
        raw = [raw]
    devices = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        name = (item.get("FriendlyName") or "").strip()
        if not name:
            continue
        devices.append({
            "name":         name,
            "instance_id":  (item.get("InstanceId")  or "").strip(),
            "device_class": (item.get("Class")        or "").strip(),
            "class_guid":   str(item.get("ClassGuid") or "").strip().lower().strip("{}"),
        })
    return devices


def _enumerate_linux() -> List[Dict[str, Any]]:
    """Enumerate input devices via /proc/bus/input/devices."""
    devices: List[Dict[str, Any]] = []
    try:
        with open("/proc/bus/input/devices", "r") as f:
            content = f.read()
        block: Dict[str, str] = {}
        for line in content.splitlines():
            if line.startswith("N:"):
                m = re.search(r'Name="([^"]+)"', line)
                if m:
                    block["name"] = m.group(1)
            elif line.startswith("H:") and "js" in line.lower():
                block["device_class"] = "HID_Joystick"
            elif line.startswith("H:") and "event" in line.lower():
                block.setdefault("device_class", "HID_Event")
            elif line == "" and block.get("name"):
                devices.append({
                    "name": block["name"], "instance_id": "",
                    "device_class": block.get("device_class", "Input"), "class_guid": "",
                })
                block = {}
    except Exception:
        pass
    return devices


def _enumerate_macos() -> List[Dict[str, Any]]:
    try:
        out = subprocess.check_output(
            ["system_profiler", "SPUSBDataType", "-json"],
            timeout=15, stderr=subprocess.DEVNULL,
        ).decode()
        data = json.loads(out)
        return [
            {"name": item.get("_name", ""), "instance_id": "",
             "device_class": "USB", "class_guid": ""}
            for item in data.get("SPUSBDataType", [])
            if item.get("_name")
        ]
    except Exception:
        return []


def enumerate_hardware() -> List[Dict[str, Any]]:
    """Enumerate all present hardware devices on the local terminal. OS-agnostic."""
    os_name = platform.system().lower()
    if os_name == "windows":
        return _enumerate_windows()
    if os_name == "linux":
        return _enumerate_linux()
    return _enumerate_macos()


# ── Device Classification ─────────────────────────────────────────────────────

def classify_device(name: str, device_class: str, class_guid: str) -> str:
    """
    Return a category string:
      hmi_hotas | hmi_joystick | hmi_gamepad | hmi_rudder | hmi_yoke |
      hmi_throttle | keyboard | mouse | audio | display | storage | network | other
    """
    nl = name.lower()
    gl = class_guid.lower()
    cl = device_class.lower()

    for kw in _HMI_3D_KEYWORDS:
        if kw in nl:
            if "rudder" in nl:   return "hmi_rudder"
            if "yoke"   in nl:   return "hmi_yoke"
            if "hotas"  in nl:   return "hmi_hotas"
            if "throttle" in nl and "stick" not in nl and "joystick" not in nl:
                return "hmi_throttle"
            return "hmi_joystick"

    for kw in _GAMEPAD_KEYWORDS:
        if kw in nl:
            return "hmi_gamepad"

    if gl == _GUID_KEYBOARD or cl == "keyboard": return "keyboard"
    if gl == _GUID_MOUSE    or cl == "mouse" or "mouse" in nl: return "mouse"
    if gl == _GUID_DISPLAY  or cl in ("display", "monitor"):   return "display"
    if gl == _GUID_DISK     or cl in ("diskdrive", "cdrom"):   return "storage"
    if gl == _GUID_AUDIO    or cl in ("media", "audio"):       return "audio"
    if gl == _GUID_NET      or cl in ("net", "network"):       return "network"
    if gl == _GUID_HID      or cl == "hid":                    return "hmi_unknown"
    return "other"


# ── VID / PID Extraction ──────────────────────────────────────────────────────

def extract_vid_pid(instance_id: str) -> Tuple[Optional[str], Optional[str]]:
    m = re.search(r"VID_([0-9A-Fa-f]{4}).*?PID_([0-9A-Fa-f]{4})", instance_id, re.IGNORECASE)
    return (m.group(1).upper(), m.group(2).upper()) if m else (None, None)


# ── Web Spec Lookup ───────────────────────────────────────────────────────────

def _http_get(url: str, timeout: int = 8) -> Optional[str]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SARA-SDK-HW/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            charset = resp.headers.get_content_charset("utf-8")
            return resp.read().decode(charset, errors="replace")
    except Exception:
        return None


def _lookup_known_spec(name: str) -> Optional[Dict[str, Any]]:
    nl = name.lower()
    for key, spec in _KNOWN_SPECS.items():
        if key in nl:
            return dict(spec)
    return None


def _usb_id_lookup(vid: str, pid: str) -> Optional[str]:
    """Ask usb-ids.gowdy.us for a canonical vendor/product name."""
    url  = f"https://usb-ids.gowdy.us/read/UD/{vid.lower()}/{pid.lower()}"
    html = _http_get(url, timeout=6)
    if not html:
        return None
    m = re.search(r"<title>([^<]+)</title>", html, re.IGNORECASE)
    if m:
        title = m.group(1).strip()
        if "\u2014" in title:
            return title.split("\u2014", 1)[-1].strip()
        if "—" in title:
            return title.split("—", 1)[-1].strip()
    return None


def _duckduckgo_spec_search(device_name: str) -> Optional[Dict[str, Any]]:
    """DuckDuckGo instant-answer search for button/axis specs."""
    query = urllib.parse.quote(f"{device_name} specifications buttons axes joystick specs")
    body  = _http_get(f"https://api.duckduckgo.com/?q={query}&format=json&no_redirect=1")
    if not body:
        return None
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return None

    abstract = (data.get("AbstractText") or "").lower()
    if not abstract:
        for topic in data.get("RelatedTopics", []):
            text = (topic.get("Text") or "").lower()
            if "button" in text or "axis" in text or "axes" in text:
                abstract = text
                break

    if not abstract:
        return None

    spec: Dict[str, Any] = {"spec_source": "web_duckduckgo"}
    m = re.search(r"(\d+)\s*(?:programmable\s*)?buttons?", abstract)
    if m:
        spec["buttons"] = int(m.group(1))
    m = re.search(r"(\d+)\s*axes", abstract)
    if m:
        spec["axis_count"] = int(m.group(1))
    return spec if len(spec) > 1 else None


def fetch_device_spec(
    device_name: str,
    vid: Optional[str] = None,
    pid: Optional[str] = None,
    fetch_web: bool = True,
) -> Dict[str, Any]:
    """
    Full spec resolution: known-table → USB-ID lookup → DuckDuckGo search.
    Returns spec dict. spec_source field indicates how it was found.
    """
    # 1 — local known-device table (fastest, no network)
    spec = _lookup_known_spec(device_name)
    if spec:
        spec["spec_source"] = "known_table"
        return spec

    base: Dict[str, Any] = {
        "spec_source": "unknown", "buttons": 0,
        "axes": [], "povs": 0, "hmi_class": "joystick",
    }
    if not fetch_web:
        return base

    # 2 — USB ID lookup for a verified canonical name, then re-check known table
    resolved_name = device_name
    if vid and pid:
        usb_name = _usb_id_lookup(vid, pid)
        if usb_name:
            base["usb_id_name"] = usb_name
            spec = _lookup_known_spec(usb_name)
            if spec:
                spec["spec_source"] = "known_table_via_usbid"
                return spec
            resolved_name = usb_name

    # 3 — DuckDuckGo instant answer
    web = _duckduckgo_spec_search(resolved_name)
    if web:
        base.update(web)

    return base


# ── 3D-Mouse Pre-Mapping Builder ──────────────────────────────────────────────

def build_default_mapping(spec: Dict[str, Any], category: str) -> Dict[str, Any]:
    """
    Build SARA default input mapping treating any joystick/HOTAS/flight stick
    as a 3D mouse: axes → spatial roles, POVs → dpad, buttons → action stubs.
    Gamepad variant uses left/right stick roles instead.
    """
    axes    = spec.get("axes") or list(AXIS_MAP_3D_MOUSE.keys())[:4]
    povs    = spec.get("povs", 0)
    buttons = spec.get("buttons", 0)
    is_pad  = (category == "hmi_gamepad")
    axis_lut = AXIS_MAP_GAMEPAD if is_pad else AXIS_MAP_3D_MOUSE

    mapping: Dict[str, Any] = {
        "mapping_type":  "gamepad" if is_pad else "3d_mouse",
        "hmi_class":     category,
        "axes":          {ax: axis_lut[ax] for ax in axes if ax in axis_lut},
        "unmapped_axes": [ax for ax in axes if ax not in axis_lut],
        "pov_hats":      {},
        "buttons":       {},
        "note":          "Pre-mapped defaults — customize per patient in VALANCE.",
    }

    for i in range(povs):
        for d, suffix in [("N","_N"),("E","_E"),("S","_S"),("W","_W")]:
            key = f"POV{i}{suffix}"
            mapping["pov_hats"][key] = POV_MAP_3D_MOUSE.get(
                f"POV0_{d}",
                {"sara_role": f"pov{i}_{d.lower()}", "description": f"POV{i} {d}"},
            )

    for i in range(buttons):
        mapping["buttons"][f"Button{i + 1}"] = BUTTON_ROLE_HINTS.get(
            i, {"sara_role": f"button_{i + 1}", "description": f"Button {i + 1}"}
        )

    return mapping


# ── Full Device Entry Assembly ────────────────────────────────────────────────

def build_device_entry(raw: Dict[str, Any], fetch_web: bool = True) -> Dict[str, Any]:
    """
    Turn a raw OS device record into a fully classified SARA device profile entry.
    HMI devices get spec resolution and a 3D-mouse default mapping.
    """
    name       = raw["name"]
    instance   = raw.get("instance_id", "")
    dev_class  = raw.get("device_class", "")
    class_guid = raw.get("class_guid", "")

    category   = classify_device(name, dev_class, class_guid)
    vid, pid   = extract_vid_pid(instance)
    is_hmi     = category.startswith("hmi_")

    entry: Dict[str, Any] = {
        "name":            name,
        "instance_id":     instance,
        "os_class":        dev_class,
        "category":        category,
        "vid":             vid,
        "pid":             pid,
        "is_hmi":          is_hmi,
        "sara_device_role": "unassigned",
    }

    if is_hmi:
        spec = fetch_device_spec(name, vid=vid, pid=pid, fetch_web=fetch_web)
        entry["spec"]            = spec
        entry["default_mapping"] = build_default_mapping(spec, category)

    return entry


# ── Backward-compat shims (kept so any existing import of old stubs still works)
DEFAULT_SDK_MACHINE_PROFILE: Dict[str, Any] = {
    "status": "active",
    "profile_id": "sdk_hardware_profiles",
    "profile_version": "v2",
    "hardware_class": "pc",
    "ownership": "MAMA via SDK adapter",
    "note": "Real enumeration via enumerate_hardware() / build_device_entry().",
}

def list_hardware_profiles() -> List[Dict[str, Any]]:
    """Return live enumerated device list (replaces the old static stub)."""
    return [build_device_entry(d, fetch_web=False) for d in enumerate_hardware()]

def resolve_hardware_profile_reference(profile_ref: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    resolved = dict(DEFAULT_SDK_MACHINE_PROFILE)
    if isinstance(profile_ref, dict):
        resolved.update({k: v for k, v in profile_ref.items() if v is not None})
    return resolved

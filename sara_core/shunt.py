"""CORE Shunt: entrypoint and ACT-mapped functions for cross-pillar communication."""
from typing import Any, Dict
from datetime import datetime, timezone
try:
    from sara_common.shunt_header import validate_shunt_header
except ImportError:
    def validate_shunt_header(payload: dict) -> bool:
        required = ["shunt_id", "source_pillar", "target_pillar", "timestamp", "intent", "payload", "context_tags", "requires_response"]
        return all(f in payload for f in required)

import os
import json

# -------------------------
# Constants
# -------------------------

NBS_BASE_DIR: str = os.path.join(os.getcwd(), "nbs_projects")
SYSTEM_CORE_PROJECT_NAME: str = "system_core"

# --- VNCE / CORE command constants ---
CORE_PROTOCOL_VNCE = "vnce"
CORE_CMD_VNCE_SESSION_START = "CORE_VNCE_SESSION_START"
CORE_CMD_VNCE_SESSION_END = "CORE_VNCE_SESSION_END"
CORE_STATE_VNCE_SESSION = "vnce_session_active"

# FSM state and transition table
CORE_FSM_STATES = {
    "idle": 0,
    "processing": 1,
    "done": 2,
    "error": 3,
    CORE_STATE_VNCE_SESSION: 4,
}
CORE_FSM_TRANSITIONS = {
    (0, "start"): (1, "begin_processing"),
    (1, "finish"): (2, "complete"),
    (1, "fail"): (3, "handle_error"),
    (0, CORE_CMD_VNCE_SESSION_START): (4, "emit_vnce_start_envelope"),
    (1, CORE_CMD_VNCE_SESSION_START): (4, "emit_vnce_start_envelope"),
    (4, CORE_CMD_VNCE_SESSION_END): (2, "emit_vnce_end_envelope"),
    (3, "reset"): (0, "reset_idle")
}


# -------------------------
# Functions
# -------------------------

def build_vnce_shunt_envelope(command: str, payload: dict) -> dict:
    """
    Build a CONTROL-bound VNCE shunt envelope from CORE.
    CORE does not validate VNCE content; it only wraps and forwards it.
    """
    import uuid

    inner_payload = payload.get("payload", payload) if isinstance(payload, dict) else {}
    context_tags = list(payload.get("context_tags", [])) if isinstance(payload, dict) else []
    context_tags.extend(["vnce", "envoy", "core-forward"])

    return {
        "shunt_id": str(payload.get("shunt_id") or uuid.uuid4()) if isinstance(payload, dict) else str(uuid.uuid4()),
        "source_pillar": payload.get("source_pillar", "CORE") if isinstance(payload, dict) else "CORE",
        "target_pillar": "CONTROL",
        "timestamp": payload.get("timestamp") if isinstance(payload, dict) and payload.get("timestamp") else datetime.now(timezone.utc).isoformat(),
        "intent": str(command).lower(),
        "payload": inner_payload,
        "context_tags": context_tags,
        "requires_response": payload.get("requires_response", True) if isinstance(payload, dict) else True,
        "protocol": CORE_PROTOCOL_VNCE,
    }


def core_shunt_entrypoint(command: str, payload: dict) -> dict:
    """
    Single entrypoint for all cross-pillar actions. Applies header validation and routes to FSM.
    """
    if not validate_shunt_header(payload):
        return {"success": False, "error": "Invalid shunt header"}

    if command in {CORE_CMD_VNCE_SESSION_START, CORE_CMD_VNCE_SESSION_END}:
        vnce_envelope = build_vnce_shunt_envelope(command, payload)
        return {
            "success": True,
            "command": command,
            "out_route": "CONTROL",
            "protocol": CORE_PROTOCOL_VNCE,
            "result": vnce_envelope,
        }

    # ACT-based dispatch logic (from actionmap.json)
    act_map = {
        "00": (load_identity, "RETURN"),
        "01": (load_config, "RETURN"),
        "10": (validate_state, "RETURN"),
        "11": (noop_action, "RETURN")
    }
    act_code = str(payload.get("ACT", "")).zfill(2)
    if act_code not in act_map:
        return {"success": False, "error": f"Unknown ACT code: {act_code}"}
    fn, out_route = act_map[act_code]
    try:
        result = fn(payload.get("payload", {}))
    except Exception as e:
        return {"success": False, "error": f"Dispatch error: {e}", "action_code": act_code, "function": fn.__name__, "out_route": out_route}
    return {"success": True, "action_code": act_code, "function": fn.__name__, "out_route": out_route, "result": result}


# --- ACT-mapped functions for CORE pillar ---
def load_identity(payload: dict) -> dict:
    """ACT 00 -- Load machine/user/SARA identity profile from NBS store."""
    import json as _json, os as _os
    project = str(payload.get("project_name") or SYSTEM_CORE_PROJECT_NAME)
    role = str(payload.get("role") or "").lower()  # user | sara | machine
    identity_dir = _os.path.join(NBS_BASE_DIR, project, "identity")
    # If specific role requested, look in that subdirectory
    candidates = []
    if role in {"user", "sara", "machine"}:
        candidates = [_os.path.join(identity_dir, role)]
    else:
        candidates = [
            _os.path.join(identity_dir, "user"),
            _os.path.join(identity_dir, "sara"),
            _os.path.join(identity_dir, "machine"),
        ]
    profiles = []
    for d in candidates:
        if not _os.path.isdir(d):
            continue
        for fname in _os.listdir(d):
            if not fname.endswith(".json"):
                continue
            fpath = _os.path.join(d, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = _json.load(f)
                profiles.append({"path": fpath, "data": data})
            except Exception:
                pass
    if not profiles:
        return {"success": False, "error": f"No identity files found in {identity_dir}", "project": project}
    return {"success": True, "project": project, "identity_profiles": profiles, "count": len(profiles)}


def load_config(payload: dict) -> dict:
    """ACT 01 -- Load system config deterministically from NBS store."""
    import json as _json, os as _os
    project = str(payload.get("project_name") or SYSTEM_CORE_PROJECT_NAME)
    config_dir = _os.path.join(NBS_BASE_DIR, project, "control", "config")
    configs = {}
    if _os.path.isdir(config_dir):
        for fname in _os.listdir(config_dir):
            if not fname.endswith(".json"):
                continue
            fpath = _os.path.join(config_dir, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    configs[fname] = _json.load(f)
            except Exception:
                pass
    # Also check for a trust-policy alongside the config
    trust_candidates = [
        _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "trust-policy.json"),
        "/etc/sara-lite/trust-policy.json",
    ]
    for tp in trust_candidates:
        if _os.path.exists(tp):
            try:
                with open(tp, "r", encoding="utf-8") as f:
                    configs["trust-policy.json"] = _json.load(f)
            except Exception:
                pass
            break
    return {"success": True, "project": project, "configs": configs, "count": len(configs)}


def validate_state(payload: dict) -> dict:
    """ACT 10 -- Validate current FSM state against allowed CORE transitions."""
    state_str = str(payload.get("state", "")).lower()
    if not state_str:
        return {"valid": False, "reason": "No state provided in payload"}
    allowed = set(CORE_FSM_STATES.keys())
    if state_str not in allowed:
        return {"valid": False, "state": state_str, "allowed": sorted(allowed), "reason": "State not in CORE FSM"}
    # Check if transition is possible from current state
    current_code = CORE_FSM_STATES.get(state_str, -1)
    reachable = {v[0] for (s, a), v in CORE_FSM_TRANSITIONS.items() if s == current_code}
    reachable_names = [k for k, v in CORE_FSM_STATES.items() if v in reachable]
    return {"valid": True, "state": state_str, "state_code": current_code, "reachable_states": reachable_names}


def noop_action(payload: dict) -> dict:
    """ACT 11 -- No operation; returns payload unchanged."""
    return {"success": True, "noop": True, "payload": payload}

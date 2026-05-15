"""
SARA Control — Shunt entrypoint, ACT dispatch, header validation, and pillar routing.
Extracted from sara_controlgen1.py.
"""
import os
import json
from typing import Dict, Any

_KNOWN_PILLARS = {"CONTROL", "CORE", "SECURITY", "MAMA", "SDK"}


def _load_actionmap():
    _here = os.path.dirname(os.path.abspath(__file__))
    _path = os.path.join(_here, "..", "actionmap.updated.json")
    if not os.path.exists(_path):
        _path = os.path.join(_here, "..", "actionmap.json")
    if not os.path.exists(_path):
        return {}
    try:
        import json as _json
        with open(_path, "r", encoding="utf-8") as f:
            return _json.load(f)
    except Exception:
        return {}


def _dispatch_to_pillar(target_pillar: str, command: str, inner_payload: dict) -> dict:
    """Load and call the target pillar's shunt entrypoint via relative importlib path."""
    import importlib.util as _iu, os as _os
    _here = _os.path.dirname(_os.path.abspath(__file__))
    _pillar_map = {
        "CORE":     ("sara_coregen1",     _os.path.join(_here, "..", "sara_core",     "sara_coregen1.py")),
        "SECURITY": ("sara_securitygen1", _os.path.join(_here, "..", "sara_security", "sara_securitygen1.py")),
        "MAMA":     ("sara_mamagen1",     _os.path.join(_here, "..", "sara_mama",     "sara_mamagen1.py")),
        "SDK":      ("Sara_sdk_gen1",     _os.path.join(_here, "..", "sara_sdk",      "Sara_sdk.gen1.py")),
    }
    if target_pillar not in _pillar_map:
        return {"success": False, "error": f"Unknown target pillar: {target_pillar}"}
    mod_name, mod_path = _pillar_map[target_pillar]
    if not _os.path.exists(mod_path):
        return {"success": False, "error": f"Pillar module not found: {mod_path}"}
    try:
        _spec = _iu.spec_from_file_location(mod_name, mod_path)
        _mod = _iu.module_from_spec(_spec)
        _spec.loader.exec_module(_mod)
        ep_name = f"{target_pillar.lower()}_shunt_entrypoint"
        ep = getattr(_mod, ep_name, None)
        if ep is None:
            return {"success": False, "error": f"No entrypoint {ep_name} in {mod_name}"}
        return ep(command, inner_payload)
    except Exception as e:
        return {"success": False, "error": f"Pillar dispatch error: {e}"}


def route_command(envelope: dict) -> dict:
    """ACT 00 — Route BuceyShunt envelope to target pillar."""
    target = str(envelope.get("target_pillar", "")).upper()
    intent = str(envelope.get("intent", "route"))
    inner = dict(envelope.get("payload", {}))
    if target == "CONTROL" or not target:
        return {"status": "SELF_ROUTED", "intent": intent, "result": inner}
    if target not in _KNOWN_PILLARS:
        return {"success": False, "error": f"Unknown target_pillar: {target}"}
    return _dispatch_to_pillar(target, intent, inner)


def validate_profile(envelope: dict) -> dict:
    """ACT 01 — Validate source_pillar and required shunt fields."""
    source = str(envelope.get("source_pillar", "")).upper()
    missing = [f for f in ("shunt_id", "source_pillar", "target_pillar", "timestamp", "intent", "payload", "context_tags", "requires_response") if f not in envelope]
    if missing:
        return {"valid": False, "reason": f"Missing fields: {missing}"}
    if source not in _KNOWN_PILLARS:
        return {"valid": False, "reason": f"Unknown source_pillar: {source}"}
    return {"valid": True, "source_pillar": source, "shunt_id": envelope.get("shunt_id")}


def authorize_map(envelope: dict) -> dict:
    """ACT 10 — Check envelope intent against actionmap for the source pillar."""
    source = str(envelope.get("source_pillar", "")).upper()
    intent = str(envelope.get("intent", "")).strip()
    actionmap = _load_actionmap()
    pillar_map = actionmap.get(source, {})
    allowed_intents = set(pillar_map.values())
    if intent in allowed_intents:
        return {"authorized": True, "source_pillar": source, "intent": intent}
    return {"authorized": False, "source_pillar": source, "intent": intent, "reason": "Intent not in actionmap for source pillar"}


def reject_action(envelope: dict) -> dict:
    """ACT 11 — Reject the action and log the reason."""
    return {
        "rejected": True,
        "source_pillar": envelope.get("source_pillar", "UNKNOWN"),
        "intent": envelope.get("intent", "UNKNOWN"),
        "shunt_id": envelope.get("shunt_id", ""),
        "reason": "CONTROL:REJECT — action denied by ACT 11",
    }


def launch_all_pillars(payload):
    """
    Launches the five main SARA pillars (CONTROL, CORE, SECURITY, MAMA, SDK) using the control's mapper.
    Deterministic, additive handler. Does not modify any other logic.
    """
    results = {}
    try:
        from sara_core.sara_coregen1 import core_shunt_entrypoint
        results["CORE"] = core_shunt_entrypoint("start", payload)
    except Exception as e:
        results["CORE"] = {"error": str(e)}
    try:
        from sara_security.sara_securitygen1 import security_shunt_entrypoint
        results["SECURITY"] = security_shunt_entrypoint("start", payload)
    except Exception as e:
        results["SECURITY"] = {"error": str(e)}
    try:
        from sara_mama.sara_mamagen1 import mama_shunt_entrypoint
        results["MAMA"] = mama_shunt_entrypoint("start", payload)
    except Exception as e:
        results["MAMA"] = {"error": str(e)}
    try:
        import importlib.util as _iu, os as _os
        _sdk_path = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "sara_sdk", "Sara_sdk.gen1.py")
        _sdk_spec = _iu.spec_from_file_location("Sara_sdk_gen1", _sdk_path)
        _sdk_mod = _iu.module_from_spec(_sdk_spec)
        _sdk_spec.loader.exec_module(_sdk_mod)
        results["SDK"] = _sdk_mod.dispatch_sdk_protocol("special_case", "start", payload)
    except Exception as e:
        results["SDK"] = {"error": str(e)}
    results["CONTROL"] = {"info": "CONTROL pillar active (self)"}
    return {"launched_pillars": results}


def validate_shunt_header(payload: dict) -> bool:
    """
    Enforces shunt header contract on inbound/outbound actions.
    """
    required_fields = ["shunt_id", "source_pillar", "target_pillar", "timestamp", "intent", "payload", "context_tags", "requires_response"]
    return all(field in payload for field in required_fields)


def control_shunt_entrypoint(command: str, payload: dict) -> dict:
    """
    Single entrypoint for all cross-pillar actions. Applies header validation and routes to FSM.
    """
    if not validate_shunt_header(payload):
        return {"success": False, "error": "Invalid shunt header"}

    act_map = {
        "00": (route_command, "RETURN"),
        "01": (validate_profile, "RETURN"),
        "10": (authorize_map, "RETURN"),
        "11": (reject_action, "RETURN"),
        "99": (launch_all_pillars, "RETURN")
    }
    act_code = str(payload.get("ACT", "")).zfill(2)
    if act_code not in act_map:
        return {"success": False, "error": f"Unknown ACT code: {act_code}"}
    fn, out_route = act_map[act_code]
    try:
        result = fn(payload)
    except Exception as e:
        return {"success": False, "error": f"Dispatch error: {e}", "action_code": act_code, "function": fn.__name__, "out_route": out_route}
    return {"success": True, "action_code": act_code, "function": fn.__name__, "out_route": out_route, "result": result}


# --- Binary header constants ---
SARA_CONTROL_HEADER_START = "SARA_CONTROL_HEADER_START"
SARA_CONTROL_HEADER_BYTE0 = 0x01
SARA_CONTROL_HEADER_BYTE1 = 0x1D
SARA_CONTROL_HEADER_BYTE2 = 0x00
SARA_CONTROL_HEADER_BYTE3 = 0xC1
SARA_CONTROL_HEADER_BYTE4 = 0xA0
SARA_CONTROL_HEADER_BYTE5 = 0x31
SARA_CONTROL_HEADER_RESERVED_BYTES = 210
SARA_CONTROL_HEADER_END = "SARA_CONTROL_HEADER_END"
SARA_CONTROL_BINARY_SPECIAL_HEADER_LITERAL = """SARA_CONTROL_HEADER_START
BYTE0: 01        # Shunt Mode Enable
BYTE1: 1D        # Domain=00 CPU | Origin=01 Control-native | Authority=11 CONTROL-only | Routing=01 thirds
BYTE2: 00        # Envoy/Resonator Switch (0 = standard control lane)
BYTE3: C1        # FileName_FirstLetter=11 | OrchestratorPattern=00 | Lane=01
BYTE4: A0        # ExtensionSignature=10 | DomainConfirm=10
BYTE5: 31        # ShuntAuthority=3 execute/write | ShuntLock=1 control-owned
RESERVED: 00 * 210 bytes
SARA_CONTROL_HEADER_END"""
SARA_CONTROL_BINARY_SPECIAL_HEADER_BYTES = bytes(
    [
        SARA_CONTROL_HEADER_BYTE0,
        SARA_CONTROL_HEADER_BYTE1,
        SARA_CONTROL_HEADER_BYTE2,
        SARA_CONTROL_HEADER_BYTE3,
        SARA_CONTROL_HEADER_BYTE4,
        SARA_CONTROL_HEADER_BYTE5,
    ]
)

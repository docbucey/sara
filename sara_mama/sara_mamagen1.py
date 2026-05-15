def mama_slm_entrypoint(command: str, payload: dict) -> dict:
    """
    SLM entrypoint for MAMA. Only responds if CONTROL is up and (MAMA and CORE) are up.
    Accepts 'probe' command to return available functions.
    """
    control_up = payload.get('control_up', False)
    mama_up = True  # This is MAMA
    core_up = payload.get('core_up', False)
    if not control_up:
        return {"status": "standing_by", "detail": "CONTROL not available"}
    if not (mama_up and core_up):
        return {"status": "standby", "detail": "Waiting for MAMA and CORE"}
    if command == 'probe':
        return {
            "status": "ready",
            "functions": [
                "terminal_window_action", "ide_protocol_action", "device_input_action", "learning_action", "mama_stagework_action"
            ]
        }
    return {"status": "ready", "detail": "MAMA SLM active via CONTROL"}
def terminal_window_action(payload: dict):
    """
    MAMA interactive terminal window: routes command to CONTROL, returns output for UI display.
    Args: payload dict with keys: command (str or list), user (optional)
    Returns: result dict with stdout/stderr/output
    """
    import importlib
    import os
    import json
    from datetime import datetime
    # Shunt header enforcement
    if isinstance(payload, dict) and 'shunt_id' in payload:
        if not validate_shunt_header(payload):
            return {"success": False, "error": "Invalid shunt header"}
    audit_entry = {
        'timestamp': datetime.now().isoformat(),
        'action': 'terminal_window_action',
        'user': payload.get('user', 'system'),
        'command': payload.get('command')
    }
    try:
        control_mod = importlib.import_module('claywork.saragen0finish.sara_control.sara_controlgen1')
        result = control_mod.system_command_action('run_system_command', payload)
    except Exception as e:
        result = {"success": False, "error": f"CONTROL routing failed: {e}"}
    audit_entry['result'] = 'PASS' if result.get('success') else 'FAIL'
    audit_entry['details'] = result.get('error', result.get('stdout', ''))
    # Persistent audit logging
    try:
        audit_dir = os.path.join(os.path.dirname(__file__), 'audit_logs')
        os.makedirs(audit_dir, exist_ok=True)
        audit_file = os.path.join(audit_dir, 'terminal_window_audit.log')
        with open(audit_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(audit_entry) + '\n')
    except Exception:
        pass
    return result
# --- IDE Protocol Mediation ---
def ide_protocol_action(action: str, payload: dict):
    """
    Mediates IDE protocol actions: validates, logs, and forwards to CONTROL for enforcement/persistence.
    """
    # Shunt header enforcement
    if isinstance(payload, dict) and 'shunt_id' in payload:
        if not validate_shunt_header(payload):
            return {"success": False, "error": "Invalid shunt header"}

    audit_entry = {
        'timestamp': datetime.now().isoformat(),
        'ide_action': action,
        'payload': payload,
        'user': os.getenv('USER', 'system')
    }
    try:
        control_mod = importlib.import_module('claywork.saragen0finish.sara_control.sara_controlgen1')
        result = control_mod.office_file_action(action, None, payload)
    except Exception as e:
        result = {"success": False, "error": f"CONTROL routing failed: {e}"}
    audit_entry['result'] = 'PASS' if result.get('success') else 'FAIL'
    audit_entry['details'] = result.get('error', result.get('info', ''))
    # Persistent audit logging
    try:
        audit_dir = os.path.join(os.path.dirname(__file__), 'audit_logs')
        os.makedirs(audit_dir, exist_ok=True)
        audit_file = os.path.join(audit_dir, 'ide_protocol_audit.log')
        with open(audit_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(audit_entry) + '\n')
    except Exception:
        pass
    return result
# --- Device Input (Smithy) and Learning Management Protocol Mediation ---
import importlib
import os
import json
from datetime import datetime

def device_input_action(action: str, payload: dict):
    """
    Mediates device input (Smithy) actions: validates, logs, and forwards to CONTROL for enforcement/persistence.
    """
    # Shunt header enforcement
    if isinstance(payload, dict) and 'shunt_id' in payload:
        if not validate_shunt_header(payload):
            return {"success": False, "error": "Invalid shunt header"}

    audit_entry = {
        'timestamp': datetime.now().isoformat(),
        'device_action': action,
        'payload': payload,
        'user': os.getenv('USER', 'system')
    }
    try:
        control_mod = importlib.import_module('claywork.saragen0finish.sara_control.sara_controlgen1')
        result = control_mod.office_file_action(action, None, payload)
    except Exception as e:
        result = {"success": False, "error": f"CONTROL routing failed: {e}"}
    audit_entry['result'] = 'PASS' if result.get('success') else 'FAIL'
    audit_entry['details'] = result.get('error', result.get('info', ''))
    # Persistent audit logging
    try:
        audit_dir = os.path.join(os.path.dirname(__file__), 'audit_logs')
        os.makedirs(audit_dir, exist_ok=True)
        audit_file = os.path.join(audit_dir, 'device_input_audit.log')
        with open(audit_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(audit_entry) + '\n')
    except Exception:
        pass
    return result

def learning_action(action: str, payload: dict):
    """
    Mediates learning/experiential management actions: validates, logs, and forwards to CONTROL/CORE for persistence.
    """
    # Shunt header enforcement
    if isinstance(payload, dict) and 'shunt_id' in payload:
        if not validate_shunt_header(payload):
            return {"success": False, "error": "Invalid shunt header"}

    audit_entry = {
        'timestamp': datetime.now().isoformat(),
        'learning_action': action,
        'payload': payload,
        'user': os.getenv('USER', 'system')
    }
    try:
        # Prefer CONTROL for enforcement, fallback to CORE for direct persistence
        try:
            control_mod = importlib.import_module('claywork.saragen0finish.sara_control.sara_controlgen1')
            result = control_mod.office_file_action(action, None, payload)
        except Exception:
            core_mod = importlib.import_module('claywork.saragen0finish.sara_core.sara_coregen1')
            result = core_mod.sara_project_memory_nbs(payload)
    except Exception as e:
        result = {"success": False, "error": f"Learning routing failed: {e}"}
    audit_entry['result'] = 'PASS' if result.get('success') else 'FAIL'
    audit_entry['details'] = result.get('error', result.get('info', ''))
    # Persistent audit logging
    try:
        audit_dir = os.path.join(os.path.dirname(__file__), 'audit_logs')
        os.makedirs(audit_dir, exist_ok=True)
        audit_file = os.path.join(audit_dir, 'learning_audit.log')
        with open(audit_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(audit_entry) + '\n')
    except Exception:
        pass
    return result
# --- Stagework (Office Suite) Mediation Logic ---
import importlib
import os
import json
from datetime import datetime

def mama_stagework_action(action: str, path: str, data=None):
    """
    Mediates Stagework (Office Suite) actions: validates, logs, and forwards to CONTROL's office_file_action.
    """
    # Shunt header enforcement
    if isinstance(data, dict) and 'shunt_id' in data:
        if not validate_shunt_header(data):
            return {"success": False, "error": "Invalid shunt header"}

    # Audit log entry
    audit_entry = {
        'timestamp': datetime.now().isoformat(),
        'stagework_action': action,
        'path': path,
        'user': os.getenv('USER', 'system')
    }

    # Forward to CONTROL's office_file_action
    try:
        control_mod = importlib.import_module('claywork.saragen0finish.sara_control.sara_controlgen1')
        result = control_mod.office_file_action(action, path, data)
    except Exception as e:
        result = {"success": False, "error": f"CONTROL routing failed: {e}"}

    audit_entry['result'] = 'PASS' if result.get('success') else 'FAIL'
    audit_entry['details'] = result.get('error', result.get('info', ''))

    # Persistent audit logging
    try:
        audit_dir = os.path.join(os.path.dirname(__file__), 'audit_logs')
        os.makedirs(audit_dir, exist_ok=True)
        audit_file = os.path.join(audit_dir, 'stagework_audit.log')
        with open(audit_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(audit_entry) + '\n')
    except Exception:
        pass
    return result

# shunt header: sara_mama_gen1
# --- FDSSM FORMALIZATION (AUTOGENERATED) ---
from typing import Dict, Any

# ShuntFSM object declaration (stub)

# shunt header: sara_mama_gen1
# --- FDSSM FORMALIZATION (AUTOGENERATED) ---
from typing import Dict, Any

# ShuntFSM object declaration (stub)
class ShuntFSM:
    def __init__(self, states: Dict[str, int], transitions: Dict[str, Any]):
        self.states = states
        self.transitions = transitions

# FSM state and transition table (stub/example)
MAMA_FSM_STATES = {
    "idle": 0,
    "processing": 1,
    "done": 2,
    "error": 3
}
MAMA_FSM_TRANSITIONS = {
    (0, "start"): (1, "begin_processing"),
    (1, "finish"): (2, "complete"),
    (1, "fail"): (3, "handle_error"),
    (3, "reset"): (0, "reset_idle")
}
mama_fsm = ShuntFSM(MAMA_FSM_STATES, MAMA_FSM_TRANSITIONS)

# Shunt entrypoint
def mama_shunt_entrypoint(command: str, payload: dict) -> dict:
    """
    Single entrypoint for all cross-pillar actions. Applies header validation and routes to FSM.
    """
    if not validate_shunt_header(payload):
        return {"success": False, "error": "Invalid shunt header"}

    # ACT-based dispatch logic (from actionmap.json)
    act_map = {
        "00": (snapshot, "STORE"),
        "01": (diff, "RETURN"),
        "10": (persist, "STORE"),
        "11": (noop_action, "RETURN")
    }
    act_code = str(payload.get("ACT", "")).zfill(2)
    if act_code not in act_map:
        return {"success": False, "error": f"Unknown ACT code: {act_code}"}
    fn, out_route = act_map[act_code]
    try:
        result = fn(payload)  # pass full shunt envelope so ACT functions can access context
    except Exception as e:
        return {"success": False, "error": f"Dispatch error: {e}", "action_code": act_code, "function": fn.__name__, "out_route": out_route}
    return {"success": True, "action_code": act_code, "function": fn.__name__, "out_route": out_route, "result": result}

# --- ACT-mapped functions for MAMA pillar ---
def snapshot(envelope: dict) -> dict:
    """ACT 00 â€” STORE: take a memory snapshot and append to MamaLedger."""
    inner = dict(envelope.get("payload", {}))
    task_type = str(inner.get("task_type") or envelope.get("intent") or "snapshot")
    try:
        ledger = MamaLedger()
        entry = ledger.append_attempt(
            task_type=task_type,
            status="SNAPSHOT",
            reason="MAMA:ACT00:snapshot",
            model_profile=str(inner.get("model_profile") or "plainjain_native"),
            lesson=str(inner.get("lesson") or ""),
            provenance=dict(inner.get("provenance") or {"shunt_id": envelope.get("shunt_id", "")}),
        )
        return {"success": True, "snapshot": True, "ledger_entry": entry, "task_type": task_type}
    except Exception as e:
        return {"success": False, "error": str(e), "snapshot": True}

def diff(envelope: dict) -> dict:
    """ACT 01 â€” RETURN: compute diff of ledger entries vs prior accepted state."""
    import json as _json
    inner = dict(envelope.get("payload", {}))
    task_type = str(inner.get("task_type") or "")
    try:
        ledger = MamaLedger()
        if not os.path.exists(ledger.ledger_path):
            return {"success": True, "diff": [], "reason": "MAMA:no_ledger_entries"}
        entries = []
        with open(ledger.ledger_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(_json.loads(line))
                    except Exception:
                        pass
        if task_type:
            entries = [e for e in entries if e.get("task_type") == task_type]
        if len(entries) < 2:
            return {"success": True, "diff": entries, "reason": "MAMA:insufficient_entries_for_diff"}
        # Return the last two entries as a simple diff summary
        prev, curr = entries[-2], entries[-1]
        changed = {k: {"from": prev.get(k), "to": curr.get(k)} for k in set(list(prev.keys()) + list(curr.keys())) if prev.get(k) != curr.get(k)}
        return {"success": True, "diff": changed, "task_type": task_type, "compared": [prev.get("ts"), curr.get("ts")]}
    except Exception as e:
        return {"success": False, "error": str(e), "diff": True}

def persist(envelope: dict) -> dict:
    """ACT 10 â€” STORE: persist memory packet to MamaLedger as accepted state."""
    inner = dict(envelope.get("payload", {}))
    task_type = str(inner.get("task_type") or envelope.get("intent") or "persist")
    try:
        mama = PlainJainMama()
        attempt = {
            "status": str(inner.get("status") or "PASS"),
            "reason": str(inner.get("reason") or "MAMA:ACT10:persist"),
        }
        packet = mama.create_memory_packet(
            task_type=task_type,
            attempt=attempt,
            preferred_profile=str(inner.get("model_profile") or "plainjain_native"),
        )
        return {"success": True, "persist": True, "packet": packet, "task_type": task_type}
    except Exception as e:
        return {"success": False, "error": str(e), "persist": True}

def noop_action(envelope: dict) -> dict:
    """ACT 11 â€” No operation."""
    return {"success": True, "noop": True, "shunt_id": envelope.get("shunt_id", "")}

# Header enforcement wrapper
def validate_shunt_header(payload: dict) -> bool:
    """
    Enforces shunt header contract on inbound/outbound actions.
    """
    required_fields = ["shunt_id", "source_pillar", "target_pillar", "timestamp", "intent", "payload", "context_tags", "requires_response"]
    return all(field in payload for field in required_fields)
# pillar: sara_mama
# generation: gen1-baseline
# BuceyShunt direct-communication header
SARA_MAMA_HEADER_START = "SARA_MAMA_HEADER_START"
SARA_MAMA_HEADER_BYTE0 = 0x01
SARA_MAMA_HEADER_BYTE1 = 0x3A
SARA_MAMA_HEADER_BYTE2 = 0x01
SARA_MAMA_HEADER_BYTE3 = 0xD2
SARA_MAMA_HEADER_BYTE4 = 0xB0
SARA_MAMA_HEADER_BYTE5 = 0x51
SARA_MAMA_HEADER_RESERVED_BYTES = 210
SARA_MAMA_HEADER_END = "SARA_MAMA_HEADER_END"
SARA_MAMA_BINARY_SPECIAL_HEADER_LITERAL = """SARA_MAMA_HEADER_START\nBYTE0: 01        # Shunt Mode Enable\nBYTE1: 3A        # Domain=00 CPU | Origin=11 Mama-native | Authority=11 MAMA-only | Routing=11 full dispatch\nBYTE2: 01        # Envoy/Resonator Switch (1 = mama special dispatch)\nBYTE3: D2        # FileName_FirstLetter=11 | MamaPattern=10 | Lane=10\nBYTE4: B0        # ExtensionSignature=11 | DomainConfirm=00\nBYTE5: 51        # ShuntAuthority=5 orchestrate | ShuntLock=1 mama-owned\nRESERVED: 00 * 210 bytes\nSARA_MAMA_HEADER_END"""
SARA_MAMA_BINARY_SPECIAL_HEADER_BYTES = bytes([
    SARA_MAMA_HEADER_BYTE0,
    SARA_MAMA_HEADER_BYTE1,
    SARA_MAMA_HEADER_BYTE2,
    SARA_MAMA_HEADER_BYTE3,
    SARA_MAMA_HEADER_BYTE4,
    SARA_MAMA_HEADER_BYTE5,
])

"""
SARA Mama Gen1 baseline (PlainJain-first)

Purpose:
- Establish Mama as the memory and routing substrate for model-agnostic generation.
- Use PlainJain principles as the first Gen1 spec base.
- Keep traditional model files swappable without changing Mama memory contracts.
- All orchestration and protocol actions are routed through the control FSM and shunt header for enforcement and audit.
"""

"""
SARA Mama Gen1 baseline (PlainJain-first)

Purpose:
- Establish Mama as the memory and routing substrate for model-agnostic generation.
- Use PlainJain principles as the first Gen1 spec base.
- Keep traditional model files swappable without changing Mama memory contracts.

This file is intentionally lightweight for harness and early Gen1 proofing.
"""


import difflib
import json
import os
import re
import importlib.util
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Set

# Import protocol modules

from secretary_protocol import SecretaryProtocol
from accountant_protocol import AccountantProtocol
from mailroom_protocol import MailroomProtocol
from marketing_protocol import MarketingProtocol
from switchboard_protocol import SwitchboardProtocol
from settings_protocol import SettingsProtocol
from ide_protocol import dispatch_ide_protocol


# MAMA intentionally avoids direct Gen1 cross-pillar imports to prevent circular dependencies.

# Import geek_protocol for browser/AI bridge
from geek_protocol import bridge_to_web_ai, learn_from_interaction, add_contact as geek_add_contact, list_contacts as geek_list_contacts, remove_contact as geek_remove_contact

try:
    import language_tool_python  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    language_tool_python = None

try:
    from research_calc_gn1 import (  # type: ignore
        BusinessCalculator,
        ShiProofRunner,
        SymbolTranslator,
        TraditionalCalculator,
        run_research_calc_proof,
    )
    _RESEARCH_CALC_OK = True
except Exception:
    try:
        import sys as _sys, os as _os
        _sys.path.insert(0, _os.path.dirname(__file__))
        from research_calc_gn1 import (  # type: ignore  # noqa: E402
            BusinessCalculator,
            ShiProofRunner,
            SymbolTranslator,
            TraditionalCalculator,
            run_research_calc_proof,
        )
        _RESEARCH_CALC_OK = True
    except Exception:
        _RESEARCH_CALC_OK = False

try:
    from spellchecker import SpellChecker  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    SpellChecker = None

try:
    from reasoning_protocols import list_reasoning_models  # type: ignore
    _ALLOWED_REASONING_MODELS = {row.get("model", "") for row in list_reasoning_models() if isinstance(row, dict)}
except Exception:
    _ALLOWED_REASONING_MODELS = set()


def _load_plainjain_executor_mod_mama():
    executor_path = os.path.join(os.path.dirname(__file__), "ai_llc", "plainjain_executor.py")
    if not os.path.exists(executor_path):
        return None
    spec = importlib.util.spec_from_file_location("sara_plainjain_executor_runtime", executor_path)
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


# --- Office Suite protocol constants ---
OFFICE_SUITE_PROTOCOL_CLERK = "clerk"

OfficeSuiteProtocols: Dict[str, Dict[str, Any]] = {
    "secretary": {
        "version": "1.0",
        "handler": "SecretaryProtocol",
        "label": "Secretary",
    },
    OFFICE_SUITE_PROTOCOL_CLERK: {
        "version": "0.1",
        "handler": "handle_clerk_protocol",
        "dispatch_handler": "dispatch_clerk_protocol",
        "label": "Clerk",
        "caps": [
            "intake", "records", "routing", "status", "notifications",
            "list", "open", "meta", "devices", "bootmedia", "sideload", "verify",
            "compress", "decompress",
            "extract_full", "extract_target",
        ],
    },
    "accountant": {
        "version": "1.0",
        "handler": "AccountantProtocol",
        "label": "Accountant",
    },
    "mailroom": {
        "version": "1.0",
        "handler": "MailroomProtocol",
        "label": "Mailroom",
    },
    "marketing": {
        "version": "1.0",
        "handler": "MarketingProtocol",
        "label": "Marketing",
    },
    "switchboard": {
        "version": "1.0",
        "handler": "SwitchboardProtocol",
        "label": "Switchboard",
    },
    "settings": {
        "version": "1.0",
        "handler": "SettingsProtocol",
        "label": "Settings",
    },
    "geek": {
        "version": "1.0",
        "handler": "geek_protocol",
        "label": "Geek",
    },
}


def handle_clerk_protocol(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clerk protocol stub for Office Suite intake, records, and task routing.
    This is metadata-only and does not alter existing dispatch logic.
    """
    return {
        "status": "NOT_IMPLEMENTED",
        "protocol": OFFICE_SUITE_PROTOCOL_CLERK,
        "handler": "handle_clerk_protocol",
        "message": "Clerk protocol stub inserted; routing is not wired yet.",
        "payload": dict(payload or {}),
    }


def clerk_intake_endpoint(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "status": "READY_FOR_CONTROL",
        "endpoint": "clerk_intake_endpoint",
        "protocol": OFFICE_SUITE_PROTOCOL_CLERK,
        "action": "intake",
        "payload": dict(payload or {}),
    }


def clerk_records_endpoint(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "status": "READY_FOR_CONTROL",
        "endpoint": "clerk_records_endpoint",
        "protocol": OFFICE_SUITE_PROTOCOL_CLERK,
        "action": "records",
        "payload": dict(payload or {}),
    }


def clerk_routing_endpoint(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "status": "READY_FOR_CONTROL",
        "endpoint": "clerk_routing_endpoint",
        "protocol": OFFICE_SUITE_PROTOCOL_CLERK,
        "action": "routing",
        "payload": dict(payload or {}),
    }


def clerk_status_endpoint(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "status": "READY_FOR_CONTROL",
        "endpoint": "clerk_status_endpoint",
        "protocol": OFFICE_SUITE_PROTOCOL_CLERK,
        "action": "status",
        "payload": dict(payload or {}),
    }


def clerk_list_endpoint(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "status": "READY_FOR_CONTROL",
        "endpoint": "clerk_list_endpoint",
        "protocol": OFFICE_SUITE_PROTOCOL_CLERK,
        "action": "list",
        "payload": dict(payload or {}),
        "message": "Directory/bundle listing stub; CONTROL will implement actual listing.",
    }


def clerk_open_endpoint(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "status": "READY_FOR_CONTROL",
        "endpoint": "clerk_open_endpoint",
        "protocol": OFFICE_SUITE_PROTOCOL_CLERK,
        "action": "open",
        "payload": dict(payload or {}),
        "message": "Open/read stub; CONTROL will implement file access.",
    }


def clerk_meta_endpoint(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "status": "READY_FOR_CONTROL",
        "endpoint": "clerk_meta_endpoint",
        "protocol": OFFICE_SUITE_PROTOCOL_CLERK,
        "action": "meta",
        "payload": dict(payload or {}),
        "message": "Metadata stub; CONTROL will implement metadata extraction.",
    }


def clerk_devices_endpoint(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "status": "READY_FOR_CONTROL",
        "endpoint": "clerk_devices_endpoint",
        "protocol": OFFICE_SUITE_PROTOCOL_CLERK,
        "action": "devices",
        "devices": [],
        "payload": dict(payload or {}),
        "message": "Device scan stub; CONTROL will enumerate USB/external drives.",
    }


def clerk_bootmedia_endpoint(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "status": "READY_FOR_CONTROL",
        "endpoint": "clerk_bootmedia_endpoint",
        "protocol": OFFICE_SUITE_PROTOCOL_CLERK,
        "action": "bootmedia",
        "payload": dict(payload or {}),
        "message": "Boot media creation stub; CONTROL will implement formatting + writing.",
    }


def clerk_sideload_endpoint(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "status": "READY_FOR_CONTROL",
        "endpoint": "clerk_sideload_endpoint",
        "protocol": OFFICE_SUITE_PROTOCOL_CLERK,
        "action": "sideload",
        "payload": dict(payload or {}),
        "message": "Sideload stub; CONTROL will implement envoy installation.",
    }


def clerk_verify_endpoint(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "status": "READY_FOR_CONTROL",
        "endpoint": "clerk_verify_endpoint",
        "protocol": OFFICE_SUITE_PROTOCOL_CLERK,
        "action": "verify",
        "payload": dict(payload or {}),
        "message": "Verification stub; CONTROL will implement signature + integrity checks.",
    }


def clerk_compress_endpoint(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "status": "READY_FOR_CONTROL",
        "endpoint": "clerk_compress_endpoint",
        "protocol": OFFICE_SUITE_PROTOCOL_CLERK,
        "action": "compress",
        "payload": dict(payload or {}),
        "message": "Compression stub; CONTROL + CORE will implement actual compression.",
    }


def clerk_decompress_endpoint(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "status": "READY_FOR_CONTROL",
        "endpoint": "clerk_decompress_endpoint",
        "protocol": OFFICE_SUITE_PROTOCOL_CLERK,
        "action": "decompress",
        "payload": dict(payload or {}),
        "message": "Decompression stub; CONTROL + CORE will implement actual decompression.",
    }


def clerk_extract_full_endpoint(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "status": "READY_FOR_CONTROL",
        "endpoint": "clerk_extract_full_endpoint",
        "protocol": OFFICE_SUITE_PROTOCOL_CLERK,
        "action": "extract_full",
        "payload": dict(payload or {}),
        "message": "Full extraction stub; CONTROL + CORE will implement full bundle extraction.",
    }


def clerk_extract_target_endpoint(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "status": "READY_FOR_CONTROL",
        "endpoint": "clerk_extract_target_endpoint",
        "protocol": OFFICE_SUITE_PROTOCOL_CLERK,
        "action": "extract_target",
        "payload": dict(payload or {}),
        "message": "Targeted extraction stub; CONTROL + CORE will implement selective extraction.",
    }


def dispatch_clerk_protocol(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Metadata-safe Clerk dispatcher.
    Routes Clerk actions to protocol endpoints without adding OS-level behavior here.
    """
    envelope = dict(payload or {})
    action = str(envelope.get("action", "intake")).strip().lower()
    routes = {
        "intake": clerk_intake_endpoint,
        "records": clerk_records_endpoint,
        "routing": clerk_routing_endpoint,
        "status": clerk_status_endpoint,
        "notifications": clerk_status_endpoint,
    }
    routes.update({
        "list": clerk_list_endpoint,
        "open": clerk_open_endpoint,
        "meta": clerk_meta_endpoint,
        "devices": clerk_devices_endpoint,
        "bootmedia": clerk_bootmedia_endpoint,
        "sideload": clerk_sideload_endpoint,
        "verify": clerk_verify_endpoint,
    })
    routes.update({
        "compress": clerk_compress_endpoint,
        "decompress": clerk_decompress_endpoint,
    })
    routes.update({
        "extract_full": clerk_extract_full_endpoint,
        "extract_target": clerk_extract_target_endpoint,
    })
    handler = routes.get(action)
    if handler is None:
        return {
            "status": "ERROR",
            "protocol": OFFICE_SUITE_PROTOCOL_CLERK,
            "action": action,
            "error": f"Unsupported Clerk action: {action}",
            "supported_actions": sorted(routes.keys()),
        }
    # CONTROL routing is orchestrated externally through shunt envelopes.
    # MAMA remains presentation/dispatch-only and does not import or call CONTROL directly.
    return handler(envelope)


# Central FSM/dispatcher for protocol routing
class MamaDispatcher:
    def __init__(self):
        self.secretary = SecretaryProtocol()
        self.accountant = AccountantProtocol()
        self.mailroom = MailroomProtocol()
        self.marketing = MarketingProtocol()
        self.switchboard = SwitchboardProtocol()
        # Geek protocol does not require instantiation
        self.settings = SettingsProtocol()

    def dispatch(self, task_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route the request to the correct protocol handler based on task_type.
        All orchestration and security checks flow through control FSM/shunt header logic.
        This ensures Mama is always slaved to control for backend actions.
        """
        # Attach shunt header for audit
        payload = dict(payload)
        payload['mama_shunt_header'] = SARA_MAMA_BINARY_SPECIAL_HEADER_BYTES
        # Fallback to direct protocol dispatch if not handled by control
        if task_type == "word":
            return self.secretary.handle(payload)
        elif task_type == "excel":
            return self.accountant.handle(payload)
        elif task_type == "email":
            return self.mailroom.handle(payload)
        elif task_type == "call":
            return self.switchboard.handle(payload)
        elif task_type == "marketing":
            return self.marketing.handle(payload)
        elif task_type == "settings":
            return self.settings.handle(payload)
        elif task_type == "list_contacts_geek":
            return geek_list_contacts()
        elif task_type == "add_contact_geek":
            return geek_add_contact(payload.get("name"), payload.get("url"), payload.get("roles"))
        elif task_type == "remove_contact_geek":
            return geek_remove_contact(payload.get("name"), payload.get("url"))
        else:
            return {"error": f"Unknown task_type: {task_type}"}


MODEL_PROFILES: Dict[str, Dict[str, Any]] = {
    "plainjain_native": {
        "kind": "internal",
        "source": "ai_llc/plainjainllm.slam",
        "notes": "NBS-weighted native path using resonance, stability, provenance",
    },
    "deepseeker_coder_local": {
        "kind": "bridge",
        "source": "ai_llc/deepseeker_coder_bridge.slam",
        "notes": "DeepSeek Coder first expansion profile for local lab testing",
    },
    "ollama_default": {
        "kind": "bridge",
        "source": "ai_llc/ollama_bridge.slam",
        "notes": "Traditional external model bridge for text generation (opt-in only via SARA_ALLOW_OLLAMA)",
    },
}


COMMON_WORDS: Set[str] = {
    "a", "about", "after", "all", "also", "an", "and", "any", "are", "as", "at",
    "be", "because", "been", "before", "best", "both", "build", "but", "by",
    "can", "check", "code", "core", "create", "data", "do", "each", "end", "error",
    "file", "files", "for", "from", "get", "good", "grammar", "has", "have", "help",
    "if", "in", "into", "is", "it", "its", "just", "key", "learn", "like", "list",
    "make", "memory", "mode", "model", "more", "most", "name", "need", "new", "no",
    "not", "now", "of", "on", "one", "or", "other", "our", "out", "path", "profile",
    "project", "proof", "ready", "reason", "research", "result", "run", "same", "set",
    "should", "simple", "so", "some", "spell", "start", "status", "store", "system",
    "term", "terms", "text", "that", "the", "their", "them", "then", "there", "this",
    "to", "tool", "type", "up", "use", "user", "using", "valid", "value", "want", "was",
    "we", "well", "when", "with", "word", "words", "work", "workflow", "you", "your",
}


def _normalize_term(term: str) -> str:
    return re.sub(r"[^A-Za-z0-9_\-]", "", str(term or "").strip())


def _tokenize_words(text: str) -> List[str]:
    return re.findall(r"[A-Za-z][A-Za-z0-9_\-']*", text or "")


def _is_acronymish(token: str) -> bool:
    return token.isupper() and len(token) >= 2


def _is_technical_token(token: str) -> bool:
    return (
        bool(re.search(r"[_\-]", token))
        or bool(re.search(r"[A-Z].*[a-z]|[a-z].*[A-Z]", token))
        or bool(re.search(r"\d", token))
    )


class AdaptiveJargonLexicon:
    """Persistent, mode-aware jargon storage and text quality checks."""

    def __init__(self, base_dir: Optional[str] = None):
        here = os.path.dirname(__file__)
        self.base_dir = base_dir or here
        self.logs_dir = os.path.join(self.base_dir, "logs")
        os.makedirs(self.logs_dir, exist_ok=True)
        self.lexicon_path = os.path.join(self.logs_dir, "mama_jargon_lexicon.json")
        self.grammar_tool = None
        if language_tool_python is not None:
            try:
                self.grammar_tool = language_tool_python.LanguageTool("en-US")
            except Exception:
                self.grammar_tool = None

        self.spell_tool = None
        if SpellChecker is not None:
            try:
                self.spell_tool = SpellChecker()
            except Exception:
                self.spell_tool = None

        self._state = self._load_state()

    def _default_state(self) -> Dict[str, Any]:
        return {
            "version": 1,
            "created_at": _iso_now(),
            "updated_at": _iso_now(),
            "global_jargon": [],
            "modes": {
                "research": [],
                "coding": [],
                "office": [],
            },
        }

    def _load_state(self) -> Dict[str, Any]:
        if not os.path.exists(self.lexicon_path):
            state = self._default_state()
            self._save_state(state)
            return state
        try:
            with open(self.lexicon_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if not isinstance(loaded, dict):
                raise ValueError("lexicon format invalid")
            return loaded
        except Exception:
            state = self._default_state()
            self._save_state(state)
            return state

    def _save_state(self, state: Dict[str, Any]) -> None:
        state["updated_at"] = _iso_now()
        with open(self.lexicon_path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)

    def _mode_list(self, mode: str) -> List[str]:
        modes = self._state.setdefault("modes", {})
        if mode not in modes:
            modes[mode] = []
        return modes[mode]

    def teach_terms(self, terms: Iterable[str], mode: Optional[str] = None) -> Dict[str, Any]:
        clean_terms: List[str] = []
        for t in terms:
            nt = _normalize_term(t)
            if nt:
                clean_terms.append(nt)

        added_global = 0
        added_mode = 0

        global_terms = set(self._state.setdefault("global_jargon", []))
        for term in clean_terms:
            if term not in global_terms:
                global_terms.add(term)
                added_global += 1
        self._state["global_jargon"] = sorted(global_terms)

        if mode:
            mode_terms = set(self._mode_list(mode))
            for term in clean_terms:
                if term not in mode_terms:
                    mode_terms.add(term)
                    added_mode += 1
            self._state["modes"][mode] = sorted(mode_terms)

        self._save_state(self._state)
        return {
            "status": "PASS",
            "mode": mode,
            "added_global": added_global,
            "added_mode": added_mode,
            "lexicon_path": self.lexicon_path,
        }

    def get_known_terms(self, mode: Optional[str] = None) -> Set[str]:
        known = set(self._state.get("global_jargon", []))
        if mode:
            known.update(self._mode_list(mode))
        return known

    def _build_known_wordset(self, mode: str) -> Set[str]:
        known = set(COMMON_WORDS)
        jargon = self.get_known_terms(mode)
        known.update(jargon)
        known.update({w.lower() for w in jargon})
        return known

    def _rule_based_grammar(self, text: str) -> List[Dict[str, Any]]:
        issues: List[Dict[str, Any]] = []
        repeated_word_pattern = re.compile(r"\b([A-Za-z]+)\s+\1\b", re.IGNORECASE)
        for m in repeated_word_pattern.finditer(text):
            issues.append({
                "type": "grammar",
                "message": "Repeated word detected",
                "span": [m.start(), m.end()],
                "suggestion": m.group(1),
            })

        for m in re.finditer(r"\s{2,}", text):
            issues.append({
                "type": "grammar",
                "message": "Multiple spaces detected",
                "span": [m.start(), m.end()],
                "suggestion": "Use one space",
            })

        sentence_end_pattern = re.compile(r"[A-Za-z0-9\)]\n")
        for m in sentence_end_pattern.finditer(text):
            issues.append({
                "type": "grammar",
                "message": "Possible missing punctuation before line break",
                "span": [m.start(), m.end()],
                "suggestion": "Consider ending the sentence with . ? or !",
            })

        return issues

    def _grammar_check(self, text: str) -> List[Dict[str, Any]]:
        if self.grammar_tool is None:
            return self._rule_based_grammar(text)

        try:
            matches = self.grammar_tool.check(text)
            issues: List[Dict[str, Any]] = []
            for m in matches:
                issues.append({
                    "type": "grammar",
                    "message": m.message,
                    "span": [m.offset, m.offset + m.errorLength],
                    "suggestion": (m.replacements[0] if m.replacements else None),
                    "rule": m.ruleId,
                })
            return issues
        except Exception:
            return self._rule_based_grammar(text)

    def _spell_suggestions(self, token: str, known_words: Set[str]) -> List[str]:
        token_lower = token.lower()
        if self.spell_tool is not None:
            try:
                candidates = list(self.spell_tool.candidates(token_lower))[:5]
                return [c for c in candidates if c in known_words][:3] or candidates[:3]
            except Exception:
                pass

        return difflib.get_close_matches(token_lower, list(known_words), n=3, cutoff=0.82)

    def _collect_unknown_tokens(self, text: str, mode: str) -> List[Dict[str, Any]]:
        known_words = self._build_known_wordset(mode)
        known_jargon = self.get_known_terms(mode)
        unknowns: List[Dict[str, Any]] = []

        for token in _tokenize_words(text):
            norm = _normalize_term(token)
            low = norm.lower()
            if not norm or len(norm) < 3:
                continue
            if _is_acronymish(norm) or _is_technical_token(norm):
                continue
            if norm in known_jargon or low in known_words:
                continue

            suggestions = self._spell_suggestions(norm, known_words)
            unknowns.append({
                "type": "spelling",
                "token": token,
                "suggestions": suggestions,
            })

        deduped: Dict[str, Dict[str, Any]] = {}
        for entry in unknowns:
            key = str(entry.get("token", "")).lower()
            if key and key not in deduped:
                deduped[key] = entry
        return list(deduped.values())

    def check_text(self,
                   text: str,
                   mode: str = "research",
                   user_jargon: Optional[Iterable[str]] = None,
                   auto_learn: bool = False) -> Dict[str, Any]:
        if user_jargon:
            self.teach_terms(user_jargon, mode=mode)

        spelling = self._collect_unknown_tokens(text, mode=mode)
        grammar = self._grammar_check(text)

        jargon_hits = [
            token for token in _tokenize_words(text)
            if _normalize_term(token) in self.get_known_terms(mode)
        ]

        if auto_learn:
            teach_candidates = [
                s["token"] for s in spelling
                if _normalize_term(s.get("token", "")) and _is_technical_token(_normalize_term(s["token"]))
            ]
            if teach_candidates:
                self.teach_terms(teach_candidates, mode=mode)

        return {
            "status": "PASS",
            "mode": mode,
            "valid": len(spelling) == 0 and len(grammar) == 0,
            "spelling_issues": spelling,
            "grammar_issues": grammar,
            "jargon_detected": sorted(set(jargon_hits)),
            "known_jargon_count": len(self.get_known_terms(mode)),
            "lexicon_path": self.lexicon_path,
        }


class MamaLedger:
    """Append-safe memory ledger for accepted and failed attempts."""

    def __init__(self, base_dir: Optional[str] = None):
        here = os.path.dirname(__file__)
        self.base_dir = base_dir or here
        self.logs_dir = os.path.join(self.base_dir, "logs")
        os.makedirs(self.logs_dir, exist_ok=True)
        self.ledger_path = os.path.join(self.logs_dir, "mama_attempt_ledger.ndjson")

    def append_attempt(self,
                       task_type: str,
                       status: str,
                       reason: str,
                       model_profile: str,
                       lesson: Optional[str] = None,
                       provenance: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        entry = {
            "ts": _iso_now(),
            "task_type": task_type,
            "status": status,
            "reason": reason,
            "model_profile": model_profile,
            "lesson": lesson,
            "provenance": provenance or {},
        }
        with open(self.ledger_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        return entry


class PlainJainMama:
    """
    PlainJain-first Mama baseline.

    Gen1 intent:
    - Keep a stable memory contract.
    - Route to different model profiles using the same lesson/provenance structure.
    """

    def __init__(self, ledger: Optional[MamaLedger] = None):
        self.ledger = ledger or MamaLedger()
        self.jargon = AdaptiveJargonLexicon(base_dir=os.path.dirname(__file__))

    def list_model_profiles(self) -> List[str]:
        return sorted(MODEL_PROFILES.keys())

    def choose_profile(self, preferred: Optional[str] = None) -> str:
        if preferred and preferred in MODEL_PROFILES:
            return preferred
        return "plainjain_native"

    def extract_lesson(self, attempt: Dict[str, Any]) -> str:
        status = str(attempt.get("status", "unknown")).upper()
        reason = str(attempt.get("reason", "no-reason"))
        if status == "PASS":
            return f"reuse-path:{reason}"
        return f"avoid-path:{reason}"

    def create_memory_packet(self,
                             task_type: str,
                             attempt: Dict[str, Any],
                             preferred_profile: Optional[str] = None) -> Dict[str, Any]:
        profile = self.choose_profile(preferred_profile)
        lesson = self.extract_lesson(attempt)
        status = str(attempt.get("status", "unknown")).upper()
        reason = str(attempt.get("reason", "no-reason"))

        ledger_entry = self.ledger.append_attempt(
            task_type=task_type,
            status=status,
            reason=reason,
            model_profile=profile,
            lesson=lesson,
            provenance={
                "base_spec": "plainjainllm.slam",
                "profile_source": MODEL_PROFILES[profile]["source"],
            },
        )

        return {
            "mama_packet": {
                "task_type": task_type,
                "status": status,
                "reason": reason,
                "lesson": lesson,
                "selected_profile": profile,
                "profile_notes": MODEL_PROFILES[profile]["notes"],
                "ledger_ref": {
                    "ts": ledger_entry["ts"],
                    "path": self.ledger.ledger_path,
                },
            }
        }

    def teach_jargon(self, terms: Iterable[str], mode: str = "research") -> Dict[str, Any]:
        """Allow end users to teach evolving jargon terms at runtime."""
        return self.jargon.teach_terms(terms=terms, mode=mode)

    def check_text_quality(self,
                           text: str,
                           mode: str = "research",
                           user_jargon: Optional[Iterable[str]] = None,
                           auto_learn: bool = False) -> Dict[str, Any]:
        """Spell and grammar check that preserves user-taught jargon."""
        return self.jargon.check_text(
            text=text,
            mode=mode,
            user_jargon=user_jargon,
            auto_learn=auto_learn,
        )

    def run_research_calc(self,
                          formula: str,
                          samples: int = 500) -> Dict[str, Any]:
        """
        Evaluate a formula string through the research calculator.

        Accepts symbol shortcodes and Unicode math notation transparently:
            \\alpha, \\sqrt{x}, \\frac{a}{b}, \\partial f/x, âˆž, Î±, âˆ‚, âˆ«, Î£ ...

        Returns a full run-result dict including per-block DataFrames,
        falsifiability flags, boundary/NaN counts, and derivative maps.
        If research_calc_gn1 is unavailable returns an error dict.
        """
        if not _RESEARCH_CALC_OK:
            return {
                "status": "ERROR",
                "error": "research_calc_gn1 not available â€” ensure sara_mama dir is on sys.path",
                "formula_original": formula,
            }
        runner = ShiProofRunner(samples=samples)
        return runner.run(formula)

    def run_traditional_calc(self,
                             expression: str,
                             variables: Optional[Dict[str, Any]] = None,
                             rows: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Run traditional scientific calculator mode.

        - If rows are provided: evaluate expression across all rows.
        - Else: evaluate single expression with optional variable substitutions.
        """
        if not _RESEARCH_CALC_OK:
            return {
                "status": "ERROR",
                "error": "research_calc_gn1 not available â€” ensure sara_mama dir is on sys.path",
                "expression_original": expression,
            }
        calc = TraditionalCalculator()
        if rows is not None:
            return calc.evaluate_rows(expression=expression, rows=rows)
        return calc.evaluate(expression=expression, variables=variables)

    def run_business_calc(self,
                          operation: str,
                          inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run business calculator mode.

        Supported operation values include:
        roi, gross_margin, profit_margin, break_even_units,
        compound_growth, loan_payment, npv, cagr, markup,
        discount_price, formula.
        """
        if not _RESEARCH_CALC_OK:
            return {
                "status": "ERROR",
                "error": "research_calc_gn1 not available â€” ensure sara_mama dir is on sys.path",
                "operation": operation,
            }
        calc = BusinessCalculator()
        return calc.calculate(operation=operation, inputs=inputs)

    def validate_real_world_formula(self,
                                    formula: str,
                                    observations: List[Dict[str, Any]],
                                    observed_col: str,
                                    abs_tolerance: float = 0.05,
                                    rel_tolerance: float = 0.05,
                                    scenario_label: str = "real_world",
                                    units_map: Optional[Dict[str, str]] = None,
                                    uncertainty_col: Optional[str] = None,
                                    uncertainty_abs_default: float = 0.0,
                                    uncertainty_rel_default: float = 0.0,
                                    strict_units: bool = False,
                                    outlier_policy: str = "none",
                                    baseline_formula: Optional[str] = None,
                                    verdict_version: str = "v1",
                                    run_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate a formula against measured real-world observations.

        Each observation row should include all input variables used in the
        formula plus one measured output column (observed_col).

        Example row for SHI:
            {"memory": 12.0, "footprint": 3.0, "runtime": 2.0,
             "enumerator": 1.0, "shi_observed": 5.1}
        """
        if not _RESEARCH_CALC_OK:
            return {
                "status": "ERROR",
                "error": "research_calc_gn1 not available â€” ensure sara_mama dir is on sys.path",
                "formula_original": formula,
            }

        runner = ShiProofRunner(samples=16)
        return runner.validate_real_world_observations(
            formula=formula,
            observations=observations,
            observed_col=observed_col,
            abs_tolerance=abs_tolerance,
            rel_tolerance=rel_tolerance,
            scenario_label=scenario_label,
            units_map=units_map,
            uncertainty_col=uncertainty_col,
            uncertainty_abs_default=uncertainty_abs_default,
            uncertainty_rel_default=uncertainty_rel_default,
            strict_units=strict_units,
            outlier_policy=outlier_policy,
            baseline_formula=baseline_formula,
            verdict_version=verdict_version,
            run_id=run_id,
        )

    def validate_real_world_formula_from_excel(self,
                                               formula: str,
                                               excel_path: str,
                                               observed_col: str,
                                               sheet_name: Optional[str] = None,
                                               abs_tolerance: float = 0.05,
                                               rel_tolerance: float = 0.05,
                                               scenario_label: Optional[str] = None,
                                               units_map: Optional[Dict[str, str]] = None,
                                               report_output_path: Optional[str] = None,
                                               uncertainty_col: Optional[str] = None,
                                               uncertainty_abs_default: float = 0.0,
                                               uncertainty_rel_default: float = 0.0,
                                               strict_units: bool = False,
                                               outlier_policy: str = "none",
                                               baseline_formula: Optional[str] = None,
                                               verdict_version: str = "v1",
                                               run_id: Optional[str] = None) -> Dict[str, Any]:
        """
        One-step Excel flow for real-world scientific validation.

        Reads measured rows from an Excel sheet, validates formula fit,
        and optionally exports a report (.xlsx/.csv/.json).
        """
        if not _RESEARCH_CALC_OK:
            return {
                "status": "ERROR",
                "error": "research_calc_gn1 not available â€” ensure sara_mama dir is on sys.path",
                "formula_original": formula,
            }

        runner = ShiProofRunner(samples=16)
        result = runner.validate_real_world_excel(
            formula=formula,
            excel_path=excel_path,
            observed_col=observed_col,
            sheet_name=sheet_name,
            abs_tolerance=abs_tolerance,
            rel_tolerance=rel_tolerance,
            scenario_label=scenario_label,
            units_map=units_map,
            uncertainty_col=uncertainty_col,
            uncertainty_abs_default=uncertainty_abs_default,
            uncertainty_rel_default=uncertainty_rel_default,
            strict_units=strict_units,
            outlier_policy=outlier_policy,
            baseline_formula=baseline_formula,
            verdict_version=verdict_version,
            run_id=run_id,
        )

        if report_output_path and result.get("status") == "PASS":
            result["report_export"] = runner.export_validation_report(
                validation_result=result,
                output_path=report_output_path,
            )

        return result

    def translate_formula_symbols(self, formula: str) -> str:
        """
        Translate symbol shortcodes/Unicode in a formula to sympy ASCII
        without running test blocks. Useful for formula preview/validation.
        """
        if not _RESEARCH_CALC_OK:
            return formula
        return SymbolTranslator().translate(formula)

    def symbol_palette(self) -> List[Any]:
        """Return symbol palette entries for UI toolbar consumers."""
        if not _RESEARCH_CALC_OK:
            return []
        return SymbolTranslator.palette()

    def symbol_shortcode_help(self) -> str:
        """Return a human-readable shortcode reference."""
        if not _RESEARCH_CALC_OK:
            return "research_calc_gn1 not loaded"
        return SymbolTranslator.shortcode_help()


def run_mama_proof() -> Dict[str, Any]:
    """Small proof path used for first startup and harness-era validation."""
    mama = PlainJainMama()
    packet = mama.create_memory_packet(
        task_type="startup_proof",
        attempt={"status": "PASS", "reason": "plainjain-baseline-initialized"},
        preferred_profile="plainjain_native",
    )
    jargon_seed = mama.teach_jargon(["jargonese", "ShuntFSM", "paladin_gate"], mode="coding")
    quality = mama.check_text_quality(
        text="This is jargonese and ShuntFSM protocol text with paladin_gate wired in.",
        mode="coding",
    )
    calc_proof: Dict[str, Any] = {"status": "SKIPPED"}
    if _RESEARCH_CALC_OK:
        try:
            calc_proof = run_research_calc_proof()
        except Exception as e:
            calc_proof = {"status": "ERROR", "error": str(e)}

    return {
        "status": "PASS",
        "reason": "MAMA:plainjain-base-ready",
        "packet": packet,
        "jargon_seed": jargon_seed,
        "quality": {
            "valid": quality.get("valid", False),
            "known_jargon_count": quality.get("known_jargon_count", 0),
            "lexicon_path": quality.get("lexicon_path"),
        },
        "research_calc": {
            "status": calc_proof.get("status"),
            "translation_score": calc_proof.get("translation_score"),
            "palette_size": calc_proof.get("palette_size"),
            "runner_status": calc_proof.get("runner", {}).get("status"),
        },
    }


def _extract_validated_reasoning(result: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not isinstance(result, dict):
        return {}

    candidate = result
    if isinstance(result.get("reasoning"), dict):
        candidate = result["reasoning"]

    selected_by = str(candidate.get("selected_by") or "")
    selected_model = str(candidate.get("selected_model") or candidate.get("protocol") or "")
    security_validated = bool(candidate.get("security_validated"))
    envelope_validated = bool(candidate.get("envelope_validated"))
    advisory_only = bool(candidate.get("advisory_only"))
    presentation_only = bool(candidate.get("presentation_only"))
    schema_safe = bool(candidate.get("schema_safe"))

    if selected_by != "CONTROL":
        return {}
    if not security_validated or not envelope_validated:
        return {}
    if not advisory_only or not presentation_only or not schema_safe:
        return {}
    if _ALLOWED_REASONING_MODELS and selected_model not in _ALLOWED_REASONING_MODELS:
        return {}

    output = candidate.get("model_output")
    if not isinstance(output, dict):
        output = {}

    return {
        "selected_by": selected_by,
        "selected_model": selected_model,
        "domain": str(candidate.get("domain") or ""),
        "security_validated": security_validated,
        "envelope_validated": envelope_validated,
        "advisory_only": advisory_only,
        "presentation_only": presentation_only,
        "schema_safe": schema_safe,
        "model_output": output,
    }


def _build_reasoning_overlay(request: Dict[str, Any], result: Optional[Dict[str, Any]], mode: str, strain: str) -> Dict[str, Any]:
    validated = _extract_validated_reasoning(result)
    profile = request.get("machine_profile") if isinstance(request.get("machine_profile"), dict) else {}
    profile_id = str(profile.get("profile_id") or "default")

    overlay = {
        "visible": bool(validated),
        "profile_adaptation": {
            "profile_id": profile_id,
            "mode": mode,
            "strain": strain,
            "voice_first": True,
            "low_click": True,
        },
        "accessibility": {
            "advisory_only": True,
            "presentation_only": True,
            "security_gate_before_visibility": True,
        },
        "generative_surface": {
            "style": "guided" if mode == "interactive" else "quiet",
            "reasoning_lens": str(validated.get("selected_model") or "none"),
            "reasoning_domain": str(validated.get("domain") or "none"),
            "reasoning_summary": str((validated.get("model_output") or {}).get("notes") or "No validated reasoning overlay."),
        },
    }
    if validated:
        overlay["validated_reasoning"] = validated
    return overlay


def _phase1_outcome_from_result_mama(result: Optional[Dict[str, Any]]) -> str:
    if not isinstance(result, dict):
        return "pending"
    explicit = str(result.get("phase1_outcome") or "").strip().lower()
    if explicit in {"allow", "deny", "constrain", "schema_fail", "boundary_blocked", "pending"}:
        return explicit

    status_u = str(result.get("status") or "").strip().upper()
    error_l = str(result.get("error") or result.get("reason") or "").strip().lower()
    if "schema" in error_l or status_u in {"SCHEMA_FAIL", "SCHEMA-FAIL"}:
        return "schema_fail"
    if status_u in {"DENY", "ERROR", "FAIL"}:
        return "deny"
    if status_u in {"CHALLENGE", "CONSTRAIN", "CONSTRAINED"} or "constrain" in error_l:
        return "constrain"
    if status_u in {"QUARANTINE", "LOCKDOWN", "HOLD"}:
        return "boundary_blocked"
    if status_u in {"ALLOW", "READY", "PASS"}:
        return "allow"
    return "pending"


def _phase1_osh_surface_mama(result: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    base_pipeline = result.get("osh_pipeline") if isinstance(result, dict) and isinstance(result.get("osh_pipeline"), dict) else {}
    stages = base_pipeline.get("stages") if isinstance(base_pipeline.get("stages"), list) else []
    if not stages:
        current = str(base_pipeline.get("current_stage") or "OSH-1")
        stage_codes = ["OSH-1", "OSH-2", "OSH-3", "OSH-4", "OSH-5"]
        labels = {
            "OSH-1": "Intake",
            "OSH-2": "Normalization",
            "OSH-3": "Boundary",
            "OSH-4": "Schema",
            "OSH-5": "Non-Authority",
        }
        if current not in stage_codes:
            current = "OSH-1"
        current_index = stage_codes.index(current)
        for idx, code in enumerate(stage_codes):
            state = "pending"
            if idx < current_index:
                state = "complete"
            elif idx == current_index:
                state = "active"
            stages.append({"code": code, "label": labels.get(code, code), "state": state})
    outcome = _phase1_outcome_from_result_mama(result)
    return {
        "current_stage": str(base_pipeline.get("current_stage") or "OSH-1"),
        "stages": stages,
        "phase1_outcome": outcome,
        "security_outcome_set": ["allow", "deny", "constrain", "schema_fail"],
    }


def _extract_biometric_context_mama(
    amip_payload: Optional[Dict[str, Any]] = None,
    result: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Build a bounded biometric/context bundle for presentation-scoped adaptation.
    This does not perform identity matching, routing mutation, or policy changes.

    Biometric context is always evaluated for local, in-program human/ADA adaptation
    when SECURITY visibility allows (phase-1 outcome). There is no end-user opt-out
    in payload; misuse or off-device sharing is a SECURITY/policy matter, not a UX toggle.
    """
    request = dict(amip_payload or {})
    payload = request.get("payload") if isinstance(request.get("payload"), dict) else {}
    biometrics = payload.get("biometrics") if isinstance(payload.get("biometrics"), dict) else {}

    phase1 = _phase1_osh_surface_mama(result)
    phase1_outcome = str(phase1.get("phase1_outcome") or "pending")
    security_allows_visibility = phase1_outcome in {"allow", "constrain"}

    # Keep feature-level extraction coarse and non-identifying.
    voice = biometrics.get("voice") if isinstance(biometrics.get("voice"), dict) else {}
    video = biometrics.get("video") if isinstance(biometrics.get("video"), dict) else {}
    interaction = biometrics.get("interaction") if isinstance(biometrics.get("interaction"), dict) else {}

    context_bundle = {
        "enabled": bool(security_allows_visibility),
        "prediction_enabled": bool(security_allows_visibility),
        "constant_local_adaptation": True,
        "security_allows_visibility": security_allows_visibility,
        "phase1_outcome": phase1_outcome,
        "signals": {
            "voice": {
                "speech_rate_wpm": voice.get("speech_rate_wpm"),
                "pause_ratio": voice.get("pause_ratio"),
                "volume_variance": voice.get("volume_variance"),
            },
            "video": {
                "gaze_stability": video.get("gaze_stability"),
                "motion_level": video.get("motion_level"),
                "blink_rate": video.get("blink_rate"),
            },
            "interaction": {
                "typing_hesitation": interaction.get("typing_hesitation"),
                "correction_rate": interaction.get("correction_rate"),
                "latency_ms": interaction.get("latency_ms"),
            },
        },
        "guardrails": {
            "identity_inference": False,
            "policy_mutation": False,
            "routing_mutation": False,
            "presentation_only": True,
            "local_device_program_intent": True,
        },
    }
    return context_bundle


def _predict_contextual_state_mama(context_bundle: Dict[str, Any], mode: str, strain: str) -> Dict[str, Any]:
    """
    Deterministic contextual prediction for UX adaptation only.
    Output is advisory; CONTROL/SECURITY remain authoritative.
    """
    if not isinstance(context_bundle, dict) or not context_bundle.get("prediction_enabled"):
        return {
            "enabled": False,
            "predicted_state": "prediction_disabled",
            "confidence": 0.0,
            "recommended_ux_mode": "guided" if mode == "interactive" else "quiet",
            "advisory_only": True,
        }

    signals = context_bundle.get("signals") if isinstance(context_bundle.get("signals"), dict) else {}
    voice = signals.get("voice") if isinstance(signals.get("voice"), dict) else {}
    video = signals.get("video") if isinstance(signals.get("video"), dict) else {}
    interaction = signals.get("interaction") if isinstance(signals.get("interaction"), dict) else {}

    score = 0.0
    if isinstance(voice.get("pause_ratio"), (int, float)) and float(voice.get("pause_ratio")) > 0.35:
        score += 0.25
    if isinstance(interaction.get("typing_hesitation"), (int, float)) and float(interaction.get("typing_hesitation")) > 0.4:
        score += 0.25
    if isinstance(interaction.get("correction_rate"), (int, float)) and float(interaction.get("correction_rate")) > 0.3:
        score += 0.2
    if isinstance(video.get("motion_level"), (int, float)) and float(video.get("motion_level")) > 0.6:
        score += 0.15
    if strain in {"high", "critical", "constrained"}:
        score += 0.15

    if score >= 0.65:
        predicted = "overload_risk"
        recommended = "recovery_guided"
    elif score >= 0.35:
        predicted = "fatigue_risk"
        recommended = "low_strain_guided"
    else:
        predicted = "stable"
        recommended = "guided" if mode == "interactive" else "quiet"

    return {
        "enabled": True,
        "predicted_state": predicted,
        "confidence": min(1.0, round(score, 3)),
        "recommended_ux_mode": recommended,
        "advisory_only": True,
        "presentation_only": True,
    }


if __name__ == "__main__":
    result = run_mama_proof()
    print("=" * 55)
    print("SARA MAMA: Gen1 PlainJain Baseline Proof")
    print("=" * 55)
    print(f"  Status : {result['status']}")
    print(f"  Reason : {result['reason']}")
    print("=" * 55)

# shunt_header: sara_mama_gen1_base
# evolution anchor: plainjain-first Mama baseline for Gen1 extensions


def adapt_amip_ux_mama(amip_payload: Optional[Dict[str, Any]] = None, result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Return a deterministic low-strain UX profile for interactive vs night_shift requests."""
    request = dict(amip_payload or {})
    budget = dict(request.get("resource_budget") or {})
    mode = str(request.get("mode") or "interactive").strip().lower()
    if mode not in {"interactive", "night_shift"}:
        mode = "interactive"
    strain = str(budget.get("strain") or "medium").strip().lower()
    if strain not in {"low", "medium", "high"}:
        strain = "medium"

    if mode == "night_shift":
        ux_profile = {
            "voice_first": True,
            "low_click": True,
            "full_feedback": False,
            "animations": False,
            "cognitive_load": "reduced",
            "status_style": "quiet_summary",
        }
    else:
        ux_profile = {
            "voice_first": True,
            "low_click": True,
            "full_feedback": True,
            "animations": False,
            "cognitive_load": "guided",
            "status_style": "interactive_summary",
        }

    reasoning_overlay = _build_reasoning_overlay(request=request, result=result, mode=mode, strain=strain)

    result_block = dict(result or {})
    control_generation_policy = result_block.get("generation_policy") if isinstance(result_block.get("generation_policy"), dict) else {}
    payload_block = request.get("payload") if isinstance(request.get("payload"), dict) else {}
    payload_generation_controls = payload_block.get("generation_controls") if isinstance(payload_block.get("generation_controls"), dict) else {}
    selected_profile = str(
        control_generation_policy.get("selected_profile")
        or payload_block.get("generation_profile")
        or "stable_probabilistic"
    )
    effective_controls = control_generation_policy.get("effective_controls") if isinstance(control_generation_policy.get("effective_controls"), dict) else payload_generation_controls
    if not isinstance(effective_controls, dict):
        effective_controls = {}

    generation_surface = {
        "requested_profile": str(control_generation_policy.get("requested_profile") or payload_block.get("generation_profile") or ""),
        "selected_profile": selected_profile,
        "probabilistic_enabled": bool(control_generation_policy.get("probabilistic_enabled", selected_profile != "strict_deterministic")),
        "repeatability_required": bool(payload_block.get("requires_repeatability", False)),
        "replay_mode": bool(payload_block.get("replay_mode", False) or payload_block.get("requires_repeatability", False)),
        "replay_key": str(payload_block.get("replay_key") or ""),
        "replay_seed": payload_block.get("replay_seed"),
        "effective_controls": effective_controls,
        "fallback_chain": list(control_generation_policy.get("fallback_chain") or []),
        "policy_reasons": list(control_generation_policy.get("reasons") or []),
    }

    phase1_surface = _phase1_osh_surface_mama(result)
    biometric_context = _extract_biometric_context_mama(amip_payload=amip_payload, result=result)
    contextual_prediction = _predict_contextual_state_mama(
        context_bundle=biometric_context,
        mode=mode,
        strain=strain,
    )

    return {
        "status": "READY",
        "mode": mode,
        "strain": strain,
        "routing_intent": str(request.get("routing_intent") or ""),
        "correlation_id": str(request.get("correlation_id") or ""),
        "ux_profile": ux_profile,
        "generation_surface": generation_surface,
        "phase1_surface": phase1_surface,
        "biometric_context": biometric_context,
        "contextual_prediction": contextual_prediction,
        "reasoning_overlay": reasoning_overlay,
        "reasoning_visible": bool(reasoning_overlay.get("visible")),
        "result_status": str((result or {}).get("status") or (result or {}).get("success") or "pending"),
    }


def _resolve_native_runtime_knobs_mama(summary: Dict[str, Any]) -> Dict[str, Any]:
    generation_surface = summary.get("generation_surface") if isinstance(summary.get("generation_surface"), dict) else {}
    selected = str(generation_surface.get("selected_profile") or "stable_probabilistic")
    controls = generation_surface.get("effective_controls") if isinstance(generation_surface.get("effective_controls"), dict) else {}
    mode = str(summary.get("mode") or "interactive")
    strain = str(summary.get("strain") or "medium")

    presets: Dict[str, Dict[str, Any]] = {
        "strict_deterministic": {
            "sampling_width": 1,
            "propagation_depth": 1,
            "stability_threshold": 0.96,
            "temperature": 0.0,
            "top_p": 1.0,
            "seed": 7,
            "executor_mode": "strict",
        },
        "stable_probabilistic": {
            "sampling_width": 2,
            "propagation_depth": 2,
            "stability_threshold": 0.9,
            "temperature": 0.22,
            "top_p": 0.9,
            "seed": None,
            "executor_mode": "stable",
        },
        "creative_probabilistic": {
            "sampling_width": 3,
            "propagation_depth": 3,
            "stability_threshold": 0.84,
            "temperature": 0.68,
            "top_p": 0.95,
            "seed": None,
            "executor_mode": "creative",
        },
    }
    knobs = dict(presets.get(selected, presets["stable_probabilistic"]))
    for key in ("temperature", "top_p", "seed"):
        if key in controls:
            knobs[key] = controls[key]

    if mode == "night_shift":
        knobs["sampling_width"] = min(int(knobs.get("sampling_width", 2)), 2)
        knobs["propagation_depth"] = min(int(knobs.get("propagation_depth", 2)), 2)
    if strain in {"high", "critical", "constrained"}:
        knobs["sampling_width"] = 1
        knobs["propagation_depth"] = min(int(knobs.get("propagation_depth", 2)), 2)

    knobs["selected_profile"] = selected
    knobs["probabilistic_enabled"] = bool(generation_surface.get("probabilistic_enabled", selected != "strict_deterministic"))
    knobs["replay_mode"] = bool(generation_surface.get("replay_mode", False))
    knobs["replay_key"] = str(generation_surface.get("replay_key") or "")
    knobs["replay_ledger_enabled"] = True
    knobs["correlation_id"] = str(summary.get("correlation_id") or "")
    if generation_surface.get("replay_seed") is not None:
        knobs["seed"] = generation_surface.get("replay_seed")
    return knobs


def _apply_native_runtime_policy_mama(
    summary: Dict[str, Any],
    ai_result: Optional[Dict[str, Any]],
    amip_payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    effective_result = dict(ai_result or {})
    runtime_knobs = _resolve_native_runtime_knobs_mama(summary)
    request_payload = (amip_payload or {}).get("payload") if isinstance((amip_payload or {}).get("payload"), dict) else {}
    machine_profile = (amip_payload or {}).get("machine_profile") if isinstance((amip_payload or {}).get("machine_profile"), dict) else {}

    if str(effective_result.get("selected_model") or "").strip().lower() in {"", "plainjain_native", "plainjain"}:
        model_output = effective_result.get("model_output") if isinstance(effective_result.get("model_output"), dict) else {}
        model_output.update({
            "runtime_policy_applied": True,
            "executor_mode": runtime_knobs.get("executor_mode"),
            "sampling_width": runtime_knobs.get("sampling_width"),
            "propagation_depth": runtime_knobs.get("propagation_depth"),
            "stability_threshold": runtime_knobs.get("stability_threshold"),
            "notes": str(model_output.get("notes") or "PlainJain native runtime controls applied by MAMA generation policy."),
        })

        executor_mod = _load_plainjain_executor_mod_mama()
        if executor_mod is not None and hasattr(executor_mod, "execute_plainjain"):
            try:
                native_exec = executor_mod.execute_plainjain(
                    payload=request_payload,
                    runtime_knobs=runtime_knobs,
                    machine_profile=machine_profile,
                )
                if isinstance(native_exec, dict):
                    model_output["generated_text"] = str(native_exec.get("generated_text") or model_output.get("generated_text") or "")
                    effective_result["native_execution"] = native_exec
            except Exception as e:
                effective_result["native_execution"] = {
                    "success": False,
                    "engine": "plainjain_executor",
                    "error": str(e),
                }

        effective_result["model_output"] = model_output
        effective_result["selected_model"] = "plainjain_native"

    effective_result["native_runtime"] = runtime_knobs
    return {"result": effective_result, "runtime_knobs": runtime_knobs}


def summarize_bucey_shunt_mama(shunt_response: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Summarize a shunt-wrapped response for ADA-friendly display surfaces."""
    envelope = dict(shunt_response or {})
    amip_payload = envelope.get("amip_payload") if isinstance(envelope.get("amip_payload"), dict) else {}
    result = envelope.get("result") if isinstance(envelope.get("result"), dict) else {}
    summary = adapt_amip_ux_mama(amip_payload=amip_payload, result=result)
    runtime_applied = _apply_native_runtime_policy_mama(summary=summary, ai_result=result, amip_payload=amip_payload)
    summary["native_runtime"] = runtime_applied["runtime_knobs"]
    if not summary.get("reasoning_visible"):
        summary["reasoning_visibility"] = "hidden_until_control_and_security_validation"
    phase1_surface = summary.get("phase1_surface") if isinstance(summary.get("phase1_surface"), dict) else _phase1_osh_surface_mama(result)
    summary.update({
        "ami_id": str(envelope.get("ami_id") or ""),
        "request_id": str(envelope.get("request_id") or ""),
        "phase1_outcome": str(phase1_surface.get("phase1_outcome") or "pending"),
        "osh_pipeline": phase1_surface,
        "message": "AMIP-aware summary prepared for low-strain MAMA presentation.",
    })
    return summary


def present_amipi_result_mama(amip_payload: Optional[Dict[str, Any]] = None, ai_result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Normalize AMIPI results for low-strain presentation without changing backend behavior."""
    summary = adapt_amip_ux_mama(amip_payload=amip_payload, result=ai_result)
    runtime_applied = _apply_native_runtime_policy_mama(summary=summary, ai_result=ai_result, amip_payload=amip_payload)
    summary["native_runtime"] = runtime_applied["runtime_knobs"]
    if not summary.get("reasoning_visible"):
        summary["reasoning_visibility"] = "hidden_until_control_and_security_validation"
    phase1_surface = summary.get("phase1_surface") if isinstance(summary.get("phase1_surface"), dict) else _phase1_osh_surface_mama(ai_result)
    summary["message"] = "Internal AI result normalized for MAMA display."
    summary["amipi_result"] = runtime_applied["result"]
    summary["phase1_outcome"] = str(phase1_surface.get("phase1_outcome") or "pending")
    summary["osh_pipeline"] = phase1_surface
    return summary


def query_replay_ledger_mama(
    replay_key: str = "",
    correlation_id: str = "",
    prompt_hash_prefix: str = "",
    output_hash_prefix: str = "",
    limit: int = 20,
    latest_first: bool = True,
    summary_only: bool = False,
    csv_path: str = "",
) -> Dict[str, Any]:
    """Convenience wrapper around replay_ledger_query tool for MAMA-side continuity inspection."""
    tool_path = os.path.join(os.path.dirname(__file__), "tools", "replay_ledger_query.py")
    if not os.path.exists(tool_path):
        return {
            "success": False,
            "error": "replay_ledger_query tool not found",
            "tool_path": tool_path,
        }

    try:
        spec = importlib.util.spec_from_file_location("sara_mama_replay_ledger_tool", tool_path)
        if spec is None or spec.loader is None:
            return {"success": False, "error": "unable to load replay_ledger_query tool"}
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        ledger_path = mod._default_ledger_path() if hasattr(mod, "_default_ledger_path") else ""
        entries = mod._load_entries(ledger_path) if hasattr(mod, "_load_entries") else []
        filtered = mod._filter_entries(
            entries,
            replay_key=str(replay_key or "").strip(),
            correlation_id=str(correlation_id or "").strip(),
            prompt_hash=str(prompt_hash_prefix or "").strip(),
            output_hash=str(output_hash_prefix or "").strip(),
        ) if hasattr(mod, "_filter_entries") else []

        filtered.sort(key=lambda x: str(x.get("ts", "")), reverse=bool(latest_first))
        selected = filtered[: max(1, int(limit))]
        summary = mod._build_summary(filtered) if hasattr(mod, "_build_summary") else {"count": len(filtered)}

        csv_written = ""
        if csv_path and hasattr(mod, "_write_csv"):
            csv_written = mod._write_csv(str(csv_path), selected)

        payload: Dict[str, Any] = {
            "success": True,
            "ledger": ledger_path,
            "summary": summary,
        }
        if csv_written:
            payload["csv"] = csv_written
        if not summary_only:
            payload["records"] = selected
        return payload
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "tool_path": tool_path,
        }


def compare_replay_ledgers_mama(
    ledger_a: str,
    ledger_b: str,
    replay_key: str = "",
    correlation_id: str = "",
    limit: int = 200,
    summary_only: bool = False,
    csv_path: str = "",
) -> Dict[str, Any]:
    """Compare two replay ledgers (desktop vs ARM/wearable) for continuity by prompt hash/output hash."""
    tool_path = os.path.join(os.path.dirname(__file__), "tools", "replay_ledger_compare.py")
    if not os.path.exists(tool_path):
        return {
            "success": False,
            "error": "replay_ledger_compare tool not found",
            "tool_path": tool_path,
        }

    try:
        spec = importlib.util.spec_from_file_location("sara_mama_replay_compare_tool", tool_path)
        if spec is None or spec.loader is None:
            return {"success": False, "error": "unable to load replay_ledger_compare tool"}
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        if not hasattr(mod, "_load_entries") or not hasattr(mod, "_filter") or not hasattr(mod, "_compare"):
            return {"success": False, "error": "replay_ledger_compare tool missing expected functions"}

        a_all = mod._load_entries(str(ledger_a))
        b_all = mod._load_entries(str(ledger_b))
        a_rows = mod._filter(a_all, str(replay_key or "").strip(), str(correlation_id or "").strip())
        b_rows = mod._filter(b_all, str(replay_key or "").strip(), str(correlation_id or "").strip())
        comparisons, summary = mod._compare(a_rows, b_rows)
        selected = comparisons[: max(1, int(limit))]

        csv_written = ""
        if csv_path and hasattr(mod, "_write_csv"):
            csv_written = mod._write_csv(str(csv_path), selected)

        payload: Dict[str, Any] = {
            "success": True,
            "ledger_a": str(ledger_a),
            "ledger_b": str(ledger_b),
            "summary": summary,
        }
        if csv_written:
            payload["csv"] = csv_written
        if not summary_only:
            payload["comparisons"] = selected
        return payload
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "tool_path": tool_path,
        }


# --- Artifact JSON writers (result.meta.json, distant_end.json, master_result.json) ---
def _write_mama_artifacts(status: str, reached: bool, reason: str) -> None:
    """Write/update the three pillar artifact JSON files for MAMA."""
    import json as _json
    _here = os.path.dirname(os.path.abspath(__file__))
    _local = {
        "pillar": "sara_mama",
        "file": "sara_mamagen1.py",
        "status": status,
        "reached": reached,
        "reason": reason,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    _distant = {
        "pillar": "sara_mama",
        "file": "sara_mamagen1.py",
        "status": status,
        "reached": reached,
        "note": reason,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    _master = {"pillar": "sara_mama", "final_status": status, "local": _local, "distant": _distant}
    for fname, obj in [("result.meta.json", _local), ("distant_end.json", _distant), ("master_result.json", _master)]:
        try:
            with open(os.path.join(_here, fname), "w", encoding="utf-8") as f:
                _json.dump(obj, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

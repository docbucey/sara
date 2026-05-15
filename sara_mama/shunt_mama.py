"""Shunt FSM, entrypoint, ACT-mapped functions, and header validation for MAMA."""

import os
from typing import Any, Dict

try:
    from sara_common import validate_shunt_header as _common_validate_shunt_header  # type: ignore
except ImportError:
    _common_validate_shunt_header = None

from .ledger_mama import MamaLedger
from .plainjain_mama import PlainJainMama


class ShuntFSM:
    def __init__(self, states: Dict[str, int], transitions: Dict[str, Any]):
        self.states = states
        self.transitions = transitions


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


def validate_shunt_header(payload: dict) -> bool:
    """
    Enforces shunt header contract on inbound/outbound actions.
    """
    if _common_validate_shunt_header is not None:
        return _common_validate_shunt_header(payload)
    required_fields = ["shunt_id", "source_pillar", "target_pillar", "timestamp", "intent", "payload", "context_tags", "requires_response"]
    return all(field in payload for field in required_fields)


def mama_shunt_entrypoint(command: str, payload: dict) -> dict:
    """
    Single entrypoint for all cross-pillar actions. Applies header validation and routes to FSM.
    """
    if not validate_shunt_header(payload):
        return {"success": False, "error": "Invalid shunt header"}

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
        result = fn(payload)
    except Exception as e:
        return {"success": False, "error": f"Dispatch error: {e}", "action_code": act_code, "function": fn.__name__, "out_route": out_route}
    return {"success": True, "action_code": act_code, "function": fn.__name__, "out_route": out_route, "result": result}


def snapshot(envelope: dict) -> dict:
    """ACT 00 \u2014 STORE: take a memory snapshot and append to MamaLedger."""
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
    """ACT 01 \u2014 RETURN: compute diff of ledger entries vs prior accepted state."""
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
        prev, curr = entries[-2], entries[-1]
        changed = {k: {"from": prev.get(k), "to": curr.get(k)} for k in set(list(prev.keys()) + list(curr.keys())) if prev.get(k) != curr.get(k)}
        return {"success": True, "diff": changed, "task_type": task_type, "compared": [prev.get("ts"), curr.get("ts")]}
    except Exception as e:
        return {"success": False, "error": str(e), "diff": True}


def persist(envelope: dict) -> dict:
    """ACT 10 \u2014 STORE: persist memory packet to MamaLedger as accepted state."""
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
    """ACT 11 \u2014 No operation."""
    return {"success": True, "noop": True, "shunt_id": envelope.get("shunt_id", "")}

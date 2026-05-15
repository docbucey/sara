"""
SARA Control — FSM state constants, transition validation, logging, and execution.
Extracted from sara_controlgen1.py.
"""
from typing import Dict, Any

CONTROL_STATE_COMPRESS = "CONTROL_COMPRESS"
CONTROL_STATE_DECOMPRESS = "CONTROL_DECOMPRESS"
CONTROL_STATE_EXTRACT_FULL = "CONTROL_EXTRACT_FULL"
CONTROL_STATE_EXTRACT_TARGET = "CONTROL_EXTRACT_TARGET"
CONTROL_STATE_SEARCH = "CONTROL_SEARCH"


def control_log_transition(prev_state: str, next_state: str, action: str) -> None:
    """
    Metadata-only FSM transition logger.
    No raw data, no sensitive payloads.
    """
    try:
        print(f"[CONTROL FSM] {prev_state} → {next_state} via {action}")
    except Exception:
        pass


def control_validate_transition(current_state: str, action: str) -> str:
    """
    Enforce strict FSM transitions for Clerk → CONTROL actions.
    Returns the next CONTROL state or raises an error.
    """

    if action == "search":
        return CONTROL_STATE_SEARCH

    if action == "compress":
        return CONTROL_STATE_COMPRESS

    if action == "decompress":
        return CONTROL_STATE_DECOMPRESS

    if action == "extract_full":
        if current_state != CONTROL_STATE_DECOMPRESS:
            raise ValueError("extract_full requires prior decompress state")
        return CONTROL_STATE_EXTRACT_FULL

    if action == "extract_target":
        if current_state not in (CONTROL_STATE_DECOMPRESS, CONTROL_STATE_SEARCH):
            raise ValueError("extract_target requires decompress or search state")
        return CONTROL_STATE_EXTRACT_TARGET

    raise ValueError(f"Unknown or invalid action: {action}")


def control_execute_with_fsm(current_state: str, action: str, handler, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Wrap CONTROL executor calls with strict FSM validation + logging.
    """
    try:
        next_state = control_validate_transition(current_state, action)
        control_log_transition(current_state, next_state, action)
        result = handler(payload)
        result["fsm_state"] = next_state
        return result
    except Exception as e:
        return {
            "status": "ERROR",
            "action": action,
            "error": str(e),
            "fsm_state": current_state,
        }

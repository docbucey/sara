"""SLM entrypoint and action functions for MAMA."""

import importlib
import json
import os
from datetime import datetime

from .shunt_mama import validate_shunt_header


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
    try:
        audit_dir = os.path.join(os.path.dirname(__file__), 'audit_logs')
        os.makedirs(audit_dir, exist_ok=True)
        audit_file = os.path.join(audit_dir, 'terminal_window_audit.log')
        with open(audit_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(audit_entry) + '\n')
    except Exception:
        pass
    return result


def ide_protocol_action(action: str, payload: dict):
    """
    Mediates IDE protocol actions: validates, logs, and forwards to CONTROL for enforcement/persistence.
    """
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
    try:
        audit_dir = os.path.join(os.path.dirname(__file__), 'audit_logs')
        os.makedirs(audit_dir, exist_ok=True)
        audit_file = os.path.join(audit_dir, 'ide_protocol_audit.log')
        with open(audit_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(audit_entry) + '\n')
    except Exception:
        pass
    return result


def device_input_action(action: str, payload: dict):
    """
    Mediates device input (Smithy) actions: validates, logs, and forwards to CONTROL for enforcement/persistence.
    """
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
    try:
        audit_dir = os.path.join(os.path.dirname(__file__), 'audit_logs')
        os.makedirs(audit_dir, exist_ok=True)
        audit_file = os.path.join(audit_dir, 'learning_audit.log')
        with open(audit_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(audit_entry) + '\n')
    except Exception:
        pass
    return result


def mama_stagework_action(action: str, path: str, data=None):
    """
    Mediates Stagework (Office Suite) actions: validates, logs, and forwards to CONTROL's office_file_action.
    """
    if isinstance(data, dict) and 'shunt_id' in data:
        if not validate_shunt_header(data):
            return {"success": False, "error": "Invalid shunt header"}

    audit_entry = {
        'timestamp': datetime.now().isoformat(),
        'stagework_action': action,
        'path': path,
        'user': os.getenv('USER', 'system')
    }

    try:
        control_mod = importlib.import_module('claywork.saragen0finish.sara_control.sara_controlgen1')
        result = control_mod.office_file_action(action, path, data)
    except Exception as e:
        result = {"success": False, "error": f"CONTROL routing failed: {e}"}

    audit_entry['result'] = 'PASS' if result.get('success') else 'FAIL'
    audit_entry['details'] = result.get('error', result.get('info', ''))

    try:
        audit_dir = os.path.join(os.path.dirname(__file__), 'audit_logs')
        os.makedirs(audit_dir, exist_ok=True)
        audit_file = os.path.join(audit_dir, 'stagework_audit.log')
        with open(audit_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(audit_entry) + '\n')
    except Exception:
        pass
    return result

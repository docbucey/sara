# sara_security/shunt_sec.py
# Extracted from sara_securitygen1.py — shunt entrypoint and ACT-mapped functions.
# Named shunt_sec.py to avoid collision with stdlib.

import os
from datetime import datetime, timezone
from typing import Dict, Any

try:
    from sara_common.types import SecurityOutcome
except ImportError:
    pass

SECURITY_OUTCOME_ALLOW = "ALLOW"
SECURITY_OUTCOME_CHALLENGE = "CHALLENGE"
SECURITY_OUTCOME_QUARANTINE = "QUARANTINE"
SECURITY_OUTCOME_LOCKDOWN = "LOCKDOWN"

try:
    from .sara_securitygen1 import _SECURITY_KEEP_STATE
except ImportError:
    try:
        from sara_securitygen1 import _SECURITY_KEEP_STATE
    except ImportError:
        _SECURITY_KEEP_STATE: Dict[str, Any] = {
            "vault_state": "sealed",
            "control_lockdown": False,
            "last_outcome": SECURITY_OUTCOME_ALLOW,
            "volatile_cache": {},
            "pending_challenges": [],
            "incident_history": [],
            "posture": {},
            "stables_sessions": {},
            "trust_policy": {},
            "vnce_last_attested": {},
        }

try:
    from .trust import _load_trust_policy_sec
except ImportError:
    try:
        from trust import _load_trust_policy_sec
    except ImportError:
        def _load_trust_policy_sec():
            return {
                "allowed_environments": ["local", "local_only", "trusted_local", "interactive"],
                "trusted_hosts": ["localhost", "127.0.0.1", "::1", "local_only"],
            }

try:
    from .stables import stables_validate_session_sec
except ImportError:
    try:
        from stables import stables_validate_session_sec
    except ImportError:
        def stables_validate_session_sec(**kw):
            return {"applied": False, "outcome": SECURITY_OUTCOME_ALLOW}


def validate_shunt_header(payload: dict) -> bool:
    """
    Enforces shunt header contract on inbound/outbound actions.
    """
    required_fields = ["shunt_id", "source_pillar", "target_pillar", "timestamp", "intent", "payload", "context_tags", "requires_response"]
    return all(field in payload for field in required_fields)


def audit_gate(envelope: dict) -> dict:
    """ACT 00 — Real allow/deny/challenge decision using trust policy and STABLES."""
    inner = dict(envelope.get("payload", {}))
    context_tags = list(envelope.get("context_tags", []))
    # Extract environment and session context from envelope
    environment = str(inner.get("environment") or "local_only")
    host = str(inner.get("host") or "localhost")
    session_id = str(envelope.get("shunt_id") or inner.get("session_id") or "")
    # Check trust posture (scout_house_posture_sec may not be defined yet — use policy check directly)
    policy = _load_trust_policy_sec()
    allowed_env = {str(v).strip().lower() for v in (policy.get("allowed_environments") or [])}
    trusted_hosts = {str(v).strip().lower() for v in (policy.get("trusted_hosts") or [])}
    env_ok = environment.lower() in allowed_env
    host_ok = host.lower() in trusted_hosts
    # STABLES validation if session context present
    stables_result = {}
    if session_id or any(t in {"vnce", "envoy", "session"} for t in context_tags):
        stables_result = stables_validate_session_sec(
            shunt_envelope=envelope,
            context={"session_id": session_id, "environment": environment, "host": host},
        )
        stables_outcome = stables_result.get("outcome", SECURITY_OUTCOME_ALLOW)
        if stables_outcome in {SECURITY_OUTCOME_QUARANTINE, SECURITY_OUTCOME_LOCKDOWN}:
            return {"outcome": stables_outcome, "reason": stables_result.get("reason", "STABLES:deny"),
                    "stables": stables_result, "audit_gate": True}
        if stables_outcome == SECURITY_OUTCOME_CHALLENGE:
            return {"outcome": SECURITY_OUTCOME_CHALLENGE, "reason": stables_result.get("reason", "STABLES:challenge"),
                    "stables": stables_result, "audit_gate": True}
    if not env_ok or not host_ok:
        _SECURITY_KEEP_STATE["last_outcome"] = SECURITY_OUTCOME_CHALLENGE
        return {"outcome": SECURITY_OUTCOME_CHALLENGE, "reason": "AUDIT_GATE:env/host not trusted",
                "environment": environment, "host": host, "stables": stables_result, "audit_gate": True}
    _SECURITY_KEEP_STATE["last_outcome"] = SECURITY_OUTCOME_ALLOW
    return {"outcome": SECURITY_OUTCOME_ALLOW, "reason": "AUDIT_GATE:pass",
            "environment": environment, "host": host, "stables": stables_result, "audit_gate": True}


def quarantine(envelope: dict) -> dict:
    """ACT 01 — Quarantine the shunt envelope; log to incident history and return QUARANTINE outcome."""
    import datetime as _dt
    record = {
        "ts": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "shunt_id": envelope.get("shunt_id", ""),
        "source_pillar": envelope.get("source_pillar", "UNKNOWN"),
        "intent": envelope.get("intent", ""),
        "context_tags": list(envelope.get("context_tags", [])),
        "reason": "QUARANTINE:ACT01",
        "outcome": SECURITY_OUTCOME_QUARANTINE,
    }
    _SECURITY_KEEP_STATE.setdefault("incident_history", []).append(record)
    _SECURITY_KEEP_STATE["last_outcome"] = SECURITY_OUTCOME_QUARANTINE
    # Write to audit log file if possible
    try:
        _logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
        os.makedirs(_logs_dir, exist_ok=True)
        _log_path = os.path.join(_logs_dir, "security_quarantine_log.ndjson")
        with open(_log_path, "a", encoding="utf-8") as f:
            import json as _json
            f.write(_json.dumps(record) + "\n")
    except Exception:
        pass
    return {"outcome": SECURITY_OUTCOME_QUARANTINE, "record": record, "quarantine": True}


def scan(envelope: dict) -> dict:
    """ACT 10 — Threat scan: check payload for known threat indicators."""
    inner = dict(envelope.get("payload", {}))
    threat_patterns = ["exec(", "eval(", "__import__", "subprocess", "os.system", "rm -rf", "DROP TABLE", "SELECT * FROM"]
    # Scan the string representation of the inner payload
    try:
        import json as _json
        payload_str = _json.dumps(inner)
    except Exception:
        payload_str = str(inner)
    threats_found = [p for p in threat_patterns if p.lower() in payload_str.lower()]
    if threats_found:
        _SECURITY_KEEP_STATE["last_outcome"] = SECURITY_OUTCOME_QUARANTINE
        return {"outcome": SECURITY_OUTCOME_QUARANTINE, "threats": threats_found,
                "reason": "SCAN:threat_pattern_detected", "scan": True}
    _SECURITY_KEEP_STATE["last_outcome"] = SECURITY_OUTCOME_ALLOW
    return {"outcome": SECURITY_OUTCOME_ALLOW, "threats": [], "reason": "SCAN:clean", "scan": True}


def noop_action(envelope: dict) -> dict:
    """ACT 11 — No operation; returns envelope metadata."""
    return {"success": True, "noop": True, "shunt_id": envelope.get("shunt_id", "")}


def security_shunt_entrypoint(command: str, payload: dict) -> dict:
    """
    Single entrypoint for all cross-pillar actions. Applies header validation and routes to FSM.
    """
    if not validate_shunt_header(payload):
        return {"success": False, "error": "Invalid shunt header"}

    # ACT-based dispatch logic (stub: no SECURITY codes in actionmap.json)
    act_map = {
        "00": (audit_gate, "RETURN"),
        "01": (quarantine, "RETURN"),
        "10": (scan, "RETURN"),
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

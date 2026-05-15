# sara_security/sheriff.py
# Extracted from sara_securitygen1.py — structured audit event record.

import os
import json
from typing import Optional, Dict, Any

try:
    from sara_common.types import SecurityOutcome
except ImportError:
    pass

try:
    from .trust import _iso_now_sec, _json_safe_sec
except ImportError:
    try:
        from trust import _iso_now_sec, _json_safe_sec
    except ImportError:
        from datetime import datetime, timezone

        def _iso_now_sec() -> str:
            return datetime.now(timezone.utc).isoformat()

        def _json_safe_sec(value):
            if value is None or isinstance(value, (str, int, float, bool)):
                return value
            if isinstance(value, dict):
                return {str(k): _json_safe_sec(v) for k, v in value.items()}
            if isinstance(value, list):
                return [_json_safe_sec(v) for v in value]
            return str(value)


def sheriff_audit(event_type, actor, decision, reason, details: Optional[Dict[str, Any]] = None, **extra):
    """Writes a single audit line; returns the event dict with optional structured metadata."""
    event = {
        "ts": _iso_now_sec(),
        "event_type": event_type,
        "actor": actor,
        "decision": decision,
        "reason": reason,
    }
    if isinstance(details, dict) and details:
        event["details"] = _json_safe_sec(details)
    if extra:
        event.update(_json_safe_sec(extra))
    audit_dir = os.path.join(os.path.dirname(__file__), "logs")
    os.makedirs(audit_dir, exist_ok=True)
    audit_path = os.path.join(audit_dir, "security_audit.ndjson")
    with open(audit_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    return event

"""SDK Shunt: local BuceyShunt envelope construction and dispatch."""
import uuid
from typing import Any, Dict, Optional
from datetime import datetime, timezone

try:
    from sara_common.shunt_header import validate_shunt_header, SHUNT_REQUIRED_FIELDS
except ImportError:
    SHUNT_REQUIRED_FIELDS = ["shunt_id", "source_pillar", "target_pillar", "timestamp", "intent", "payload", "context_tags", "requires_response"]
    def validate_shunt_header(payload: dict) -> bool:
        return all(f in payload for f in SHUNT_REQUIRED_FIELDS)


def build_local_bucey_shunt(
    intent: str,
    payload: Dict[str, Any],
    target_pillar: str = "CONTROL",
    source_pillar: str = "SDK",
    context_tags: Optional[list] = None,
    requires_response: bool = True,
) -> Dict[str, Any]:
    """Build a BuceyShunt envelope from SDK for local dispatch to CONTROL."""
    envelope = {
        "shunt_id": str(uuid.uuid4()),
        "source_pillar": source_pillar.upper(),
        "target_pillar": target_pillar.upper(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "intent": intent,
        "payload": payload,
        "context_tags": context_tags or [],
        "requires_response": requires_response,
    }
    return envelope


def send_bucey_shunt(envelope: Dict[str, Any], transport: str = "local") -> Dict[str, Any]:
    """Validate and dispatch a BuceyShunt envelope. Local-only for now."""
    if not validate_shunt_header(envelope):
        return {"success": False, "error": "SDK:shunt-header-validation-failed"}
    if transport != "local":
        return {"success": False, "error": f"SDK:transport-{transport}-not-implemented"}
    return {
        "success": True,
        "status": "SHUNT_DISPATCHED",
        "shunt_id": envelope.get("shunt_id"),
        "target_pillar": envelope.get("target_pillar"),
        "note": "SDK local dispatch ready; CONTROL routing pending.",
    }

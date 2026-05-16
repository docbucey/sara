"""Android shunt adapter stubs for SARA SDK Gen1."""

from __future__ import annotations

from typing import Any, Dict


class AndroidShuntAdapter:
    """Placeholder adapter for future Android-to-shunt envelopes."""

    def build_request(self, action: str, payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
        return {
            "status": "stub",
            "platform": "android",
            "action": action,
            "payload": payload or {},
        }

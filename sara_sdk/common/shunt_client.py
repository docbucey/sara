"""Shared shunt client stubs for SARA SDK Gen1."""

from __future__ import annotations

from typing import Any, Dict, Optional
from datetime import datetime, timezone
import uuid


class ShuntClient:
    """Placeholder shared client for future SDK-to-Control shunt traffic."""

    def _iso_now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def build_local_bucey_shunt(
        self,
        ami_id: str,
        amip_payload: Dict[str, Any],
        profile_ref: Optional[Dict[str, Any]] = None,
        correlation_id: str = "",
    ) -> Dict[str, Any]:
        return {
            "header": {
                "shunt_version": "gen1",
                "shunt_id": str(uuid.uuid4()),
                "timestamp_utc": self._iso_now(),
            },
            "fsm_bits": {
                "state": str(amip_payload.get("mode", "interactive")),
                "routing_policy": "local_only",
                "strain_policy": str(amip_payload.get("resource_budget", {}).get("strain", "medium")),
            },
            "ami_id": str(ami_id or ""),
            "profile_ref": dict(profile_ref or {}),
            "correlation_id": str(correlation_id or amip_payload.get("correlation_id", "")),
            "request_id": str(uuid.uuid4()),
            "transport_policy": {
                "local_only": True,
                "response_expected": True,
                "allow_automation": amip_payload.get("mode") == "night_shift",
            },
            "amip_payload": dict(amip_payload or {}),
        }

    def send(self, envelope: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "stub",
            "note": "No runtime binding is implemented yet.",
            "envelope": envelope,
        }

    def send_bucey_shunt(
        self,
        ami_id: str,
        amip_payload: Dict[str, Any],
        profile_ref: Optional[Dict[str, Any]] = None,
        correlation_id: str = "",
    ) -> Dict[str, Any]:
        envelope = self.build_local_bucey_shunt(
            ami_id=ami_id,
            amip_payload=amip_payload,
            profile_ref=profile_ref,
            correlation_id=correlation_id,
        )
        return self.send(envelope)

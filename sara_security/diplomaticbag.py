from typing import Dict, Any
from enum import Enum

class EnforcementDecision(Enum):
    ALLOW = "ALLOW"
    RESTRICT = "RESTRICT"
    DENY = "DENY"
    ALERT = "ALERT"

class DiplomaticBag:
    def __init__(self, logger=None):
        self.logger = logger

    def inspect_pouch(self, pouch: Dict[str, Any]) -> Dict[str, Any]:
        decision = EnforcementDecision.ALLOW
        reason = "skeleton-default"
        capability_map = {
            "cue_out": True,
            "cue_in": True,
            "log_emit": True,
            "location_emit": True
        }

        if not pouch or not isinstance(pouch, dict):
            decision = EnforcementDecision.DENY
            reason = "invalid_pouch"
            capability_map = {k: False for k in capability_map}
            self._log(pouch, decision, reason)
            return {
                "decision": decision.value,
                "reason": reason,
                "capability_map": capability_map
            }

        geofence_result = pouch.get("geofence_result")
        compliance = pouch.get("compliance", {})

        if geofence_result == "OUT_OF_RANGE":
            decision = EnforcementDecision.DENY
            reason = "out_of_range"
            capability_map = {k: False for k in capability_map}
        elif geofence_result == "OUTSIDE":
            decision = EnforcementDecision.RESTRICT
            reason = "outside_allowed_zone"
            capability_map["cue_out"] = False
        elif compliance.get("medical") == "NON_COMPLIANT":
            decision = EnforcementDecision.RESTRICT
            reason = "medical_non_compliant"
            capability_map["cue_out"] = False

        self._log(pouch, decision, reason)
        return {
            "decision": decision.value,
            "reason": reason,
            "capability_map": capability_map
        }

    def _log(self, pouch: Dict[str, Any], decision: EnforcementDecision, reason: str):
        if self.logger:
            self.logger.info({
                "device_id": pouch.get("device_id"),
                "role": pouch.get("role"),
                "decision": decision.value,
                "reason": reason,
                "geofence_result": pouch.get("geofence_result"),
                "compliance": pouch.get("compliance")
            })

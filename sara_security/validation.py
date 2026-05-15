# sara_security/validation.py
# Extracted from sara_securitygen1.py — payload and envelope validation.

import re
from typing import Optional, Dict, List, Any

try:
    from sara_common.types import SecurityOutcome
except ImportError:
    pass

SECURITY_OUTCOME_ALLOW = "ALLOW"
SECURITY_OUTCOME_CHALLENGE = "CHALLENGE"
SECURITY_OUTCOME_QUARANTINE = "QUARANTINE"
SECURITY_OUTCOME_LOCKDOWN = "LOCKDOWN"

try:
    from .stables import stables_validate_session_sec
except ImportError:
    try:
        from stables import stables_validate_session_sec
    except ImportError:
        def stables_validate_session_sec(**kw):
            return {"applied": False, "outcome": SECURITY_OUTCOME_ALLOW}

try:
    from .paladin import paladin_gate
except ImportError:
    try:
        from paladin import paladin_gate
    except ImportError:
        def paladin_gate(text):
            return True, "PALADIN:ALLOW:stub"

_AMI_ID_RE = re.compile(r"^[0-9A-Fa-f]{4}\s[0-9A-Fa-f]{8}\s[0-9A-Fa-f]{4}$")
_AMIP_REQUIRED_FIELDS = {
    "amip_version",
    "mode",
    "routing_intent",
    "resource_budget",
    "payload",
    "machine_profile",
    "correlation_id",
}


def validate_ami_id_sec(ami_id: str) -> Dict[str, Any]:
    value = str(ami_id or "").strip()
    valid = bool(_AMI_ID_RE.match(value))
    return {
        "valid": valid,
        "ami_id": value,
        "reason": "AMI:valid" if valid else "AMI:invalid-format",
    }


def validate_amip_payload_sec(amip_request: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(amip_request, dict):
        return {"valid": False, "reason": "AMIP:payload-not-dict", "errors": ["payload must be a dict"]}

    errors: List[str] = []
    missing = sorted(field for field in _AMIP_REQUIRED_FIELDS if field not in amip_request)
    if missing:
        errors.append(f"missing_fields:{','.join(missing)}")

    if str(amip_request.get("amip_version", "")) != "0.1":
        errors.append("invalid_amip_version")

    mode = str(amip_request.get("mode", "")).strip().lower()
    if mode not in {"interactive", "night_shift"}:
        errors.append("invalid_mode")

    routing_intent = str(amip_request.get("routing_intent", "")).strip()
    if not routing_intent:
        errors.append("missing_routing_intent")

    budget = amip_request.get("resource_budget")
    if not isinstance(budget, dict):
        errors.append("resource_budget_not_dict")
    else:
        if str(budget.get("strain", "")).strip().lower() not in {"low", "medium", "high"}:
            errors.append("invalid_strain")
        if not isinstance(budget.get("tokens", None), int):
            errors.append("tokens_not_int")
        if not isinstance(budget.get("runtime_ms", None), int):
            errors.append("runtime_ms_not_int")

    machine_profile = amip_request.get("machine_profile")
    if not isinstance(machine_profile, dict) or not str(machine_profile.get("profile_id", "")).strip():
        errors.append("invalid_machine_profile")

    correlation_id = str(amip_request.get("correlation_id", "")).strip()
    if not correlation_id:
        errors.append("missing_correlation_id")

    errors.extend(_validate_self_evolve_signature_sec(amip_request))
    errors.extend(_validate_contextual_routing_signals_sec(amip_request))

    return {
        "valid": len(errors) == 0,
        "reason": "AMIP:valid" if not errors else "AMIP:invalid",
        "errors": errors,
        "routing_intent": routing_intent,
        "mode": mode or "interactive",
        "correlation_id": correlation_id,
    }


def validate_bucey_shunt_sec(shunt_envelope: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(shunt_envelope, dict):
        return {"valid": False, "reason": "BUCEY:envelope-not-dict", "errors": ["envelope must be a dict"]}

    errors: List[str] = []
    header = shunt_envelope.get("header")
    if not isinstance(header, dict):
        errors.append("missing_header")

    ami_validation = validate_ami_id_sec(shunt_envelope.get("ami_id", ""))
    if not ami_validation.get("valid"):
        errors.append("invalid_ami_id")

    if "amip_payload" not in shunt_envelope or not isinstance(shunt_envelope.get("amip_payload"), dict):
        errors.append("missing_amip_payload")

    if not str(shunt_envelope.get("correlation_id", "")).strip():
        errors.append("missing_correlation_id")

    if not str(shunt_envelope.get("request_id", "")).strip():
        errors.append("missing_request_id")

    stables = stables_validate_session_sec(
        shunt_envelope=shunt_envelope,
        amip_request=shunt_envelope.get("amip_payload") if isinstance(shunt_envelope.get("amip_payload"), dict) else {},
        metadata_only=True,
    )

    return {
        "valid": len(errors) == 0,
        "reason": "BUCEY:valid" if not errors else "BUCEY:invalid",
        "errors": errors,
        "ami_validation": ami_validation,
        "stables": stables,
    }


def validate_mail_transport_sec(amip_request: Dict[str, Any]) -> Dict[str, Any]:
    request = dict(amip_request or {})
    routing_intent = str(request.get("routing_intent") or "").strip().lower()
    payload = request.get("payload") if isinstance(request.get("payload"), dict) else {}
    core_config = payload.get("core_config") if isinstance(payload.get("core_config"), dict) else {}

    allowed_intents = {"mail.smtp.send", "mail.imap.fetch"}
    if routing_intent not in allowed_intents:
        return {
            "valid": False,
            "reason": "MAIL:unsupported-routing-intent",
            "routing_intent": routing_intent,
        }

    if routing_intent == "mail.smtp.send":
        email_data = payload.get("email_data") if isinstance(payload.get("email_data"), dict) else {}
        missing_fields = [f for f in ["to", "from", "subject", "body"] if not str(email_data.get(f, "")).strip()]
        smtp_host = str(core_config.get("smtp_host", "")).strip()
        if missing_fields:
            return {
                "valid": False,
                "reason": "MAIL:smtp-missing-email-fields",
                "missing_fields": missing_fields,
                "routing_intent": routing_intent,
            }
        if not smtp_host:
            return {
                "valid": False,
                "reason": "MAIL:smtp-host-required",
                "routing_intent": routing_intent,
            }
        probe_text = f"{email_data.get('subject', '')} {email_data.get('body', '')}"
    else:
        imap_host = str(core_config.get("imap_host", "")).strip()
        username = str(core_config.get("username", "")).strip()
        if not imap_host or not username:
            return {
                "valid": False,
                "reason": "MAIL:imap-host-username-required",
                "routing_intent": routing_intent,
            }
        probe_text = str(core_config.get("criteria", "ALL"))

    allowed, gate_reason = paladin_gate(probe_text)
    if not allowed:
        return {
            "valid": False,
            "reason": gate_reason,
            "routing_intent": routing_intent,
        }

    return {
        "valid": True,
        "reason": "MAIL:allow",
        "routing_intent": routing_intent,
    }


def _validate_self_evolve_signature_sec(amip_request: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    routing_intent = str(amip_request.get("routing_intent", "")).strip().lower()
    if routing_intent != "self.evolve":
        return errors

    payload = amip_request.get("payload") if isinstance(amip_request.get("payload"), dict) else {}
    if not str(payload.get("delta_signature", "")).strip():
        errors.append("missing_self_evolve_delta_signature")
    if not str(payload.get("signed_by", "")).strip():
        errors.append("missing_self_evolve_signer")
    if bool(payload.get("dry_run", True)) is not True:
        errors.append("self_evolve_requires_dry_run")
    return errors


def _validate_contextual_routing_signals_sec(amip_request: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    payload = amip_request.get("payload") if isinstance(amip_request.get("payload"), dict) else {}
    if not isinstance(payload, dict):
        return errors

    narrative_mode = str(payload.get("narrative_mode") or payload.get("persona") or "").strip().lower()
    resonance_state = str(payload.get("resonance_state") or payload.get("resonance") or "").strip().lower()
    routing_intent = str(amip_request.get("routing_intent", "")).strip().lower()

    if routing_intent.startswith("document."):
        doc_ctx = payload.get("document_context") if isinstance(payload.get("document_context"), dict) else {}
        if doc_ctx and not str(doc_ctx.get("document_id") or "").strip():
            errors.append("document_context_missing_document_id")

    if resonance_state in {"dissonant", "unstable", "red"}:
        errors.append("resonance_state_requires_challenge")

    if narrative_mode in {"unsafe_override", "raw_bypass"}:
        errors.append("narrative_mode_denied")

    return errors

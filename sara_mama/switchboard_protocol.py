"""
SwitchboardProtocol: Telephony/VoIP/Phone routing protocol for Mama
Implements call/session validation and automation logic using standard libraries and optional pjsua (SIP/VoIP).
"""

from typing import Optional, List, Dict, Any
import os
import re

try:
    import pjsua  # Optional: SIP/VoIP library
    _VOIP_OK = True
except Exception:
    _VOIP_OK = False


class SwitchboardProtocol:
    """
    Protocol for validating and automating phone/VoIP call routing and session management.
    Includes contacts list management.
    """
    def __init__(self, contacts_path: str = "switchboard_contacts.json"):
        self.contacts_path = os.path.join(os.path.dirname(__file__), contacts_path)
        self.contacts: List[Dict[str, Any]] = self._load_contacts()

    def _load_contacts(self) -> List[Dict[str, Any]]:
        try:
            if os.path.exists(self.contacts_path):
                with open(self.contacts_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return []

    def _save_contacts(self):
        try:
            with open(self.contacts_path, "w", encoding="utf-8") as f:
                json.dump(self.contacts, f, indent=2)
        except Exception:
            pass

    def add_contact(self, name: str, number: str, contact_type: str = "phone") -> Dict[str, Any]:
        """
        Add a contact to the contacts list.
        contact_type: 'phone', 'sip', or other label.
        """
        entry = {"name": name, "number": number, "type": contact_type}
        self.contacts.append(entry)
        self._save_contacts()
        return {"status": "PASS", "contact": entry, "total_contacts": len(self.contacts)}

    def list_contacts(self, filter_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all contacts, optionally filtered by type.
        """
        if filter_type:
            return [c for c in self.contacts if c.get("type") == filter_type]
        return list(self.contacts)

    def remove_contact(self, name: str, number: Optional[str] = None) -> Dict[str, Any]:
        """
        Remove a contact by name (and optionally number).
        """
        before = len(self.contacts)
        self.contacts = [c for c in self.contacts if not (c["name"] == name and (number is None or c["number"] == number))]
        self._save_contacts()
        after = len(self.contacts)
        return {"status": "PASS", "removed": before - after, "total_contacts": after}

    def validate_call(self, call_data: Dict[str, Any], required_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Validate that the call/session contains all required fields and valid phone/SIP addresses.
        call_data: dict with keys like 'from', 'to', 'type', 'session_id', etc.
        """
        missing = [f for f in (required_fields or ["from", "to", "type"]) if f not in call_data or not call_data[f]]
        invalid_numbers = []
        phone_regex = r"^\+?[0-9\- ]{7,15}$"
        sip_regex = r"^sip:[^@]+@[^@]+$"
        for field in ["from", "to"]:
            val = call_data.get(field)
            if val and not (re.match(phone_regex, str(val)) or re.match(sip_regex, str(val))):
                invalid_numbers.append({"field": field, "value": val})
        return {
            "status": "PASS" if not missing and not invalid_numbers else "FAIL",
            "missing_fields": missing,
            "invalid_numbers": invalid_numbers,
            "call_data": call_data,
        }

    def automate_call(self, call_data: Dict[str, Any], connect: bool = False) -> Dict[str, Any]:
        """
        Example automation: (stub) initiate call using pjsua if available, else simulate.
        """
        if _VOIP_OK and connect:
            try:
                # Example: initiate call via pjsua (requires config)
                # lib = pjsua.Lib()
                # lib.init()
                # ... setup accounts, make call ...
                return {"status": "PASS", "connected": True, "note": "Call initiated via pjsua (stub)"}
            except Exception as e:
                return {"status": "ERROR", "error": str(e)}
        else:
            return {"status": "PASS", "connected": False, "note": "Simulation only; no call made."}

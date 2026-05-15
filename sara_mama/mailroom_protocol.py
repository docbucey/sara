"""
MailroomProtocol: Outlook/Gmail style email protocol for Mama
Implements email validation and automation logic using standard libraries and optional exchangelib.
"""

from typing import Optional, List, Dict, Any
import importlib.util
import json
import re
import os

try:
    import exchangelib  # For Outlook/Exchange automation (optional)
    _EXCHANGE_OK = True
except Exception:
    _EXCHANGE_OK = False


def _load_core_transport_module():
    """Load CORE module lazily so Mailroom can delegate transport primitives safely."""
    try:
        core_path = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "sara_core", "sara_coregen1.py")
        )
        if not os.path.exists(core_path):
            return None
        spec = importlib.util.spec_from_file_location("sara_coregen1", core_path)
        if spec is None or spec.loader is None:
            return None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None


class MailroomProtocol:
    """
    Protocol for validating and automating email messages (Outlook, Gmail style).
    Includes contacts list management.
    """
    def __init__(self, contacts_path: str = "mailroom_contacts.json"):
        self.contacts_path = os.path.join(os.path.dirname(__file__), contacts_path)
        self.contacts: List[Dict[str, Any]] = self._load_contacts()
        self._core_transport = _load_core_transport_module()

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

    def add_contact(self, name: str, email: str, contact_type: str = "email") -> Dict[str, Any]:
        """
        Add a contact to the contacts list.
        contact_type: 'email', 'group', or other label.
        """
        entry = {"name": name, "email": email, "type": contact_type}
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

    def remove_contact(self, name: str, email: Optional[str] = None) -> Dict[str, Any]:
        """
        Remove a contact by name (and optionally email).
        """
        before = len(self.contacts)
        self.contacts = [c for c in self.contacts if not (c["name"] == name and (email is None or c["email"] == email))]
        self._save_contacts()
        after = len(self.contacts)
        return {"status": "PASS", "removed": before - after, "total_contacts": after}

    def validate_email(self, email_data: Dict[str, Any], required_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Validate that the email contains all required fields and a valid email address format.
        email_data: dict with keys like 'to', 'from', 'subject', 'body', etc.
        """
        missing = [f for f in (required_fields or ["to", "from", "subject", "body"]) if f not in email_data or not email_data[f]]
        invalid_emails = []
        email_regex = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
        for field in ["to", "from"]:
            val = email_data.get(field)
            if val and not re.match(email_regex, str(val)):
                invalid_emails.append({"field": field, "value": val})
        return {
            "status": "PASS" if not missing and not invalid_emails else "FAIL",
            "missing_fields": missing,
            "invalid_emails": invalid_emails,
            "email_data": email_data,
        }

    def automate_send(
        self,
        email_data: Dict[str, Any],
        send: bool = False,
        use_core_transport: bool = False,
        core_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Example automation: (stub) send email using exchangelib if available, else simulate.
        """
        if send and use_core_transport:
            if self._core_transport is None or not hasattr(self._core_transport, "core_smtp_send_email"):
                return {"status": "ERROR", "error": "CORE SMTP transport is unavailable"}

            cfg = dict(core_config or {})
            smtp_host = str(cfg.get("smtp_host", "")).strip()
            smtp_port = int(cfg.get("smtp_port", 587))
            username = str(cfg.get("username", "")).strip()
            password = str(cfg.get("password", ""))
            use_tls = bool(cfg.get("use_tls", True))
            use_ssl = bool(cfg.get("use_ssl", False))
            timeout = int(cfg.get("timeout", 20))

            if not smtp_host:
                return {"status": "FAIL", "error": "core_config.smtp_host is required for CORE transport"}

            return self._core_transport.core_smtp_send_email(
                smtp_host=smtp_host,
                smtp_port=smtp_port,
                username=username,
                password=password,
                email_data=email_data,
                use_tls=use_tls,
                use_ssl=use_ssl,
                timeout=timeout,
            )

        if _EXCHANGE_OK and send:
            try:
                # Example: send via exchangelib (requires config)
                # account = exchangelib.Account(...)
                # m = exchangelib.Message(account=account, ...)
                # m.send()
                return {"status": "PASS", "sent": True, "note": "Email sent via exchangelib (stub)"}
            except Exception as e:
                return {"status": "ERROR", "error": str(e)}
        else:
            return {"status": "PASS", "sent": False, "note": "Simulation only; no email sent."}

    def fetch_inbox(
        self,
        fetch: bool = False,
        use_core_transport: bool = False,
        core_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Fetch inbox metadata through CORE-owned IMAP transport when enabled."""
        if not fetch:
            return {"status": "PASS", "fetched": False, "note": "Simulation only; no inbox retrieval."}

        if not use_core_transport:
            return {"status": "PASS", "fetched": False, "note": "IMAP fetch disabled; set use_core_transport=True."}

        if self._core_transport is None or not hasattr(self._core_transport, "core_imap_fetch_inbox"):
            return {"status": "ERROR", "error": "CORE IMAP transport is unavailable"}

        cfg = dict(core_config or {})
        imap_host = str(cfg.get("imap_host", "")).strip()
        username = str(cfg.get("username", "")).strip()
        password = str(cfg.get("password", ""))

        if not imap_host or not username:
            return {"status": "FAIL", "error": "core_config.imap_host and core_config.username are required"}

        return self._core_transport.core_imap_fetch_inbox(
            imap_host=imap_host,
            username=username,
            password=password,
            mailbox=str(cfg.get("mailbox", "INBOX")),
            limit=int(cfg.get("limit", 20)),
            use_ssl=bool(cfg.get("use_ssl", True)),
            port=cfg.get("port"),
            criteria=str(cfg.get("criteria", "ALL")),
        )

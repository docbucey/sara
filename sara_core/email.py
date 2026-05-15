"""CORE Email: SMTP send and IMAP fetch for mail transport."""
import os
import json
import email
import smtplib
import imaplib
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def core_smtp_send_email(
    smtp_host: str,
    smtp_port: int,
    username: str,
    password: str,
    email_data: Dict[str, Any],
    use_tls: bool = True,
    use_ssl: bool = False,
    timeout: int = 20,
) -> Dict[str, Any]:
    """CORE-owned SMTP transport primitive for outbound mail submission."""
    import smtplib
    from email.message import EmailMessage

    if not isinstance(email_data, dict):
        return {"status": "FAIL", "error": "email_data must be a dict"}

    required = ["to", "from", "subject", "body"]
    missing = [key for key in required if not str(email_data.get(key, "")).strip()]
    if missing:
        return {"status": "FAIL", "error": "missing_fields", "missing_fields": missing}

    msg = EmailMessage()
    msg["To"] = str(email_data.get("to", "")).strip()
    msg["From"] = str(email_data.get("from", "")).strip()
    msg["Subject"] = str(email_data.get("subject", "")).strip()
    msg.set_content(str(email_data.get("body", "")))

    try:
        if use_ssl:
            with smtplib.SMTP_SSL(host=smtp_host, port=int(smtp_port), timeout=timeout) as client:
                if username:
                    client.login(username, password)
                client.send_message(msg)
        else:
            with smtplib.SMTP(host=smtp_host, port=int(smtp_port), timeout=timeout) as client:
                if use_tls:
                    client.starttls()
                if username:
                    client.login(username, password)
                client.send_message(msg)
        return {
            "status": "PASS",
            "sent": True,
            "transport": "smtp",
            "host": str(smtp_host),
            "port": int(smtp_port),
        }
    except Exception as exc:
        return {
            "status": "ERROR",
            "sent": False,
            "transport": "smtp",
            "error": str(exc),
        }


def core_imap_fetch_inbox(
    imap_host: str,
    username: str,
    password: str,
    mailbox: str = "INBOX",
    limit: int = 20,
    use_ssl: bool = True,
    port: Optional[int] = None,
    criteria: str = "ALL",
) -> Dict[str, Any]:
    """CORE-owned IMAP transport primitive for inbox retrieval."""
    import email
    import imaplib

    if not imap_host or not username:
        return {"status": "FAIL", "error": "imap_host and username are required"}

    safe_limit = max(1, min(int(limit or 20), 200))
    imap_client = None
    try:
        if use_ssl:
            imap_client = imaplib.IMAP4_SSL(imap_host, int(port or 993))
        else:
            imap_client = imaplib.IMAP4(imap_host, int(port or 143))

        imap_client.login(username, password)
        select_status, _ = imap_client.select(mailbox, readonly=True)
        if str(select_status).upper() != "OK":
            return {"status": "FAIL", "error": f"select_failed:{mailbox}"}

        search_status, data = imap_client.search(None, criteria)
        if str(search_status).upper() != "OK":
            return {"status": "FAIL", "error": f"search_failed:{criteria}"}

        ids = data[0].split() if data and data[0] else []
        selected_ids = ids[-safe_limit:]
        messages: List[Dict[str, Any]] = []

        for msg_id in selected_ids:
            fetch_status, msg_data = imap_client.fetch(msg_id, "(RFC822)")
            if str(fetch_status).upper() != "OK" or not msg_data:
                continue
            raw_message = msg_data[0][1] if isinstance(msg_data[0], tuple) and len(msg_data[0]) > 1 else b""
            parsed = email.message_from_bytes(raw_message)
            messages.append(
                {
                    "id": msg_id.decode("utf-8", errors="ignore"),
                    "from": str(parsed.get("From", "")),
                    "to": str(parsed.get("To", "")),
                    "subject": str(parsed.get("Subject", "")),
                    "date": str(parsed.get("Date", "")),
                }
            )

        return {
            "status": "PASS",
            "transport": "imap",
            "mailbox": str(mailbox),
            "count": len(messages),
            "messages": messages,
        }
    except Exception as exc:
        return {
            "status": "ERROR",
            "transport": "imap",
            "error": str(exc),
        }
    finally:
        if imap_client is not None:
            try:
                imap_client.logout()
            except Exception:
                pass

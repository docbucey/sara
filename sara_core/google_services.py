"""
CORE — Google Services integration.
Calendar, Meet, SMS-via-email, web browse.
Uses Google API client library when available, falls back to REST/SMTP.

Setup: pip install google-api-python-client google-auth-oauthlib
For SMS: uses carrier email gateways (no Twilio needed).
"""

import json
import os
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

# ── Google Calendar ────────────────────────────────────────────────────────

_CALENDAR_SERVICE = None
_SCOPES = ["https://www.googleapis.com/auth/calendar"]


def _get_calendar_service():
    """Lazy-init Google Calendar API service."""
    global _CALENDAR_SERVICE
    if _CALENDAR_SERVICE is not None:
        return _CALENDAR_SERVICE

    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    creds = None
    token_path = os.path.join(os.path.expanduser("~"), ".sara", "google_token.json")
    creds_path = os.path.join(os.path.expanduser("~"), ".sara", "google_credentials.json")

    os.makedirs(os.path.dirname(token_path), exist_ok=True)

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, _SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(creds_path):
                raise FileNotFoundError(
                    f"Place Google OAuth credentials.json at {creds_path}. "
                    "Get it from https://console.cloud.google.com/apis/credentials"
                )
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, _SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, "w") as f:
            f.write(creds.to_json())

    _CALENDAR_SERVICE = build("calendar", "v3", credentials=creds)
    return _CALENDAR_SERVICE


def calendar_list_events(
    max_results: int = 10,
    time_min: Optional[str] = None,
    calendar_id: str = "primary",
) -> Dict[str, Any]:
    """List upcoming Google Calendar events."""
    try:
        service = _get_calendar_service()
        if not time_min:
            time_min = datetime.now(timezone.utc).isoformat()
        result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
        ).execute()
        events = []
        for ev in result.get("items", []):
            start = ev.get("start", {}).get("dateTime", ev.get("start", {}).get("date", ""))
            events.append({
                "id": ev.get("id"),
                "summary": ev.get("summary", "(no title)"),
                "start": start,
                "end": ev.get("end", {}).get("dateTime", ""),
                "location": ev.get("location", ""),
                "meet_link": ev.get("hangoutLink", ""),
            })
        return {"success": True, "count": len(events), "events": events}
    except FileNotFoundError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": f"Calendar API error: {e}"}


def calendar_create_event(
    summary: str,
    start_time: str,
    end_time: Optional[str] = None,
    description: str = "",
    location: str = "",
    add_meet: bool = False,
    attendees: Optional[List[str]] = None,
    calendar_id: str = "primary",
) -> Dict[str, Any]:
    """Create a Google Calendar event. Optionally attach a Google Meet link."""
    try:
        service = _get_calendar_service()

        if not end_time:
            from dateutil.parser import parse as dt_parse
            start_dt = dt_parse(start_time)
            end_dt = start_dt + timedelta(hours=1)
            end_time = end_dt.isoformat()

        body: Dict[str, Any] = {
            "summary": summary,
            "start": {"dateTime": start_time, "timeZone": "America/Chicago"},
            "end": {"dateTime": end_time, "timeZone": "America/Chicago"},
        }
        if description:
            body["description"] = description
        if location:
            body["location"] = location
        if attendees:
            body["attendees"] = [{"email": a} for a in attendees]
        if add_meet:
            body["conferenceData"] = {
                "createRequest": {
                    "requestId": f"sara-{int(datetime.now().timestamp())}",
                    "conferenceSolutionKey": {"type": "hangoutsMeet"},
                }
            }

        event = service.events().insert(
            calendarId=calendar_id,
            body=body,
            conferenceDataVersion=1 if add_meet else 0,
        ).execute()

        return {
            "success": True,
            "event_id": event.get("id"),
            "html_link": event.get("htmlLink"),
            "meet_link": event.get("hangoutLink", ""),
            "summary": event.get("summary"),
            "start": event.get("start", {}).get("dateTime"),
        }
    except FileNotFoundError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": f"Calendar create error: {e}"}


# ── Google Meet ────────────────────────────────────────────────────────────

def create_meet_link(
    summary: str = "SARA Meeting",
    duration_minutes: int = 60,
    attendees: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Create a Google Meet link by creating a calendar event with conferencing."""
    start = datetime.now(timezone.utc) + timedelta(minutes=5)
    return calendar_create_event(
        summary=summary,
        start_time=start.isoformat(),
        end_time=(start + timedelta(minutes=duration_minutes)).isoformat(),
        add_meet=True,
        attendees=attendees,
    )


# ── SMS via carrier email gateway ──────────────────────────────────────────

CARRIER_GATEWAYS = {
    "att": "{number}@txt.att.net",
    "tmobile": "{number}@tmomail.net",
    "verizon": "{number}@vtext.com",
    "sprint": "{number}@messaging.sprintpcs.com",
    "uscellular": "{number}@email.uscc.net",
    "boost": "{number}@sms.myboostmobile.com",
    "cricket": "{number}@sms.cricketwireless.net",
    "metro": "{number}@mymetropcs.com",
    "googlefi": "{number}@msg.fi.google.com",
    "mint": "{number}@mailmymobile.net",
    "visible": "{number}@vzwpix.com",
}


def send_sms(
    to_number: str,
    message: str,
    carrier: str,
    gmail_address: str,
    gmail_app_password: str,
) -> Dict[str, Any]:
    """Send SMS via carrier email gateway using Gmail SMTP."""
    import re
    digits = re.sub(r"\D", "", to_number)
    if len(digits) < 10:
        return {"success": False, "error": f"Invalid phone number: {to_number}"}

    carrier_key = carrier.lower().replace(" ", "").replace("-", "")
    gateway_template = CARRIER_GATEWAYS.get(carrier_key)
    if not gateway_template:
        return {
            "success": False,
            "error": f"Unknown carrier: {carrier}",
            "supported": list(CARRIER_GATEWAYS.keys()),
        }

    sms_email = gateway_template.format(number=digits)

    from sara_core.email import core_smtp_send_email
    result = core_smtp_send_email(
        smtp_host="smtp.gmail.com",
        smtp_port=587,
        username=gmail_address,
        password=gmail_app_password,
        email_data={
            "to": sms_email,
            "from": gmail_address,
            "subject": "",
            "body": message[:160],
        },
        use_tls=True,
    )

    if result.get("status") == "PASS":
        return {"success": True, "sent_to": sms_email, "number": digits, "carrier": carrier}
    return {"success": False, "error": result.get("error", "SMTP failed")}


# ── Web Browse ─────────────────────────────────────────────────────────────

def web_browse(
    url: str,
    extract: str = "text",
    timeout: int = 15,
) -> Dict[str, Any]:
    """Fetch a URL and extract text or links. No JS rendering (stdlib only)."""
    from sara_core.network import extract_text, extract_links

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SARA/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content_type = resp.headers.get("Content-Type", "text/html")
            data = resp.read(1024 * 512)  # 512KB max

        if extract == "links":
            links, meta = extract_links(data, url, content_type)
            return {"success": True, "url": url, "links": links[:100], "meta": meta}
        else:
            text, meta = extract_text(data, url, content_type)
            return {"success": True, "url": url, "text": text[:8000], "meta": meta}

    except Exception as e:
        return {"success": False, "url": url, "error": str(e)}


def web_search(
    query: str,
    num_results: int = 5,
) -> Dict[str, Any]:
    """Simple web search via DuckDuckGo HTML (no API key needed)."""
    try:
        encoded = urllib.parse.urlencode({"q": query})
        url = f"https://html.duckduckgo.com/html/?{encoded}"
        req = urllib.request.Request(url, headers={"User-Agent": "SARA/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read(1024 * 256)

        from html.parser import HTMLParser

        class DDGParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.results = []
                self._in_result = False
                self._current = {}

            def handle_starttag(self, tag, attrs):
                attrs_dict = dict(attrs)
                if tag == "a" and "result__a" in attrs_dict.get("class", ""):
                    self._in_result = True
                    href = attrs_dict.get("href", "")
                    if "uddg=" in href:
                        href = urllib.parse.unquote(
                            urllib.parse.parse_qs(urllib.parse.urlparse(href).query).get("uddg", [href])[0]
                        )
                    self._current = {"url": href, "title": ""}

            def handle_data(self, data):
                if self._in_result and self._current:
                    self._current["title"] += data.strip()

            def handle_endtag(self, tag):
                if tag == "a" and self._in_result:
                    self._in_result = False
                    if self._current.get("url"):
                        self.results.append(self._current)
                    self._current = {}

        parser = DDGParser()
        parser.feed(data.decode("utf-8", errors="ignore"))
        return {"success": True, "query": query, "results": parser.results[:num_results]}

    except Exception as e:
        return {"success": False, "query": query, "error": str(e)}

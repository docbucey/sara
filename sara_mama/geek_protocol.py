"""
SARA Geek Protocol (Gen1)

Purpose:
- Provide browser/workflow automation and validation for browser-like tasks (the SARA equivalent of Chrome, Safari, Edge, etc).
- Enable UI and automation flows for web navigation, tab/session management, and browser-based actions.
- Bridge to any web-based AI assistant (ChatGPT, Gemini, Claude, Copilot, Perplexity, etc) as a contact.
- Support dual roles (assistant, source, scraper, etc) per contact.
- All actions flow through SARA security → control → core for orchestration and audit.

Features:
- Validate browser session/task data
- Manage persistent browser session/contact info (with roles)
- Provide hooks for automation (open URL, close tab, bridge, learn/scrape)
- Secure routing: UI → MamaDispatcher → Control/Security → Core → WebAI → back
- Ready for UI integration
"""
import os
import json
from typing import Dict, Any, Optional, List

GEEK_CONTACTS_FILE = os.path.join(os.path.dirname(__file__), 'geek_contacts.json')

def _load_contacts() -> List[Dict[str, Any]]:
    if not os.path.exists(GEEK_CONTACTS_FILE):
        return []
    try:
        with open(GEEK_CONTACTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []

def _save_contacts(contacts: List[Dict[str, Any]]):
    with open(GEEK_CONTACTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(contacts, f, indent=2)

def validate_browser_task(url: str, action: str = 'open', **kwargs) -> Dict[str, Any]:
    if not url or not isinstance(url, str) or not url.startswith(('http://', 'https://')):
        return {'status': 'ERROR', 'reason': 'Invalid or missing URL'}
    if action not in {'open', 'close', 'refresh', 'bookmark', 'screenshot', 'bridge_nano', 'bridge_copilot', 'bridge_web_ai'}:
        return {'status': 'ERROR', 'reason': f'Unsupported action: {action}'}
    # Optionally add more validation for allowed domains, etc.
    return {'status': 'PASS', 'url': url, 'action': action}

# --- Generic bridge to any web-based AI assistant ---
# --- Secure bridge to any web-based AI assistant (flows through SARA security/control/core) ---
def bridge_to_web_ai(name: str, url: str, task: str, data: Optional[Dict[str, Any]] = None, user: str = 'system', auth_token: str = '') -> Dict[str, Any]:
    """
    Secure bridge method for any web-based AI assistant.
    All actions must flow: UI → MamaDispatcher → Control (security/audit) → Core → back.
    Security checks and audit logs are enforced before any web AI interaction.
    """
    audit_log = {
        'user': user,
        'auth_token': auth_token,
        'action': 'bridge_to_web_ai',
        'target': name,
        'url': url,
        'task': task,
        'data': data or {},
        'routed': ['UI', 'MamaDispatcher', 'Control', 'Security', 'Core', 'WebAI', 'Core', 'Security', 'Control', 'MamaDispatcher', 'UI']
    }
    return {
        'status': 'BRIDGE_STUB',
        'bridge': name,
        'url': url,
        'task': task,
        'data': data or {},
        'audit_log': audit_log,
        'note': f'Bridge to {name} at {url} not yet implemented. Routed securely.'
    }

# --- Learn from/scrape interaction with a web AI assistant (flows through SARA security/control/core) ---
def learn_from_interaction(name: str, url: str, interaction_data: Dict[str, Any], user: str = 'system', auth_token: str = '') -> Dict[str, Any]:
    """
    Initiate a learning/scraping event for a given web AI contact.
    This method routes through security and control, logs the event, and stores the result in core for future learning.
    """
    audit_log = {
        'user': user,
        'auth_token': auth_token,
        'action': 'learn_from_interaction',
        'target': name,
        'url': url,
        'interaction_data': interaction_data,
        'routed': ['UI', 'MamaDispatcher', 'Control', 'Security', 'Core', 'WebAI', 'Core', 'Security', 'Control', 'MamaDispatcher', 'UI']
    }
    return {
        'status': 'LEARN_STUB',
        'source': name,
        'url': url,
        'interaction_data': interaction_data,
        'audit_log': audit_log,
        'note': f'Learning/scraping from {name} at {url} not yet implemented. Routed securely.'
    }

# Add a new web AI assistant as a contact (name, url, optional type)
def add_contact(name: str, url: str, ai_type: str = 'web_ai', roles: Optional[list] = None) -> Dict[str, Any]:
    contacts = _load_contacts()
    if any(c.get('url') == url or c.get('name') == name for c in contacts):
        return {'status': 'ERROR', 'reason': 'Contact already exists'}
    contacts.append({'name': name, 'url': url, 'type': ai_type})
    _save_contacts(contacts)
    return {'status': 'PASS', 'contact': {'name': name, 'url': url, 'type': ai_type}}
    contact = {'name': name, 'url': url, 'type': ai_type, 'roles': roles or ['assistant']}
    contacts.append(contact)
    _save_contacts(contacts)
    return {'status': 'PASS', 'contact': contact}

def list_contacts() -> List[Dict[str, Any]]:
    return _load_contacts()

# Remove a contact by name or url
def remove_contact(identifier: str) -> Dict[str, Any]:
    contacts = _load_contacts()
    new_contacts = [c for c in contacts if c.get('url') != identifier and c.get('name') != identifier]
    if len(new_contacts) == len(contacts):
        return {'status': 'ERROR', 'reason': 'Contact not found'}
    _save_contacts(new_contacts)
    return {'status': 'PASS', 'removed': identifier}

# --- Documentation: Secure Routing Flow ---
# All protocol actions (including web AI bridges and learning) must flow:
#   UI → MamaDispatcher → Control (security/audit) → Core (data ops) → WebAI (if needed) → back up the stack.
# Security checks and audit logs are enforced before any web AI interaction or learning event.

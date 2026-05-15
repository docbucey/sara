"""
SARA Control — AI Backend interface and SecurityManager class.
Extracted from sara_controlgen1.py.
"""
from datetime import datetime
from typing import Any, Dict, Optional, Callable


class SARA_AIBackend:
    """
    Generic AI backend interface for SARA. Plug in any LLM or API.
    """
    def __init__(self):
        self.backends = {}
        self.default_backend = None

    def register_backend(self, name: str, handler: Callable[[str, Optional[Dict[str, Any]]], str], is_default: bool = False):
        self.backends[name] = handler
        if is_default or self.default_backend is None:
            self.default_backend = name

    def ask(self, prompt: str, context: Optional[Dict[str, Any]] = None, backend: Optional[str] = None) -> str:
        backend = backend or self.default_backend
        if backend not in self.backends:
            return f"[AI backend '{backend}' not available]"
        return self.backends[backend](prompt, context or {})


def dummy_backend(prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
    return f"[DUMMY AI] {prompt} (context: {context})"


ai_backend = SARA_AIBackend()
ai_backend.register_backend("dummy", dummy_backend, is_default=True)


class SecurityManager:
    """
    Manages security levels, access, and audit logs for SARA.
    """
    def __init__(self):
        self.levels = {
            'basic': 'General use, open access.',
            'restricted': 'Sensitive, limited access.',
            'admin': 'Admin-only, full audit.'
        }
        self.current_level = 'basic'
        self.audit_log = []

    def set_level(self, level: str):
        if level in self.levels:
            self.current_level = level
            self._log(f"Security level set to {level}")
        else:
            raise ValueError(f"Unknown security level: {level}")

    def authorize(self, action: str, user: str = "system") -> bool:
        allowed = self.current_level != 'restricted' or user == 'admin'
        self._log(f"Authorize '{action}' by {user}: {allowed}")
        return allowed

    def _log(self, message: str):
        self.audit_log.append({
            'timestamp': datetime.now().isoformat(),
            'level': self.current_level,
            'message': message
        })

    def get_status(self):
        return {
            'level': self.current_level,
            'audit': self.audit_log[-5:]
        }

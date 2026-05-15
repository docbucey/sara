# sara_security/paladin.py
# Extracted from sara_securitygen1.py — hostile signature scanning gate.

try:
    from sara_common.types import SecurityOutcome
except ImportError:
    pass

BAD_SIGNATURES = ["drop table", "sudo", "delete", "rm -rf", "force", "hack"]

def paladin_gate(request_text):
    """Returns (allowed: bool, reason: str)."""
    content = str(request_text).lower()
    for sig in BAD_SIGNATURES:
        if sig in content:
            return False, f"PALADIN:DENY:hostile-signature:{sig}"
    return True, "PALADIN:ALLOW:clean"

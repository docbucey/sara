# sara_security/harness.py
# Extracted from sara_securitygen1.py — harness proof run.

try:
    from sara_common.types import SecurityOutcome
except ImportError:
    pass

try:
    from .king import king_sovereignty_check, ROYAL_SIGNET
except ImportError:
    try:
        from king import king_sovereignty_check, ROYAL_SIGNET
    except ImportError:
        ROYAL_SIGNET = "USER_AUTH_CONFIRMED"
        def king_sovereignty_check(auth_token):
            return auth_token == ROYAL_SIGNET

try:
    from .paladin import paladin_gate
except ImportError:
    try:
        from paladin import paladin_gate
    except ImportError:
        def paladin_gate(text):
            return True, "PALADIN:ALLOW:stub"

try:
    from .sheriff import sheriff_audit
except ImportError:
    try:
        from sheriff import sheriff_audit
    except ImportError:
        def sheriff_audit(event_type, actor, decision, reason, details=None, **extra):
            return {"event_type": event_type, "actor": actor, "decision": decision, "reason": reason}


def run_security_harness_check(auth_token=ROYAL_SIGNET, request_text="harness:proof:run"):
    """
    Runs the security pillar gate sequence for a harness proof test.
    Returns a result dict with keys: status, reason.
    """
    # Step 1 -- sovereignty check
    if not king_sovereignty_check(auth_token):
        sheriff_audit("security.harness.proof", "king", "DENY", "KING:sovereignty-check-failed")
        return {"status": "FAIL", "reason": "KING:sovereignty-check-failed"}

    # Step 2 -- paladin gate
    allowed, reason = paladin_gate(request_text)
    if not allowed:
        sheriff_audit("security.harness.proof", "paladin", "DENY", reason)
        return {"status": "FAIL", "reason": reason}

    # Step 3 -- sheriff audit record for the passing path
    event = sheriff_audit("security.harness.proof", "sheriff", "ALLOW", reason)

    return {"status": "PASS", "reason": reason, "audit": event}

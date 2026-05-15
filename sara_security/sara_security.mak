SARA SECURITY PREP

Pillar:
- sara_security

Purpose:
- Define validation, permission, guardrail, and audit responsibilities for SARA Gen 0.

Gen 0 scope:
- Python-first for initial prep and early implementation.
- One later non-Python exception may live here when hardening requires it.

Security responsibilities:
- validate allowed actions
- enforce boundary rules
- gate sensitive tool or file access
- produce audit-friendly pass/fail decisions
- define where later hardened exception component can attach

Inputs:
- requested action
- target path or tool
- control decision packet
- current workspace context

Outputs:
- allow
- deny
- reason
- audit event
- future hardened exception handoff point

Restrictions:
- Security does not own product planning.
- Security does not replace Control routing.
- Security does not replace Mama history.

Future exception note:
- If any Gen 0 area needs non-Python implementation later, it must be inside sara_security and justified by hardening or isolation needs.
- Until then, treat Security as Python-first.

First Python target when implementation begins:
- sara_security.py

First implementation focus:
- rule gate for allowed actions and audit event format

Success condition for pre-prep:
- Security boundary is established before tools and model wiring expand.

King and Phoenix sovereign protocol (separate from normal evolution shunts):
- Protocol family: King and Phoenix.
- Methods: Phoenix Fire and Phoenix Ash.
- This lane is a sovereign security execution path and is not controlled by Control during active Phoenix operations.
- Standard flow remains Core -> Control for normal shunt routing; this sovereign lane is a defined exception.
- Core still defines architecture boundaries and policy constraints for sovereign execution.
- Security executes anti-malware and governance actions at OS-facing depth when the sovereign lane is active.
- Control is continuity observer and post-lane coordinator only; it does not override active Phoenix execution.
- Purpose: support anti-malware response, governance enforcement, and future distributed security processing.
- Compatibility rule: OS base security suite remains active; SARA augments and orchestrates rather than replacing base defenses.
- Expansion note: distributed processing is enabled only under Core policy approval and Security trust criteria.

Do not remove this file when updates are added.
Append newer rules below existing rules.
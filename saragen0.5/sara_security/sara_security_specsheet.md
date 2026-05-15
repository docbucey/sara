# Primitive Language Model (PLM) Template
Refer to the SARA_SYSTEM_ARCHITECTURE_SPEC.md for the full PLM template. The following summarizes the key points for SECURITY:

- Minimal, deterministic language/protocol module to prevent bloat
- Modular, with strict boundaries and extension points
- Callable by SARA for protocol/security validation or code generation
- Deterministic by default; generative/adaptive only when extended
- Core methods: parse, generate, validate, extend
# SARA Gen0.5 SECURITY Pillar Specsheet

**Alignment with C# UI Extended Spec:**
	- **Self-Training/AI Generation:** SECURITY audits and gates all self-training operations, ensuring that training data, model updates, and AI generation actions comply with trust and safety policies. All such actions are subject to SECURITY's protocol and consent boundaries.
	- **Self-Training/AI Generation:** SECURITY audits and gates all self-training operations, ensuring that training data, model updates, and AI generation actions comply with trust and safety policies. All such actions are subject to SECURITY's protocol and consent boundaries.
	- **Compatibility:** SECURITY is designed for future extensibility and protocol evolution, while Gen0.5 and earlier generations remain backward compatible with legacy protocols and workflows. SECURITY can operate fully without an AI/model component; AI integration is present only for compatibility and extension.
	- **AMIP/AMIPI Protocols:** SECURITY audits and gates all AMIP/AMIPI-aligned payloads for cross-pillar and external data exchange.
	- **SHI/Extension Protocols:** SECURITY gates and audits new protocol codes (e.g., SHI) and special-case lanes, especially for trust-sensitive or security-relevant actions.
	- **ACT Codes:** SECURITY uses ACT-mapped dispatch/action codes for pillar entrypoints, as defined in the action map and protocol handler.
	- **Extension Points:** SECURITY is ready for new protocol codes and mapped actions as defined by CONTROL and the evolving protocol map.
	- SECURITY is the gatekeeping, audit, and quarantine authority; it does not interact directly with the UI or possess routing, schema, or memory authority for UI actions.
	- All UI/backend actions must be routed through CONTROL, which enforces protocol, ADA/accessibility, mapping, and initialization requirements.
	- SECURITY participates in the hemispheric model as the trust/gate layer (left hemisphere), with all backend entry mediated by CONTROL.
	- No UI module or generative/LLM/AI surface logic may bypass CONTROL or SECURITY for backend actions.

- **Pillar:** SECURITY (The Keep)

**Purpose:**
	- Serve as the audit, gatekeeping, and quarantine pillar for the entire SARA system. All backend entry from UI is mediated by CONTROL and validated by SECURITY.
	- Enforce sovereignty checks, allow/deny decisions, and structured audit logging for all operations. CONTROL and SECURITY validate all backend entry from UI.
	- Provide deterministic, protocol-enforced, and auditable FSM for all security actions. CONTROL and SECURITY enforce all backend entry from UI.
	- Consolidate multiple security roles: King (authority), Paladin (defense), Sheriff (audit), Deputy (janitor/gatekeeper), Envoy (transport/proxy), Archeologist (history), Conservator (repair), Restoration (learning/grafting).
	- Maintain strict separation from other pillars, with explicit authority and routing enforced at the header and protocol level. No UI or LLM/AI surface logic may bypass CONTROL or SECURITY.

- **Key Functions/Classes:**
	- `Paladin`: Active defense, threat detection, and honeypot engagement.
	- `Sheriff`: System auditor, patrols and scans for integrity.
	- `Deputy`: Janitor/gatekeeper, sweeps for issues and validates outgoing data.
	- `Archeologist`: Catalogs and inventories historical artifacts.
	- `Conservator`: Repairs and stabilizes data collections.
	- `Restoration`: Scans for new capabilities and upgrades.
	- `Envoy`: Secure transport and proxy, ensures safe data movement.
	- `King`: Authority, dead man switch, and system lockdown/resurrection (Phoenix protocol).
	- `SecurityKeep`: Main interface, orchestrates all security roles and runs system-wide surveys.

- **FSM/Protocol:**
	- FSM states: `idle`, `processing`, `done`, `error` (expandable for richer security states).
	- FSM transitions: Deterministic, auditable, and strictly enforced.
	- Shunt header: Binary and literal header enforcing domain, authority, routing, and provenance (see code for byte-level details).
	- All security actions require valid shunt headers and are logged for audit. CONTROL validates all backend entry from UI.

- **Learning/AI/Context Logic:**
	- Restoration class provides learning/grafting logic for discovering and integrating new capabilities.
	- Security pillar itself is not adaptive at the gatekeeping/audit layer; learning is isolated to restoration and upgrade scanning.

- **Security/Access:**
	- All actions require explicit, protocol-compliant headers. CONTROL validates all backend entry from UI.
	- Authority and routing fields in the header enforce pillar boundaries and prevent unauthorized cross-pillar actions. CONTROL and SECURITY enforce all backend entry from UI.
	- Audit logging is mandatory for all security operations. CONTROL and SECURITY validate all backend entry from UI.
	- King/Paladin/Envoy/Keep enforce sovereignty, threat response, and system lockdown as needed.

- **Notes:**
	- SECURITY’s design merges military-grade defense (Paladin), law/audit (Sheriff), authority (King), and restoration (learning) into a single, protocol-driven pillar. All backend entry is mediated by CONTROL, per the C# UI extended spec.
	- The monolith structure (Gen0) is for reference; future generations modularize these roles but preserve their original intent and rigor.
	- See also: [sara_security.py] for full class and protocol details.
Primitive Language Model (PLM) Template**

- **Purpose:** Provide a minimal, deterministic language or protocol module to prevent bloat and enable safe extension.
- **Design:**
	- Modular, with strict boundaries and clear extension points
	- Callable by SARA for core language/protocol tasks
	- Can generate code for new languages or pillars
	- Deterministic by default; generative/adaptive only when explicitly extended
- **Core Methods:**
	- `parse(input: str) -> AST`: Parse input into a minimal abstract syntax tree (AST)
	- `generate(ast: AST) -> str`: Generate code or protocol output from AST
	- `validate(ast: AST) -> bool`: Validate AST for correctness and safety
	- `extend(extension: Callable)`: Register a new extension or protocol handler
- **Example (Python-like pseudocode):**
	```python
	class PrimitiveLanguageModel:
			def parse(self, input: str):
					# Minimal parsing logic
					pass

			def generate(self, ast):
					# Minimal code/protocol generation
					pass

			def validate(self, ast):
					# Minimal validation
					return True

			def extend(self, extension):
					# Register extension handler
					pass
	```
- **Notes:**
	- PLMs should be as simple as possible, with no unnecessary features.
	- All generative/adaptive logic must be opt-in and externally governed.
	- PLMs can be reused, extended, or replaced as SARA evolves.
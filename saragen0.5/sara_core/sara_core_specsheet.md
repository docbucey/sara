# Primitive Language Model (PLM) Template
Refer to the SARA_SYSTEM_ARCHITECTURE_SPEC.md for the full PLM template. The following summarizes the key points for CORE:

- Minimal, deterministic language/protocol module to prevent bloat
- Modular, with strict boundaries and extension points
- Callable by SARA for core tasks or code generation
- Deterministic by default; generative/adaptive only when extended
- Core methods: parse, generate, validate, extend
# SARA Gen0.5 CORE Pillar Specsheet

**Alignment with C# UI Extended Spec:**
	- **Self-Training/AI Generation:** CORE provides the persistent substrate for all self-training data, logs, and generated datasets used by SARA or exported for external AI training. All memory and data operations supporting self-improvement or dataset generation are handled here.
	- **Compatibility:** CORE is designed for future extensibility and protocol evolution, while Gen0.5 and earlier generations remain backward compatible with legacy data and workflows. CORE can operate fully without an AI/model component; AI integration is present only for compatibility and extension.
	- **AMIP/AMIPI Protocols:** CORE enforces the AMIP/AMIPI schema for all cross-pillar and external data exchange. All payloads must conform to these boundary formats.
	- **VNCE Protocol:** CORE implements VNCE session states and commands for remote/cockpit/virtual node operations, as defined in the FSM and protocol handler sections.
	- **Office/Media Protocols:** CORE provides protocol-driven handlers for Office, image, video, audio, and 3D file actions, all routed through the shunt header and validated by CONTROL.
	- **Extension Points:** CORE is ready for new protocol codes (e.g., SHI) as defined by CONTROL and the evolving protocol map.
	- CORE is the technical substrate and profile truth source; it does not interact directly with the UI or possess routing, schema, or memory authority for UI actions.
	- All UI/backend actions must be routed through CONTROL, which enforces protocol, ADA/accessibility, mapping, and initialization requirements.
	- CORE participates in the hemispheric model as the structural authority (left hemisphere), with all backend entry mediated by CONTROL.
	- No UI module or generative/LLM/AI surface logic may bypass CONTROL to access CORE.

- **Pillar:** CORE

**Purpose:**
	- Serve as the technical substrate and original center of the SARA architecture.
	- Provide foundational data, file, and protocol handling for all pillars, with backend entry always mediated by CONTROL.
	- Enforce the shunt header contract for all cross-pillar communication—no raw data or direct calls between pillars or from UI; CONTROL validates all backend entry. All AMIP/AMIPI and VNCE payloads are enforced at this layer.
	- Provide foundational data, file, and protocol handling for all other pillars, including CONTROL. No UI or LLM/AI surface logic may access CORE directly. Office/Media protocol handlers are implemented here.
	- Maintain strict architectural boundaries and compatibility for legacy and future modules. All ADA/accessibility, mapping, and initialization requirements are enforced at the CONTROL boundary. CORE is ready for protocol extension (e.g., SHI, new session types) as defined by CONTROL.

- **Key Functions/Classes:**
	- Shunt header enforcement and validation (`validate_shunt_header`). CONTROL validates all backend entry from UI.
	- ShuntFSM: Finite State Machine for protocol state and transition management.
	- Data/file IO handlers: image, video, audio, 3D, and office file operations.
	- Proto-lingua tagging and resonance validation for data integrity and compatibility.
	- Compatibility bridge (Sara_core.py) for legacy imports and runtime safety.

- **FSM/Protocol:**
	- FSM states: `idle`, `processing`, `done`, `error`, `vnce_session_active` (expandable for protocol evolution).
	- FSM transitions: Deterministic, auditable, and strictly enforced.
	- Shunt header: JSON envelope with strict required fields for all cross-pillar actions.
	- All shunt enforcement and execution must be routed through CONTROL, but CORE is the enforcer. No UI or LLM/AI surface logic may bypass CONTROL.

- **Learning/AI/Context Logic:**
	- CORE itself is intentionally non-adaptive; all learning/adaptive logic is routed through CONTROL or domain-specific modules. No UI or LLM/AI surface logic may introduce learning/adaptive logic into CORE.
	- Proto-lingua tagging and resonance fields allow for future context-driven extensions.

- **Security/Access:**
	- All actions require explicit, protocol-compliant shunt headers. CONTROL validates all backend entry from UI.
	- No direct or raw data access across pillars—enforced at the substrate level. No UI or LLM/AI surface logic may access CORE directly.
	- Audit logging and compatibility checks are mandatory for all IO and protocol operations. CONTROL is responsible for validating all backend entry from UI.

- **Notes:**
	- CORE’s architecture is highly stable and preserved, reflecting the original author’s design intent and conventions. All backend entry is mediated by CONTROL, per the C# UI extended spec.
	- Most architectural evolution occurs around CONTROL and other pillars; CORE remains the technical heart and enforcer.
	- See also: Sara_core.py for legacy compatibility logic and proto-lingua conventions.
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
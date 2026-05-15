	# Primitive Language Model (PLM) Template
	Refer to the SARA_SYSTEM_ARCHITECTURE_SPEC.md for the full PLM template. The following summarizes the key points for MAMA:

	- Minimal, deterministic language/protocol module to prevent bloat
	- Modular, with strict boundaries and extension points
	- Callable by SARA for interface or code generation tasks
	- Deterministic by default; generative/adaptive only when extended
	- Core methods: parse, generate, validate, extend
	- **Compatibility:** MAMA is designed for future extensibility and protocol evolution, while Gen0.5 and earlier generations remain backward compatible with legacy protocols and workflows. MAMA can operate fully without an AI/model component; AI integration is present only for compatibility and extension.
	- **Self-Training/AI Generation:** MAMA can present, initiate, or visualize self-training actions and AI generation tasks, but does not govern or execute them. All such actions are routed through CONTROL and visualized for the user as needed.
	- **ACT Codes:** MAMA uses ACT-mapped dispatch/action codes for pillar entrypoints, as defined in the action map and protocol handler.
# SARA Gen0.5 MAMA Pillar Specsheet

**Alignment with C# UI Extended Spec:**
	- **Self-Training/AI Generation:** MAMA can present, initiate, or visualize self-training actions and AI generation tasks, but does not govern or execute them. All such actions are routed through CONTROL and visualized for the user as needed.
	- **ACT Codes:** MAMA uses ACT-mapped dispatch/action codes for pillar entrypoints, as defined in the action map and protocol handler.
	- **Extension Points:** MAMA is ready for new protocol codes and mapped actions as defined by CONTROL and the evolving protocol map.
	- MAMA is a surface/interface layer only; it does not possess routing, schema, or memory authority.
	- All UI actions and generative/LLM/AI surface logic are subordinate to CONTROL and SECURITY, per the hemispheric model.
	- MAMA must bind to CONTROL for all backend entry and protocol enforcement; no direct backend calls are permitted from the UI or MAMA.
	- ADA/accessibility, mapping, and initialization requirements from the C# spec are enforced at the CONTROL boundary, not by MAMA.
	- MAMA participates in the hemispheric model as the humane/UX presentation layer (left hemisphere), with all backend actions routed through CONTROL.

- **Pillar:** MAMA (Man Machine Interface)

**Purpose:**
	- Serve as the primary interface layer between human operators and the SARA system, inspired by Army Signal Corps “Man Machine Interface” doctrine.
	- Provide only surface-level, non-authoritative presentation and interaction; all backend actions are routed through CONTROL.
	- Provide deterministic, auditable, and protocol-enforced routing for all model-agnostic generation, memory, and context operations (via CONTROL).
	- Act as the substrate for all hands-on/throttle-and-stick (HOTAS) style controls, ensuring direct, traceable, and context-aware interaction (with CONTROL as the backend authority).
	- Maintain strict separation of interface, memory, and orchestration logic, with all actions routed through CONTROL for governance.

	- `mama_shunt_entrypoint`: Unified entrypoint for all cross-pillar actions, enforcing shunt header validation and dispatching via FSM (CONTROL validates all backend entry). ACT codes are used for mapped actions.
	- `ShuntFSM`: Finite State Machine for MAMA protocol state and transition management.
	- ACT-mapped functions: `snapshot`, `diff`, `persist`, `noop_action` (expandable for future interface actions).
	- Header enforcement: `validate_shunt_header` ensures all payloads conform to protocol.
	- **Environmental & Situational Awareness Modules:**
		- `scout`: Hardware/OS identity and reconnaissance (planned/shared with SECURITY).
		- `yard`: Local I/O driver probing (planned/shared with SECURITY).
		- `house`: Network mapping and zero-tolerance enforcement (planned/shared with SECURITY).
		- `mapper`: System/network topology mapping (planned/shared with SECURITY).
	- These modules gather, present, and contextualize system, I/O, and network state for operator awareness and control, supporting MAMA’s Man Machine Interface role.
	- **Note:** Reasoning engines and math layers (e.g., proto_math, reasoning_protocols) are governed and orchestrated by CONTROL. MAMA only consumes advisory output and does not select or execute these engines. All UI/LLM/AI surface logic is subordinate to CONTROL and SECURITY.

- **FSM/Protocol:**
	- FSM states: `idle`, `processing`, `done`, `error` (expandable for richer interface states). All UI-initiated FSM transitions are routed through CONTROL.
	- FSM transitions: Deterministic, auditable, and strictly enforced (CONTROL enforces all backend transitions).
	- Shunt header: Binary and literal header enforcing domain, authority, routing, and provenance (see code for byte-level details). CONTROL validates all backend shunt headers.
	- All interface actions require valid shunt headers and are logged for audit (CONTROL is the backend authority).

	- MAMA itself is intentionally non-adaptive at the interface layer; all learning/adaptive logic is routed through CONTROL or domain-specific modules. MAMA does not own memory, schema, or routing logic.
	- Reasoning/math engine selection and execution is governed by CONTROL; MAMA only receives and presents advisory output. All backend actions are subordinate to CONTROL and SECURITY.
	- Context tags and intent fields in the shunt header allow for future context-driven extensions (CONTROL validates all backend context tags).
	- Native executor and context-to-SLAM binder planned for Gen0.5+ (see twin engine plan). All backend execution is routed through CONTROL.

- **Security/Access:**
	- All actions require explicit, protocol-compliant headers. CONTROL validates all backend entry.
	- Authority and routing fields in the header enforce pillar boundaries and prevent unauthorized cross-pillar actions. CONTROL is the backend authority.
	- Audit logging is mandatory for all interface operations (CONTROL is the backend authority).

- **Notes:**
	- MAMA’s design is rooted in military-grade interface doctrine (Signal Corps), with HOTAS and direct operator control as guiding principles. All backend actions are subordinate to CONTROL and SECURITY.
	- Environmental/situational awareness modules (scout, yard, house, mapper) are planned for integration or sharing with SECURITY, clarifying boundaries: SECURITY enforces, MAMA senses and presents. CONTROL is the backend authority.
	- The current implementation is intentionally lightweight for harness and proofing; future work includes native executor, context binding, richer interface state models, and full environmental awareness integration. All backend execution is routed through CONTROL.
	- All evolution must preserve traceability to original intent and protocol rigor. CONTROL is the backend authority.
	- See also: [mama_native_twin_engine_plan.md] for roadmap and missing components.
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
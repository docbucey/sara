# SARA Gen0.5 AI Pillar Specsheet

**Alignment with C# UI Extended Spec:**
  - AI is an adaptable engine and protocol bridge; it does not possess routing, schema, or memory authority for UI actions.
  - All UI/backend actions must be routed through CONTROL, which enforces protocol, ADA/accessibility, mapping, and initialization requirements.
  - AI participates in the hemispheric model as an adaptive/expressive engine (right hemisphere), with all backend entry mediated by CONTROL.
  - No UI module or generative/LLM/AI surface logic may bypass CONTROL to access AI or backend systems.

- **Pillar:** AI

**Purpose:**
  - Enable SARA to function as an adaptable AI engine, supporting LLMs, SLAMs, and other AI models via libraries such as OpenAI and compatible adapters. All backend entry from UI is mediated by CONTROL.
  - Provide a bridge between SARA’s protocol-driven architecture and external AI/model capabilities. CONTROL validates all backend entry from UI.
  - Allow dynamic loading and use of model files as needed for different scenarios and integrations. CONTROL validates all backend entry from UI.
  - Ensure AI operations always depend on at least CORE and CONTROL, plus any other relevant pillar (e.g., MAMA for interface, SECURITY for audit). No UI or LLM/AI surface logic may access AI directly.
  - Support minimal, scenario-driven pillar loading (e.g., VS Code integration may only require CORE and CONTROL). All ADA/accessibility, mapping, and initialization requirements are enforced at the CONTROL boundary.

- **Key Functions/Classes:**
  - Model loader and adapter interfaces for LLMs, SLAMs, and other AI types. CONTROL validates all backend entry from UI.
  - Protocol bridge for routing AI requests through SARA’s shunt header and control logic. CONTROL validates all backend entry from UI.
  - Integration points for AI libraries (OpenAI, HuggingFace, etc.). CONTROL validates all backend entry from UI.
  - Planned: Modular wrappers for new model types and AI workflows. All backend entry is mediated by CONTROL, per the C# UI extended spec.

- **FSM/Protocol:**
  - Follows SARA’s shunt header and protocol enforcement for all AI operations.
  - No direct cross-pillar calls—AI actions are routed through CONTROL and/or relevant pillars.

- **Learning/AI/Context Logic:**
  - AI pillar is adaptive by design, supporting dynamic model selection and context-driven workflows.
  - Context tags and intent fields in the shunt header enable scenario-specific AI behavior.

- **Security/Access:**
  - All AI actions must respect CONTROL and CORE protocol boundaries.
  - Security and audit are inherited from the pillars involved in the workflow.

- **Notes:**
  - The AI pillar is intentionally modular and extensible, designed for future growth and integration.
  - See also: sdk_micro_ai_install_unified_plan.md for installation and integration guidance.
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
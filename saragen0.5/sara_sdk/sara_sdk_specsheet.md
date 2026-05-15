# Primitive Language Model (PLM) Template
Refer to the SARA_SYSTEM_ARCHITECTURE_SPEC.md for the full PLM template. The following summarizes the key points for SDK:

- Minimal, deterministic language/protocol module to prevent bloat
- Modular, with strict boundaries and extension points
- Callable by SARA for integration or code generation tasks
- Deterministic by default; generative/adaptive only when extended
- Core methods: parse, generate, validate, extend
# SARA Gen0.5 SDK Pillar Specsheet

**Alignment with C# UI Extended Spec:**
	- **Self-Training/AI Generation:** SDK provides adapters and integration points for exporting SARA-generated data, training sets, or orchestrating the training of external AI systems. All such integrations are governed by CONTROL and SECURITY protocols.
	- **SHI/Extension Protocols:** SDK implements adapters for new protocol codes and lanes (e.g., SHI, device, IDE, ARM, TV, special-case integrations) as defined by CONTROL.
	- **SDK Protocol Lanes:** SDK is the home for integration lanes and internal AMI codes for AI/model adapters (e.g., Ollama, Gemini, Copilot, openai_local, etc.).
	- **Extension Points:** SDK is ready for new protocol codes and integration lanes as defined by CONTROL and the evolving protocol map.
	- SDK is an enablement and adaptation layer; it does not possess routing, schema, or memory authority for UI actions.
	- All UI/backend actions must be routed through CONTROL, which enforces protocol, ADA/accessibility, mapping, and initialization requirements.
	- SDK participates in the hemispheric model as an adapter/enabler (left hemisphere), with all backend entry mediated by CONTROL.
	- No UI module or generative/LLM/AI surface logic may bypass CONTROL to access SDK or backend systems.

	- **Pillar:** SDK
	- **Self-Training/AI Generation:** SDK provides adapters and protocol lanes for self-training and AI generation, enabling export/import of training data, model checkpoints, and protocol-aligned datasets. All self-improvement and AI generation actions are surfaced through SDK for integration and extension.
	- **Compatibility:** SDK is designed for future extensibility and protocol evolution, while Gen0.5 and earlier generations remain backward compatible with legacy protocols and workflows. SDK can operate fully without an AI/model component; AI integration is present only for compatibility and extension.

**Purpose:**
	- Serve as the enablement and adaptation layer for SARA, supporting expansion, integration, and creative development. All backend entry from UI is mediated by CONTROL.
	- Provide a stable space for compilers, extensions, plugin developers, and advanced contributors to innovate without destabilizing CONTROL or CORE. No UI or LLM/AI surface logic may access SDK directly.
	- Absorb per-target differences and adaptation logic, minimizing the need for CONTROL rewrites. CONTROL validates all backend entry from UI.
	- Remain intentionally open and lightly specified to encourage experimentation and future growth. All ADA/accessibility, mapping, and initialization requirements are enforced at the CONTROL boundary.

	- Adapter and wrapper modules for integrating new targets, compilers, and external systems. CONTROL validates all backend entry from UI.
	- Scaffolding for future AI, plugin, and extension development.
	- Planned: A series of wrappers and adapters to be built after the Gen0.5 rebuild, including an AI spec sheet and dedicated folder in preparation for Gen1.

	- No strict FSM or protocol requirements at this stage; SDK follows the contracts and boundaries enforced by CONTROL and CORE.
	- Future wrappers may introduce their own protocol layers as needed for integration.

	- SDK itself is non-adaptive; it provides scaffolding for others to build adaptive or AI-driven modules.
	- Planned: AI spec sheet and integration points for Gen1.

	- All SDK actions must respect CONTROL and CORE protocol boundaries. CONTROL validates all backend entry from UI.
	- Security and audit are inherited from the pillars SDK integrates with. CONTROL validates all backend entry from UI.

	- SDK is intentionally open to encourage creativity, experimentation, and outside contributions. All backend entry is mediated by CONTROL, per the C# UI extended spec.
	- It is not the project center, but a flexible enablement layer for future compilers, extensions, and plugin developers.
	- See also: sdk_micro_ai_install_unified_plan.md and sdkgen1_final_mapping_summary.md for intent and direction.
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
# Primitive Language Model (PLM) Template
The following template defines a minimal, modular Primitive Language Model (PLM) for SARA Gen0 and future generations. Use this as a reference for implementing or extending PLMs in any pillar or language:

---
**Primitive Language Model (PLM) Template**

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
---
# Primitive Language Model (PLM)
SARA Gen0 introduces the concept of a Primitive Language Model (PLM):

- A PLM is a minimal, foundational language or protocol module designed to prevent model bloat and complexity in future generations.
- PLMs can be invoked by the SARA system for core tasks, or used to generate code for new languages or pillars.
- PLMs enable SARA to extend itself or integrate new protocols/languages without requiring a full AI/LLM.
- This ensures modularity, extensibility, and long-term maintainability.

# Determinism and Generative/Adaptive Modes
SARA and all SSARA (Specialty SARA) systems are always deterministic when operating alone.

- Generative and adaptive behaviors only emerge when SARA is combined with external AI/model components or other forms of extension.
- The architecture allows for future combinations of deterministic, generative, and adaptive modes, but the outcome and behaviors of such combinations are intentionally open for future exploration.

# SARA System Architecture Spec Sheet (Gen1+)

## 1. Overview
While SARA supports integration with AI/model files (LLM, SLM, etc.) for industry and academic compatibility, it does not require an AI component to function. SARA’s architecture is fundamentally UI/protocol-driven and can operate fully without external AI. The AI layer is present for compatibility and extension only. SARA is designed to be future-compatible, supporting new protocols, interfaces, and AI integrations as they emerge. In Gen0.5 and earlier generations, SARA is also backward compatible—able to operate with legacy data, protocols, and workflows. Gen0.5 and future forms of SARA are trained and evolved from previous generations using their own NBS (Narrative Bible System) memory and protocol systems, ensuring continuity and self-improvement across versions.
Most of SARA Gen0.5’s core work is complete, with nearly all foundational and protocol-driven abilities implemented. The only major exceptions are:
	- A direct, native UI (which will be provided by Blender for now)
	- A dedicated AI engine layer (saraai) designed to allow SARA to be plugged into selected Office Suite components for advanced integration and automation
All other system features, protocol enforcement, and extensibility are present and operational in Gen0.5.
SARA, as a whole—including SECURITY, CORE, MAMA, SDK, and CONTROL—functions as an intelligent, protocol-enforcing "monkey-in-the-middle" system. Its primary design is to mediate, secure, and augment interactions between users, native AI backends, and external systems. While SARA includes its own AI and reasoning layers, it is optimized to work alongside the system's native AI when available, providing additional security, audit, and protocol enforcement. This architecture enables secure work-from-home (WFH) operation for Gen0.5 and ensures that future builds (Gen1+) can operate fully independently, with or without external AI dependencies. SARA's intelligence is distributed across all pillars, each contributing to the system's overall safety, extensibility, and autonomy.
SARA is designed as a self-training, self-improving system. It can autonomously refine its own models and workflows using its memory, protocol, and reasoning layers. Additionally, SARA can be used as a generator or trainer for other, more traditional AI systems—producing training data, evaluation sets, or even orchestrating the training of external models through its protocol-driven architecture.
SARA is a modular, protocol-driven AI system designed for safe, auditable, and extensible operation across multiple user interfaces and backends. The architecture is built around five core pillars (CORE, CONTROL, MAMA, SECURITY, SDK), each with strict boundaries and extension points, and is governed by ADA/accessibility and deterministic routing rules. This spec consolidates the current architecture, protocol map, and integration flows, referencing the latest pillar spec sheets, ADA/C# UI extended spec, and the working system file structure.

---


## 2.1 Pillar Remap & Summary (Gen0.5+)

| Pillar   | Core Role | New Additions | Boundaries |
|----------|-----------|---------------|------------|
| CORE     | Data substrate, protocol enforcement | Self-training data/logs, protocol extension | No direct UI/AI access, all via CONTROL |
| CONTROL  | Orchestration, protocol validation, audit | Self-training/AI gen orchestration, protocol extension | All cross-pillar/protocol actions via CONTROL |
| MAMA     | Human interface, ACT-mapped actions | Self-training/AI gen presentation/visualization | All backend actions via CONTROL |
| SECURITY | Audit, gatekeeping, protocol gating | Self-training/AI gen audit/gating | All trust-sensitive actions subject to SECURITY |
| SDK      | Adapter/integration layer | Self-training/AI gen adapters/export | All integrations via CONTROL/SECURITY |

**Descriptions:**
- **CORE:** Handles all persistent data, memory, and protocol enforcement. Now supports self-training data/logs and is ready for protocol extension (e.g., SHI). No direct UI or AI access—everything routes through CONTROL.
- **CONTROL:** Orchestrates all system actions, validates protocols, audits, and governs reasoning/math engines. Now explicitly manages self-training/AI generation workflows and protocol extension. All cross-pillar and protocol actions must pass through CONTROL.
- **MAMA:** Provides the human interface, UX, and ACT-mapped entrypoints. Now presents/initiates/visualizes self-training and AI generation, but does not govern or execute them. All backend actions are routed through CONTROL.
- **SECURITY:** Audits, gates, and quarantines all actions, with protocol gating for AMIP/AMIPI, SHI, ACT, and more. Now audits/gates all self-training and AI generation for compliance and safety. All trust-sensitive actions are subject to SECURITY protocol and consent boundaries.
- **SDK:** Adapter/integration layer for new protocol lanes (Ollama, Gemini, Copilot, device, IDE, ARM, TV). Now provides adapters/integration for exporting SARA-generated data, training sets, or orchestrating external AI training. All integrations are governed by CONTROL and SECURITY protocols.

### Foundation Layer (CORE)
- **Purpose:** Data substrate, file/memory management, protocol enforcement (AMIP/AMIPI, VNCE, Office/Media IO)
- **Key Protocols:** AMIP/AMIPI, VNCE, Office/Media
- **Extension Points:** New protocol handlers (e.g., SHI)
- **Spec Reference:** See `sara_core_specsheet.md`

### Orchestration Layer (CONTROL)
- **Purpose:** Routing, protocol validation, audit, reasoning/math engine governance, protocol extension (SHI, ACT, SDK lanes)
- **Key Protocols:** AMIP/AMIPI, VNCE, SHI, ACT
- **Extension Points:** New protocol codes, device/IDE lanes
- **Spec Reference:** See `sara_control_specsheet.md`

### Interface Layer (MAMA)
- **Purpose:** Human interface, UX, protocol-compliant entrypoint, ACT-mapped actions
- **Key Protocols:** ACT codes
- **Extension Points:** New mapped actions, context tags
- **Spec Reference:** See `sara_mama_specsheet.md`

### Security Layer (SECURITY)
- **Purpose:** Audit, gatekeeping, quarantine, protocol gating (AMIP/AMIPI, SHI, ACT)
- **Key Protocols:** AMIP/AMIPI, SHI, ACT
- **Extension Points:** New security codes, trust-state actions
- **Spec Reference:** See `sara_security_specsheet.md`

### Enablement Layer (SDK)
- **Purpose:** Adapter/integration layer for new protocol lanes (Ollama, Gemini, Copilot, device, IDE, ARM, TV)
- **Key Protocols:** SHI, SDK protocol lanes
- **Extension Points:** New adapters, protocol lanes
- **Spec Reference:** See `sara_sdk_specsheet.md`

---

## 2.2 Universal UI Governance Standard

Every user-facing surface in SARA — input mapper, office suite, creative tools, video editor, photo editor, IDE, cockpit, VNCE — must conform to this governance standard. No surface is exempt.

### The Universal Test
If a 10–12 year old with no interest in technology and zero reading of any manual can identify what every control does and complete their first task in under 60 seconds, the surface passes. If they hesitate or need to read anything to proceed, it fails.

This standard does not relax for complex tools. **The more cognitive work a task demands, the harder the interface must work to stay out of the way.** When a user's mental energy is spent on the task itself — writing code, editing video, composing — there is nothing left to spend learning the tool. Complexity of the domain is not permission to add complexity to the surface. It is the reason to remove it.

### Non-Negotiable Rules (All Surfaces)
- **Plain English everywhere on primary surfaces.** Technical terms belong in menus, tooltips, and advanced panels — never on buttons, labels, or first-view prompts.
- **Action-first language.** Buttons and prompts use everyday verbs: "Find", "Teach", "Save", "Try It". Never "Refresh", "Configure", "Apply", "Remove", "Submit".
- **Status in plain English.** No boolean flags, no color dots without text, no codes. "✓ Ready", "Not connected", "SARA is ready" — not "Status: True" or a lone indicator.
- **Progressive disclosure.** Complex settings are accessible but not visible on first view. Show what matters for the current step only.
- **One question at a time.** Multi-column form grids are replaced by guided sequential prompts: "What should happen when you press this?" not a 5-column editor grid.
- **No placeholder content.** Body diagrams, legends, and dev-facing debug panels are not shown to end users. If it doesn't immediately help the user, it is removed.
- **The IDE is not exempt.** A code editor used by someone with a learning disability requires the same zero-friction standard. The task is already hard. The tool must not add to that.

### Simplicity Scale by Surface

| Surface | Task Complexity | UI Simplicity Requirement |
|---------|----------------|--------------------------|
| Disability Mapper | Low | Maximum — and that ceiling applies to all surfaces below |
| Office Suite | Low–Medium | Maximum |
| Photo / Creative Suite | Medium | Maximum — drag in, do the thing, save. Advanced tools revealed progressively. |
| Video Editor | Medium–High | Maximum — the task is hard enough. First actions must be completely obvious. |
| IDE / Code Editor | High | **Maximum** — highest task complexity means highest simplicity requirement. Writing code is the work. Finding the button must not be. |
| Cockpit / Control | High | Maximum |
| VNCE / Remote | High | Maximum |

### Reference Implementation
The Disability Mapper C# UI (`DisabilityMapper/DisabilityMapper/MainWindow.xaml`) is the canonical reference for maximum-simplicity surface design. See `SPEC_SHEET_GEN0_CSHARP_EXTENDED.md` Section 1.1 for the documented design target and its rules.

All future SARA UI work — regardless of pillar, language, or framework — is measured against this standard at the appropriate row in the table above.

---

## 3. File Structure & Integration
- **Sara_core.py:** Foundation, memory, file IO, protocol enforcement
- **sara_control.py:** Orchestration, SARA class, AI backend, protocol routing
- **sara_ide.py:** IDE/VS Code integration, UI, voice I/O, main entrypoint
- **sara_mama.py:** TTS and speech recognition, UX functions
- **projectsara/**: User and SARA profiles, NBS memory files

---

## 4. Data & Control Flow

### Text Input (IDE/UI)
User → `sara_ide.py` (handle_send_to_agent_button) → `sara_control.py` (SARA.ask) → `Sara_core.py` (memory/protocol) → `sara_control.py` (response) → `sara_mama.py` (TTS) → User

### Voice Input
User → `sara_ide.py` (handle_microphone_button_press) → `sara_mama.py` (speech_to_text) → `sara_control.py` (SARA.ask) → `Sara_core.py` (memory/protocol) → `sara_mama.py` (TTS) → User

### Protocol Enforcement
All cross-pillar actions use shunt header envelopes (AMIP/AMIPI, VNCE, SHI, ACT) and are routed through CONTROL. No direct calls or raw data cross pillar boundaries.

---

## 5. Protocol & Extension Map
| Protocol/Code         | CORE   | CONTROL | MAMA   | SECURITY | SDK    |
|-----------------------|--------|---------|--------|----------|--------|
| AMIP/AMIPI            | ✓      | ✓       |        | ✓        |        |
| VNCE                  | ✓      | ✓       |        |          |        |
| SHI/Ext. Protocols    |        | ✓       |        | ✓ (if sec)| ✓      |
| ACT Codes             |        | ✓       | ✓      | ✓        |        |
| Office/Media Protocol | ✓      | ✓       |        |          |        |
| SDK Protocol Lanes    |        |         |        |          | ✓      |

---

## 6. ADA & Accessibility
- All UI and protocol flows are governed by ADA/C# UI extended spec (see `SPEC_SHEET_GEN0_CSHARP_EXTENDED.md`).
- No UI feature may bypass CONTROL or weaken SECURITY.
- All accessibility, mapping, and initialization requirements are enforced at CONTROL boundary.

---

## 7. Integration & Upgrade Notes
- All protocol and extension points are modularized for safe upgrades.
- Removed/consolidated files are documented in `SARA_ARCHITECTURE.md`.
- IDE/VS Code integration is supported via Python or TypeScript extension (see architecture doc for details).

---

## 8. References
- `sara_core_specsheet.md`, `sara_control_specsheet.md`, `sara_mama_specsheet.md`, `sara_security_specsheet.md`, `sara_sdk_specsheet.md`
- `SPEC_SHEET_GEN0_CSHARP_EXTENDED.md`
- `SARA_ARCHITECTURE.md`

---

*This spec sheet is the authoritative reference for SARA system architecture, protocol boundaries, and extension strategy. All future upgrades and repairs must conform to these boundaries and extension points.*

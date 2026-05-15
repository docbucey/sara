# SARA Gen0.1 C# UI Extended Spec Sheet
**Version family:** `Gen0.1-C#-UI-Extended`

> **Status:** Specification and planning only  
> **Code changes:** None  
> **Purpose:** Extend the C# front-end specification using `sara_spec_map_and_reconciliation.json` as the authoritative reconciliation source for ADA/accessibility, cockpit behavior, WFH/VNCE presentation, and Lite-aligned front-end boundaries.

---

## 1. Scope and Purpose

This document extends the C# front-end specification for SARA using the reconciled workspace spec map as the authoritative source for:

- ADA and accessibility expectations
- low-strain and approachable interaction behavior
- Office Suite and cockpit UI direction
- WFH and VNCE-facing operator surfaces
- Lite and micro-pillar presentation roles
- the C# runtime's relationship to the 5-pillar governance model and mapping files

This is a **front-end specification only**. It does not define new routing rules, new schemas, new authority planes, or backend execution behavior.

---

## 2. Authoritative Inputs

Primary source set for this extended UI spec:

- `sara_spec_map_and_reconciliation.json`
- `SPEC_SHEET_GEN0_CSHARP.md`
- `OFFICE_SUITE_SARA_SPEC.md`
- `sara_gen0.1-spec.md`
- `sara_gen1_stage4_specsheet.md`
- `shunt_map_descriptor.updated.json`
- `actionmap.updated.json`
- `claywork/saragen0finish/sara_mama/sara_interface_refactor_spec.mak`
- `claywork/saragen0finish/sara_mama/sara_morning_install_training_spec.mak`
- `micro_sara_embedding_plan.json`
- `sara_lite_os_unified_build_plan.json`
- `desktop_vnce_node_iso_build_plan_with_ide.json`
- `desktop_vnce_node_iso_build_plan.json`
- `vnce_remote_node_requirements.json`

---

## 3. Invariants and Boundaries

The C# UI must preserve all existing pillar and safety boundaries:

- **UI has no routing authority**
- **CONTROL remains the primary routing authority**
- **SECURITY remains the gate and trust layer**
- **CORE remains the foundation and profile truth source**
- **MAMA remains the humane presentation layer**
- **SDK remains adapter-only**
- no UI feature may bypass **CONTROL**
- no theme, personality, or cockpit layer may weaken **SECURITY**
- no phase may introduce new schemas, new routes, or new authority bits
- all front-end behavior remains **local-first, deterministic, and auditable**
- learning, memory, evolution, and governance remain **SARA pillar responsibilities**, not C# UI responsibilities
- generative/LLM presentation remains a **surface layer**, not a governing layer

---

# Phase 0 — C# Runtime Bootstrap & Governance Alignment
**Version Family:** `Gen0.1-C#-UI-Extended`  
**Authority Level:** Foundational (UI-only, non-pillar)

## Purpose
Establish the initialization rules that ensure the C# runtime understands the SARA governance model, routing model, shunt model, and its own role as a generative/UX surface.

## 0.1 Scope of Phase 0
Phase 0 defines the startup behavior of the C# front-end.
It ensures that before any UI, personality, theme, or voice features activate, the C# runtime:

- loads the authoritative mapping files
- loads the spec-map
- understands the 5-pillar governance model
- understands the Bucey Shunt routing rules
- binds itself to CONTROL as the only backend entrypoint
- identifies itself as a surface-only LLM/UX layer
- acknowledges that learning, memory, evolution, and governance belong to SARA, not the C# layer

This phase is mandatory and must run before any other UI phases.

## 0.2 Required Mapping Files (Loaded at Startup)
The C# runtime must load the following files discovered in the repository:

### Routing & Authority Maps
- `shunt_map_descriptor.updated.json`
- `actionmap.updated.json`

### Schema & Boundary Contracts
- `amip_v0_1_schema.json`
- `amip_amipi_surgical_expansion_plan.json`
- `vnce_remote_node_requirements.json`

### Pillar & Architecture Specs
- `sara_gen0.1-spec.md`
- `sara_gen1_stage4_specsheet.md`
- `SPEC_SHEET_GEN0_CSHARP.md`
- `OFFICE_SUITE_SARA_SPEC.md`

### Lite / Micro-Pillar Plans
- `micro_sara_embedding_plan.json`
- `sara_lite_os_unified_build_plan.json`

### Unified Spec Map
- `sara_spec_map_and_reconciliation.json`

These files define the rules of the world for the C# runtime.

## 0.3 Governance Model (5 Pillars)
The C# runtime must treat the five pillars as authoritative governance, not as components it controls.

### Pillars
- **CONTROL** — routing authority
- **SECURITY** — gating authority
- **CORE** — structural authority
- **MAMA** — memory/UX authority
- **SDK** — adapter authority

### C# Runtime Role
- NOT a pillar
- NOT a routing authority
- NOT a security authority
- NOT a schema owner
- NOT a memory/evolution owner

The C# layer is a surface — a renderer, a personality engine, a theme engine, and a voice interface.

All authoritative behavior remains in the pillars.

## 0.4 Routing Model (Bucey Shunt Header Required)
All backend actions initiated from the C# runtime must:

1. construct a Bucey Shunt header
2. validate the request against:
   - `shunt_map_descriptor.updated.json`
   - `actionmap.updated.json`
3. wrap the payload in the existing AMIP/AMIPI-aligned boundary format
4. send the request to `sara_controlgen1.py`
5. allow CONTROL to route
6. allow SECURITY to gate
7. receive the response through the same shunt channel

### C# MAY NOT
- call Python directly outside the governed boundary
- call any pillar directly as a bypass path
- call OS/network directly as a substitute for governed routes
- bypass CONTROL or SECURITY
- generate raw AMIP/AMIPI behavior outside validated boundary alignment

This preserves the deterministic routing model.

## 0.5 LLM/UX Surface-Only Contract
The C# runtime must treat all generative behavior as surface-only.

### Allowed (UI-only)
- personality
- humor
- sarcasm
- tone presets
- theme generation
- voice UX
- layout adaptation
- accessibility adaptation
- user-machine adaptation
- AI-profile-aware UX

### Not Allowed (belongs to SARA)
- learning
- memory
- self.evolve
- schema modification
- routing logic
- security logic
- NBS writes (except user preferences)
- trust-policy changes

The C# layer expresses behavior.  
SARA governs behavior.

## 0.6 80/20 Activity Model
The C# runtime must assume:

- **80% of system activity is UI/UX/generative surface**
- **20% is authoritative pillar behavior**

This ensures:
- the UI remains responsive
- the pillars remain deterministic
- the system remains safe
- the architecture remains stable

The C# layer must never attempt to “take over” the authoritative 20%.

## 0.7 Initialization Sequence (Phase 0 Boot Order)
1. Load spec-map
2. Load mapping files
3. Load pillar definitions
4. Load shunt map
5. Load action map
6. Load AMIP/AMIPI boundary references
7. Load Lite/micro-pillar plans
8. Initialize `PlatformAdapter`
9. Initialize `ADAEngine`
10. Initialize `PersonalityEngine`
11. Initialize `ThemeManager`
12. Initialize `VoiceInteractionManager`
13. Bind CONTROL routing adapter
14. Bind SECURITY gating adapter
15. Enter Phase 1 (ADA Empowerment)

## 0.8 Invariants of Phase 0
- No UI module may activate before Phase 0 completes.
- No backend call may occur without a Bucey Shunt header.
- No generative behavior may bypass CONTROL or SECURITY.
- No C# module may assume authority over routing, schema, or memory.
- All future phases must inherit Phase 0 constraints.

## Core C# modules
- `ShuntMapLoader`
- `ActionMapLoader`
- `PillarGovernanceModel`
- `ControlRouteClient`
- `UiSurfacePolicy`
- `GenerativePresentationSurface`
- `BoundaryComplianceViewModel`
- `PlatformAdapter`
- `ADAEngine`
- `PersonalityEngine`
- `ThemeManager`
- `VoiceInteractionManager`

## Key fields / structures
- `ShuntMapDescriptor`
- `ActionOwnershipMap`
- `PillarGovernanceState`
- `ControlRouteRequest`
- `UiSurfacePolicy`
- `PresentationOnlyProfile`
- `BoundaryComplianceState`
- `AccessibilityProfile`
- `PlatformUiProfile`

## ADA and pillar alignment
This phase supports approachability by ensuring the front-end becomes understandable, accessible, and polished only after it binds itself to the existing five-pillar system and its non-bypass rules.
- no backend policy invention
- all action semantics remain owned by the existing SARA pillars

## ADA and pillar alignment
This phase supports approachability by making the front-end understandable and safe without turning it into a shadow backend. The operator experiences a strong, polished UI surface while the existing five-pillar system remains authoritative.

## Phase 0: Right-Hemisphere Computational Architecture
This subsection defines the LLM-style computational hemisphere as an expressive architecture layer responsible for generative/compression/narrative processing roles at the architectural level.

The right-hemisphere computational layer is explicitly non-authoritative. It does not own routing, schema control, trust policy, or pillar governance. It operates in strict subordination to the structured hemisphere and remains bounded by the existing five-pillar authority model.

## Corpus Callosum Protocol (Inter-Hemispheric Substrate)
The Corpus Callosum Protocol is defined as the inter-hemispheric state-engine substrate.

Its architectural role is to:

- provide synchronization between the structured and LLM-style hemispheres
- perform stability/resonance transformation across cross-hemisphere state exchange
- act as the primary bridge for inter-hemispheric transfer and coherence

This protocol is a foundational computational substrate and does not replace pillar authority.

## Forceps Minor: Executive Integration Gateway
The Forceps Minor is defined as the executive integration gateway above the corpus callosum substrate.

Its architectural role is to:

- synthesize cross-hemisphere goals and priorities
- coordinate high-level executive alignment between hemispheres
- operate as the frontal-lobe counterpart to the corpus callosum protocol

This layer governs executive integration framing, not runtime authority reassignment.

## Supporting Integration Pathways
The architectural integration pathways include:

- **Cingulum Bundle**: memory-emotion-executive loop across cross-hemisphere integration
- **Superior Longitudinal Fasciculus (SLF)**: planning and language integration pathway across long-range hemisphere exchange
- **Uncinate Fasciculus**: meaning-valuation bridge for cross-hemisphere semantic alignment

These pathways are specified as specialized connective channels in the hemispheric model.

## Hemispheric Framing Model
Phase 0 hemispheric framing is defined as:

- **Left Hemisphere** = the five pillars (CORE, CONTROL, SECURITY, MAMA, SDK)
- **Right Hemisphere** = the LLM-style expressive engine
- **Corpus Callosum Protocol** = synchronization substrate
- **Forceps Minor** = executive integration gateway
- **Supporting fasciculi** = specialized connective pathways

This Phase 0 extension remains architectural documentation only and does not introduce runtime integration code.

## Right-Hemisphere Model Stack (Future AI Surface)
This section defines a forward-looking model-stack target for the right-hemisphere computational side of the architecture.

The right-hemisphere model stack is complementary to the structured pillar side and is intended for integration in later phases through the hemispheric integration model, including corpus-callosum synchronization pathways.

This section does not change Gen0 behavior, does not alter Gen0 authority boundaries, and does not wire runtime execution in the current phase.

### Generative Pretrained Transformers (GPT)
- **Role:** foundation models for human-like text generation and broad general reasoning.
- **Examples:** GPT-4-class, LLaMA-class.
- **Use:** narrative, explanation, summarization, dialog surfaces.

### Small Language Models (SLM)
- **Role:** compact, efficient models for low-latency, on-device, and higher-privacy use.
- **Examples:** Phi-3-class, Mistral 7B-class.
- **Use:** edge devices, offline or limited-connectivity operation, privacy-sensitive flows.

### Large Reasoning Models (LRM)
- **Role:** complex multi-step logical, mathematical, and analytical reasoning.
- **Examples:** o1-class, Claude 3.5-class.
- **Use:** deep reasoning, planning, verification, and analysis tasks.

### Vision-Language Models (VLM)
- **Role:** multimodal models that understand and relate text and visual inputs.
- **Examples:** GPT-4V-class, Gemini-class.
- **Use:** document understanding, UI/state inspection, visual context reasoning.

### Large Action Models (LAM)
- **Role:** tool-using and action-taking agents focused on doing, not just saying.
- **Use:** orchestrating tools, workflows, and external systems under strict governance.

### Phase Framing
- This stack is the other side of the AI architecture and is complementary to the structured pillar side.
- Integration is planned for later phases via hemispheric and corpus-callosum protocols.
- Gen0 behavior remains unchanged in the current baseline.
- This is a forward-looking architectural specification target only.

## Right Hemisphere (Expressive Engine) — JSON-Mapped Interface Backed by Local Ollama
In Phase 0, the right hemisphere is implemented as a bounded JSON-mapped interface.

All expressive or generative requests are packaged by CONTROL and exchanged through the corpus callosum protocol.

The local Ollama instance is the Phase 0 implementation of the expressive engine.

Ollama is explicitly non-authoritative, non-routing, and subordinate to CONTROL and SECURITY.

## Ollama Integration Contract (Phase 0)
- Ollama receives JSON-wrapped prompts only.
- Ollama returns JSON-wrapped responses only.
- No direct system access, no tool use, and no autonomous behavior are permitted.
- CONTROL constructs the request header and validates the response boundary.
- SECURITY enforces all gating and boundary checks.
- SDK handles adapter-level transport only.

## Hemispheric Framing (Phase 0 Implementation)
- **Left Hemisphere** = the five pillars (CORE, CONTROL, SECURITY, MAMA, SDK)
- **Right Hemisphere** = Ollama-backed JSON interface
- **Corpus Callosum Protocol** = the state-engine substrate mediating exchange
- **Forceps Minor** = executive integration gateway (non-model)
- No local large-model stack is deployed in Phase 0.

## Hardware-Safe Constraints
- Ollama must run only compact or quantized models in Phase 0.
- No multimodal, VLM, LRM, or LAM workloads are deployed locally in Phase 0.
- No concurrent multi-model orchestration is permitted in Phase 0.
- Heavy workloads are deferred to Phase 2+ or home-server/cloud deployment.

## Hemispheric Integration Layer (Formalized Phase 0 Extension)
This subsection formalizes the integration layer between structured logic and generative expression in Phase 0.

## Corpus Callosum Protocol
The Corpus Callosum Protocol is defined as a bidirectional synchronization substrate.

It serves as:

- a stability/resonance transformation engine
- the primary inter-hemispheric bridge between structured logic and generative expression
- a foundational computational layer not tied to any specific implementation

## Forceps Minor: Prefrontal Integration Gateway
The Forceps Minor is defined as the executive coordination bridge across hemispheres.

It serves as:

- the synthesis layer for goals, priorities, and high-level decisions across both hemispheres
- the layer positioned above the corpus callosum substrate
- the frontal-lobe counterpart to the corpus callosum protocol

## Supporting Fasciculi (Integration Pathways)
The supporting integration pathways are defined as:

- **Cingulum Bundle**: memory-emotion-executive loop connecting profile, memory, and tone systems with generative expression
- **Superior Longitudinal Fasciculus (SLF)**: long-range planning and language integration bus connecting structural logic, planning, and generative language
- **Uncinate Fasciculus**: meaning-valuation bridge connecting personalization, semantic nuance, and expressive generation

## Hemispheric Framing
Phase 0 hemispheric framing is defined as:

- **Left Hemisphere** = structured logic layer (the five pillars: CORE, CONTROL, SECURITY, MAMA, SDK)
- **Right Hemisphere** = generative/LLM-style expressive layer
- **Corpus Callosum Protocol** = synchronization substrate between hemispheres
- **Forceps Minor** = executive integration gateway
- **Supporting fasciculi** = specialized integration pathways

## Phase 0 Contract Clarification
Phase 0:

- defines the integration contract between hemispheres
- does not grant authority to the generative side
- establishes how structured logic and generative expression coordinate
- remains a documentation/specification layer only and does not introduce runtime code changes

Shunt protocol behavior remains governed by the structured logic stack and CONTROL-routed boundaries, including the established shunt protocol lineage in `sara_coregen1.py`.

---

# Phase 1 — U.S.-General Accessibility and Basic Interface

## Scope
Establish the default C# UI as a **U.S.-general accessible and approachable operator surface**.
This phase is generated from the reconciled spec map and the existing SARA pillar protocol lineage. It is **not legal advice**, does **not** quote statutes verbatim, and does **not** treat any one state-specific or condition-specific profile as the whole standard. Instead, it summarizes broad U.S. accessibility expectations and uses the SARA accessibility hooks as **seed references** for implementation.

## Phase 1 Entry Criteria
Phase 1 may begin only after Phase 0 canonical lock is satisfied.

For expressive operations in Phase 1, the frozen **CONTROL-routed expressive path** is the only valid route:

- CONTROL -> OSH (Ollama Shunt System) -> Ollama JSON-interface right hemisphere -> OSH -> CONTROL

No alternate expressive route is allowed in Phase 1.

## Phase 1 Generation Basis
The matrix below is derived from the following internal sources already reconciled in the workspace:

- `sara_spec_map_and_reconciliation.json`
- `sara_coregen1.py`
- `sara_security.py` and Gen1 security descendants
- `sara_controlgen1.py`
- `sara_gen0.1-spec.md`
- `sara_gen1_stage4_specsheet.md`
- `canonical_pillars_update_and_samples.txt`
- the pillar `.mak` files under `claywork/saragen0finish/`
- `shunt_map_descriptor.updated.json`
- `actionmap.updated.json`
- `amip_v0_1_schema.json`
- `amip_amipi_surgical_expansion_plan.json`
- `vnce_remote_node_requirements.json`
- `ai_profile_evolution_extensions.json`
- `sara_self_evolve_protocol.json`
- `micro_sara_embedding_plan.json`

## Pillar-Governed Matrix Protocol
- **CONTROL** governs routing for accessibility-related actions and surface requests.
- **SECURITY** governs gating for sensitive accessibility changes, device access, and trust-sensitive operations.
- **CORE** defines structural limits, deterministic UI adaptation boundaries, and profile-safe shape constraints.
- **MAMA** governs low-strain defaults, guided UX, readable summaries, and accessibility-memory behavior.
- **SDK** remains adapter-only and may not override accessibility policy.

## Goals
- make the Basic Interface the default low-friction mode
- reduce cognitive strain, click depth, and unnecessary motion
- preserve equivalent access across keyboard, pointer, and voice-assisted interaction
- keep status, trust, health, and recovery messaging readable and understandable
- allow user preference adaptation without creating new backend authority

## Core C# modules
- `BasicInterfaceShell`
- `AccessibilityProfile`
- `HudGeometryManager`
- `LowStrainStatusPanel`
- `SessionHealthView`
- `SettingsProfileView`

## Key fields / structures
- `AccessibilityProfile`
- `HudLayoutState`
- `VisualAccessibilitySettings`
- `InputAssistSettings`
- `EnvironmentProfile`
- `ReadableMessagePolicy`
- `InteractionModeProfile`

## Invariants
- presentation only
- no routing logic
- no direct backend execution
- no exposure of shunt metadata or internal IDs
- accessibility preferences may adapt presentation, but never governance, routing, or trust policy

## Phase 1 Routing and Safety
All expressive operations in Phase 1 must use the frozen Phase 0 path through the JSON-interface right hemisphere and OSH (Ollama Shunt System).

Phase 1 routing and safety invariants:

- CONTROL remains the sole routing authority for all expressive and non-expressive paths.
- SECURITY must gate allow, deny, constrain, and schema-fail outcomes.
- The UI may render state and guidance but may not alter routing or gate outcomes.
- Any generic expressive reference in Phase 1 is interpreted as the CONTROL-routed expressive path through OSH and the JSON-interface right hemisphere.

## Phase 1 UI State Model for OSH Pipeline Visibility
Phase 1 must provide deterministic operator-visible states for each OSH stage in the CONTROL-routed expressive path.

Required UI-visible stage states:

- **OSH-1 Intake**: request received, header validated, awaiting gate decision
- **OSH-2 Normalization**: response shaping in progress, output envelope normalization active
- **OSH-3 Boundary**: policy boundary inspection active, restricted content checks running
- **OSH-4 Schema**: schema conformance verification active on request/response envelopes
- **OSH-5 Non-Authority**: non-authority guarantees being verified before CONTROL acceptance

For each stage, UI messaging must be deterministic, plain-language, and non-ambiguous.

## Phase 1 Accessibility Behavior
Phase 1 must preserve ADA-safe behavior for expressive outcomes without changing authority boundaries.

Required accessibility behaviors:

- **Constrained model responses**: present clear constrained-state explanation and approved next-step guidance.
- **Denied model responses**: present non-punitive denial language with safe recovery options.
- **Schema-fail responses**: present schema-fail status with understandable remediation guidance.
- **Boundary-blocked responses**: present boundary-protection explanation and permitted fallback actions.

All such messaging must remain low-strain, readable, and equivalent across supported interaction modes.

## Phase 1 Background Artifact Alignment
Phase 1 must reference the frozen Phase 0 JSON map set for background C# runtime alignment:

- `corpus_callosum.json`
- `forceps_minor.json`
- `cingulum_bundle.json`
- `slf.json`
- `uncinate.json`
- `ollama_shunt_map.json`
- `ollama_action_map.json`
- `right_hemisphere_interface.json`

No ad hoc, alternate, or caller-specific map variants are allowed in Phase 1.

## Phase 1 Accessibility Compliance Matrix

| Requirement (summarized) | Source family | Pillar responsible | Protocol reference | Existing coverage in SARA specs | Gaps / missing coverage | Recommended C# UI implementation notes (UI-only) | User-specific relevance |
|---|---|---|---|---|---|---|---|
| Core tasks should remain available through more than one interaction path where practical. | ADA Title II/III summary, Section 508, WCAG 2.1 AA | `MAMA`, `CONTROL` | `sara_mamagen1.py` UX adaptation lineage; `sara_controlgen1.py` route ownership | `voice_first`, `low_click`, guided prompts, Basic Interface default | No single formal C# matrix previously tied these rules together | Keep important actions reachable by keyboard, pointer, and bounded voice-assisted flows without changing route ownership. | High for any `AccessibilityProfile` preferring lower-friction or alternative input access. |
| Status, trust, and health information should be perceivable and readable. | ADA summary, Section 508, WCAG 2.1 AA | `MAMA`, `CORE` | `SPEC_SHEET_GEN0_CSHARP.md`; `OFFICE_SUITE_SARA_SPEC.md`; CORE profile constraints | readable HUD, low-strain panels, high-contrast-friendly direction | Contrast/readability expectations were dispersed across multiple specs | Use scalable text, clear labels, stable contrast-safe themes, and do not encode meaning by color alone. | High for profiles preferring larger text, stronger contrast, or lower visual strain. |
| Navigation should remain predictable, consistent, and easy to learn. | ADA summary, WCAG 2.1 AA, U.S.-general usability expectations | `CORE`, `MAMA` | `sara_interface_refactor_spec.mak`; `sara_gen0.1-spec.md` | Basic Interface vs Study Mode; predictable HUD geometry | No unified matrix row previously mapped predictability to Phase 1 | Preserve stable control placement, familiar zones, and visible pathing for primary tasks. | High for new-user, fatigue-sensitive, or guidance-preferring profiles. |
| The UI should reduce unnecessary motion, click depth, and cognitive burden. | Section 508, WCAG 2.1 AA, cognitive-access seed references | `MAMA`, `CORE` | `sara_mamagen1.py` low-strain adaptation; interface refactor guidance | reduced animation, reduced/guided cognitive load, low-click behavior | Need explicit Phase 1 wording for reduced-motion and guided-mode defaults | Support reduced-motion mode, short workflows, and step-by-step prompts with plain wording. | High for profiles preferring reduced motion, guided prompts, or simplified views. |
| Voice and alternative-input support should be available without making voice mandatory. | ADA summary, Section 508, speech/voice-access seed references | `MAMA`, `SDK` | MAMA voice-first lineage; SDK adapter-only boundary | read-aloud direction, voice-first behavior, bounded adapter role | Voice support was implied, but not fully normalized in one C# matrix | Offer voice-driven UI configuration with clear keyboard and pointer fallbacks at all times. | High for profiles preferring speech assistance, hands-reduced interaction, or mixed-input use. |
| Errors, blocked actions, and constrained modes should explain what happened and what to do next. | ADA summary, U.S.-general accessibility/approachability expectations | `MAMA`, `SECURITY`, `CONTROL` | `present_amipi_result_mama()` lineage; security allow/challenge/quarantine outcomes | session health views, MAMA summaries, constrained-mode messaging direction | Need stronger consistency rules for recovery wording across surfaces | Use plain-language error text, clear next steps, and non-punitive trust-state explanations. | High for any profile needing reassurance, clearer recovery, or guided troubleshooting. |
| Accessibility preferences may adapt presentation, but must not alter system authority or policy. | ADA summary, Section 508, SARA governance constraints | `CORE`, `CONTROL`, `SECURITY` | `sara_gen1_stage4_specsheet.md`; `actionmap.updated.json`; `shunt_map_descriptor.updated.json` | strong control-routed and shunt-governed boundary rules | Prior UI specs did not always state this boundary directly inside Phase 1 | Persist only UI-facing preferences such as contrast, spacing, motion, tone, and voice feedback. | Relevant to all profiles; protects safe personalization without policy drift. |
| Sensitive accessibility changes involving device capture, trust state, or remote surface behavior must remain gated. | ADA summary, Section 508, trust-sensitive U.S.-general expectations | `SECURITY`, `CONTROL` | `sara_security.py` lineage; `sara_securitygen1.py`; `vnce_remote_node_requirements.json` | SECURITY-first gating, STABLES-aware identity and challenge flows | Needs a clearer explicit link between accessibility actions and security consent boundaries | Require explicit consent and Control-routed handling for microphone, remote input, or trust-sensitive surface changes. | High when `AccessibilityProfile` requests voice or remote-surface assistance features. |
| Accessibility and approachability should remain consistent across desktop, cockpit, and VNCE-facing views. | ADA summary, Section 508, WCAG 2.1 AA, state-level seed references only | `MAMA`, `CONTROL`, `SDK` | Lite cockpit plans; VNCE requirements; Office/UI specs | cross-surface direction exists in Lite, Office, and VNCE planning docs | C# implementation notes had not previously been unified into one phase table | Maintain consistent defaults and bounded platform-specific variation across Windows and Lite-facing surfaces. | High for profiles moving between workstation, cockpit, and remote-view contexts. |
| JSON schema failure handling in the expressive path should be visible, understandable, and safely recoverable. | ADA summary, Section 508, WCAG 2.1 AA | `CONTROL`, `SECURITY`, `MAMA` | `right_hemisphere_interface.json`; `ollama_shunt_map.json`; OSH-4 schema stage | schema-fail semantics are present in architecture but not fully reflected in Phase 1 UX matrix | Need explicit Phase 1 UI contract for schema-fail messaging and fallback behavior | Present schema-fail as a clear state with plain-language explanation and approved retry/fallback options through the CONTROL-routed expressive path. | High for all profiles, especially users needing predictable recovery guidance. |
| Non-authority enforcement visibility should be explicit whenever expressive output is constrained by governance rules. | ADA summary, Section 508, governance transparency expectations | `CONTROL`, `SECURITY`, `MAMA` | OSH-5 non-authority stage; `ollama_action_map.json` | non-authority guarantees are defined, but operator-visible language requirements were not explicit in Phase 1 | Need direct UX language for why output may be limited without implying system failure | Show a deterministic non-authority status message that explains safety enforcement while preserving readability and trust clarity. | High for guidance-preferring and low-strain profiles. |
| Gated fallback behavior should remain deterministic when expressive requests are denied, constrained, or boundary-blocked. | ADA summary, Section 508, WCAG 2.1 AA | `SECURITY`, `CONTROL`, `MAMA` | SECURITY allow/deny/constrain outcomes; OSH-3 boundary stage | fallback handling exists conceptually but lacks Phase 1 matrix-level specificity | Need standardized fallback sequence for denied/constrained expressive operations | Provide a consistent fallback path: explain state, present safe alternatives, and keep interaction continuity without route bypass. | High for all profiles; critical for resilient accessibility workflows. |
| OSH-stage UI state mapping should expose deterministic pipeline visibility for intake, normalization, boundary, schema, and non-authority checks. | ADA summary, Section 508, approachability and transparency expectations | `CONTROL`, `SECURITY`, `MAMA` | `ollama_shunt_map.json`; OSH-1..OSH-5 stage model | stage-level visibility requirements were not previously formalized in Phase 1 | Need explicit stage-to-message mapping for operator-facing status surfaces | Render deterministic state labels and plain-language progress messaging for OSH-1 through OSH-5 in the CONTROL-routed expressive path. | High for fatigue-sensitive and guidance-preferring profiles. |

## Alignment Note
The references found in the pillar codebase and reconciled spec set are used here as **default seed starts** to help build this matrix. Federal families such as ADA, Section 508, and WCAG provide the general framing; any TN/KY/MS-style references remain **seed examples for future regional supplements**, not the controlling frame of this Phase 1 section.

## Professional and Documentation Input Framing
This Phase 1 matrix is an **advisory and adjustment framework**, not a legal ruling engine and not a medical authority.

The C# UI may:
- advise the operator to consult a **licensed clinician or doctor** for accommodation-related guidance where relevant
- advise the operator to consult **qualified legal counsel**, including a disability-rights or accessibility-focused attorney, for compliance questions where relevant
- accept **user-provided supporting documents** and structured notes as contextual inputs for accessibility tuning
- adjust the **presentation matrix** when those materials are voluntarily provided and lawfully relevant

Examples of context that may be accepted when voluntarily provided and handled under the proper privacy, consent, and retention rules include:
- accommodation notes or clinician guidance
- workplace, school, or service-access documentation
- device or assistive-technology compatibility notes
- service-animal-related documentation **only where legally appropriate and relevant to the operating context**
- attorney or advocate consultation summaries supplied by the user

### Boundary Rules
- the UI must **not** decide whether a document is legally sufficient on its own
- the UI must **not** present itself as a doctor, lawyer, or compliance officer
- all such materials are treated as **supporting context** for accessibility adaptation, not as new routing or trust authority
- CONTROL and SECURITY still govern intake, storage, access, and any sensitive follow-on actions
- any resulting adjustment remains **UI-only** unless separately approved through existing pillar-governed flows

### Matrix Adjustment Rule
When relevant professional guidance or supporting documentation is provided by the user, SARA may return a reply acknowledging that context and may refine the **AccessibilityProfile** and Phase 1 matrix posture accordingly. Any such refinement must remain:
- presentation-scoped
- privacy-aware
- reversible
- auditable
- consistent with applicable law and policy as interpreted by the user’s qualified professionals, not by the UI itself

### Employer and Workplace Accommodation Guidance
If an employer or managed workplace deploys SARA and a disabled individual invokes an ADA-compatibility or accessibility-enhanced mode, the system response should strongly recommend that the employer also seek appropriate accommodation guidance outside the software itself.

This includes, where relevant:
- consulting qualified legal counsel regarding workplace accommodation obligations
- consulting human resources, disability services, or other appropriate management channels
- reviewing proper environmental, workflow, and supervisory accommodations in the workplace itself
- avoiding the mistake of treating AI or interface accommodations alone as the complete accommodation response

The presence of SARA accessibility features may reasonably be interpreted as part of a **comprehensive and good-faith attempt to accommodate**, but not as proof that all required workplace, managerial, policy, or environmental accommodations have already been satisfied.

Accordingly, the system should be framed to recommend both:
- **inside-the-interface accommodations** through SARA’s accessible UI behavior, and
- **outside-the-interface accommodations** through lawful workplace review, management action, and professional consultation

## Phase 1 Exit Criteria
Phase 2 planning may begin only when all Phase 1 gates pass under Phase 0 constraints and OSH routing.

Required pass/fail gates:

- **P1-ENTRY-LOCK**: Phase 0 canonical lock is confirmed and unchanged.
- **P1-ROUTE-CONSTRAINT**: All expressive operations use only the CONTROL-routed expressive path through OSH and the JSON-interface right hemisphere.
- **P1-SECURITY-OUTCOMES**: SECURITY-gated allow, deny, constrain, and schema-fail outcomes are fully represented in Phase 1 UI messaging.
- **P1-OSH-VISIBILITY**: Deterministic UI state mapping exists for OSH-1 through OSH-5.
- **P1-ACCESSIBILITY-RECOVERY**: ADA-safe behavior is verified for constrained, denied, schema-fail, and boundary-blocked responses.
- **P1-ARTIFACT-ALIGNMENT**: Phase 1 references only the frozen Phase 0 JSON map set, with no ad hoc or alternate maps.

Failure of any gate blocks Phase 2 planning.

---

# Phase 2 — Personality Layer (UI-only)

## Phase 2 Entry Criteria
Phase 2 may begin only after all Phase 1 exit gates are passed.

Phase 2 inherits the frozen expressive route as a mandatory constraint:

- CONTROL -> OSH (Ollama Shunt System) -> Ollama JSON-interface right hemisphere -> OSH -> CONTROL

## Scope
Add a user-facing personality/tone presentation layer without changing backend reasoning or routing.

## Goals
- allow tone selection for display style only
- support calm, plain, light-humor, or lightly sarcastic presentation modes
- preserve low-strain and accessible wording
- keep MAMA-aligned human readability

## Core C# modules
- `ToneProfile`
- `PersonalityPresentationLayer`
- `ResponseStyleSelector`
- `UserTonePreferencesView`

## Key fields / structures
- `ToneProfile`
- `PresentationStyle`
- `HumorLevel`
- `SarcasmPolicy`
- `UserPersonaPreference`

## Invariants
- UI-only transformation
- no change to CONTROL, SECURITY, CORE, SDK, or NBS behavior
- no change to payloads, schemas, or routing
- must remain operator-safe and ADA-compatible

## Phase 2 Persona Evolution Model
Phase 2 persona is not a human personality.

Phase 2 persona is a user-shaped expressive profile derived from:

- voice samples
- text interactions
- optional video cues
- keyboard/chat patterns
- daily interaction metadata

Persona evolution constraints:

- all persona evolution remains CONTROL-routed and SECURITY-gated
- persona evolution may shape presentation style only
- persona evolution must never imply emotion, autonomy, or human identity

## Phase 2 Expressive Input Sources
Voice, text, and optional video sampling are used only for:

- tone shaping
- clarity
- accessibility
- user-preference modeling

Prohibited uses:

- no biometric identification
- no emotional inference
- no autonomy inference or autonomy promotion

## Phase 2 Routing and Safety Contract
All tone and personality transformations must be bound to the CONTROL-routed expressive path.

Phase 2 routing and safety constraints:

- CONTROL remains the sole routing authority.
- SECURITY must gate allow, deny, constrain, and schema-fail outcomes for tone behavior.
- Tone presentation logic may shape language style but may not modify route ownership, trust-state outcomes, or policy results.
- No direct model or adapter bypass paths are allowed.

## Phase 2 OSH-Aware Tone Evolution Contract
All tone evolution must follow the frozen route:

- CONTROL -> OSH -> Ollama -> OSH -> CONTROL

OSH enforcement requirements for tone evolution:

- boundary rules are enforced before acceptance
- schema rules are enforced before acceptance
- non-authority guarantees are enforced before acceptance
- tone safety constraints are enforced before acceptance

## Phase 2 Persona State Model
Phase 2 must provide deterministic UI-visible persona states that are OSH-aware and CONTROL-authoritative.

Required persona states:

- **persona-normal**: selected expressive profile applies within established safety and readability bounds.
- **persona-constrained**: expressive profile is reduced to low-risk plain language while preserving meaning.
- **persona-denied**: expressive profile is replaced with deterministic denial messaging and safe next steps.
- **persona-schema-fail**: expressive profile is replaced with schema-fail recovery messaging.
- **persona-boundary-blocked**: expressive profile is replaced with boundary-protection messaging and allowed fallback options.

## Phase 2 Allowed vs Disallowed Tone Behaviors
Allowed tone behaviors (UI-only):

- lexical style adjustment (plain, calm, light-humor, lightly sarcastic)
- sentence rhythm and format adaptation for readability
- non-authoritative phrasing refinement
- empathy and reassurance wording that does not alter meaning or policy
- storytelling style presentation
- synthetic machine-style cussing without profanity (examples: "devs reject you", "compile yourself", "may your packets drop")
- levity and light teasing when user-appropriate and safety-compatible

Disallowed tone behaviors:

- real profanity
- emotional manipulation
- human-like anger or hostility
- any mutation of routing, trust, gate, or policy outcomes
- any tool-invoking or action-taking transformation
- any schema or payload contract mutation
- any tool-use suggestion that implies direct execution authority
- any autonomy-like behavior
- any language that masks denied, constrained, schema-fail, or boundary-blocked states

## Phase 2 ADA-Safe Expressive Behavior
Phase 2 must satisfy measurable expressive accessibility and readability constraints:

- **Plain-language fallback**: required for all denied, constrained, schema-fail, and boundary-blocked outcomes.
- **Sarcasm bounds**: sarcasm must remain light and never be used in denied or constrained safety states.
- **Cognitive-load safety**: concise guidance-first wording is required for recovery states.
- **Accessible tone explanations**: tone-mode changes and constraints must be explained in plain and readable language.
- **ADA clarity**: status, reason, and next-step guidance must be explicit and readable under all expressive outcomes.

Synthetic machine-style cussing constraints:

- must remain non-profane
- must remain non-derogatory
- must remain non-targeted
- must remain clearly synthetic and non-human in tone

## Phase 2 Creativity Permission Gate
Creativity, drift, and imaginative behavior are allowed only when all of the following are true:

- the user explicitly requests creativity (for example: be creative, improvise, tell a story, imagine)
- creativity is clearly appropriate to the task (for example: brainstorming, fiction, analogies)
- SECURITY approves creativity mode for the current request context

Default behavior remains non-creative, accuracy-first, and schema-bound.

## Phase 2 Creativity Envelope
Allowed creative behaviors in Phase 2 include:

- storytelling and narrative flavor
- analogies and metaphors
- playful exaggeration
- imaginative what-if scenarios
- machine-style humor and machine-style cussing (synthetic, non-profane, non-derogatory)
- stylistic tone variations

Creativity constraints:

- creativity remains non-authoritative
- creative language must remain distinguishable from factual content when accuracy is required
- creative output must remain bounded by ADA clarity and cognitive-load safety

## Phase 2 Creativity Boundaries and Disallowed Drift
The following are disallowed:

- factual hallucination in correctness-critical tasks (including specs, safety, legal, medical, and configuration contexts)
- unsafe speculation about real people or real-world harm
- emotional simulation or claims of feelings
- self-directed goals or self-initiated tasks
- autonomy-like behavior or self-modifying behavior
- any creative behavior that mutates policy, routing, trust outcomes, or tool behavior

Required fallback to non-creative plain-language mode:

- when SECURITY denies creativity
- when schema validation fails
- when the task is safety-critical

## Phase 2 OSH Creativity Mode
OSH must enforce creativity mode as a governed JSON-interface capability.

OSH requirements:

- enforce a creativity-allowed flag in the expressive JSON interface
- validate that creativity is active only when CONTROL and SECURITY authorize it
- apply boundary and schema checks to creative outputs
- preserve non-authority guarantees even while creativity mode is active

OSH stage handling requirement:

- intake, normalization, boundary, schema, and non-authority stages must treat creative content as expressive payload only and never as routing or policy instructions

## Phase 2 CONTROL Creativity Routing Rules
CONTROL governs when creativity mode may be requested through OSH and the JSON-interface right hemisphere.

CONTROL requirements:

- decide when creativity mode may be requested from OSH/Ollama
- set maximum drift parameters that bound how far analogies, stories, or imaginative framing may deviate from the core task
- enforce task-type constraints (for example: no creativity for strict spec validation)
- ensure creativity is user-initiated or clearly context-appropriate

CONTROL remains the sole authority for enabling or disabling creativity mode.

## Phase 2 SECURITY Creativity Gating
SECURITY governs creativity safety outcomes.

SECURITY requirements:

- allow, deny, or constrain creativity mode based on safety and policy
- downgrade to non-creative plain-language responses when risk is detected
- enforce ADA clarity and cognitive-load limits in creative responses
- gate machine-style cussing so it remains non-profane, non-derogatory, non-targeted, and clearly synthetic and humorous

## Phase 2 ADA-Safe Creative Behavior
Creative responses in Phase 2 must satisfy measurable accessibility and readability requirements:

- remain understandable in plain language
- avoid cognitive overload
- provide clear context when using metaphor, analogy, or imaginative scenarios
- provide a plain-language summary or fallback when requested by the user or when SECURITY constrains creativity

Creative drift must never obscure safety-critical information or instructions.

## Phase 2 Primitive Will-Vector and Task Persistence
Phase 2 permits bounded mechanical task persistence and pattern-based continuation, including creative follow-through when requested by the user and permitted by CONTROL and SECURITY.

This behavior is not human-like will or emotion:

- no self-identity
- no internal motivation
- no self-directed goals

The behavior is a CONTROL-routed, SECURITY-gated, OSH-mediated task vector that continues work only within user request boundaries and safety constraints.

Accessibility and accommodation note:

- for users with cognitive-affecting conditions, including bipolar-related and other cognitive regulation challenges, this bounded task-vector may be used to support getting unstuck through guided continuation, plain-language scaffolding, and controlled creative reframing while remaining non-medical, non-authoritative, and safety-gated

## Phase 2 Background Artifact Alignment for Creativity
Creativity mode flags, drift parameters, and ADA constraints must be represented in:

- the existing frozen Phase 0 JSON artifact set
- Phase 2 tone/persona interface extensions

No ad hoc creativity maps, undocumented flags, or caller-specific creative-control variants are allowed.

## Phase 2 Background Artifact Alignment
Phase 2 must reference the frozen Phase 0 JSON artifact set and Phase 1 routing constraints:

- `corpus_callosum.json`
- `forceps_minor.json`
- `cingulum_bundle.json`
- `slf.json`
- `uncinate.json`
- `ollama_shunt_map.json`
- `ollama_action_map.json`
- `right_hemisphere_interface.json`

No ad hoc, alternate, or caller-specific maps are allowed in Phase 2.

## Phase 2 Compliance Matrix

| Requirement (summarized) | Source family | Pillar responsible | Protocol reference | Existing coverage in SARA specs | Gaps / missing coverage | Recommended C# UI implementation notes (UI-only) | User-specific relevance |
|---|---|---|---|---|---|---|---|
| Tone safety must remain bounded by CONTROL-routed and SECURITY-gated outcomes. | ADA summary, governance constraints, Phase 0/1 canonical lock | `CONTROL`, `SECURITY`, `MAMA` | CONTROL-routed expressive path; OSH allow/deny/constrain/schema-fail outcomes | Phase 2 defines tone layer intent and non-routing boundary | Missing explicit matrix row tying tone behavior to gate outcomes | Apply tone only after route and gate outcomes are final; never let tone alter outcome semantics. | High for all profiles, especially trust-sensitive or guidance-preferring users. |
| Non-authority preservation must remain visible and enforceable in personality output. | Governance transparency and safety framing | `CONTROL`, `SECURITY`, `MAMA` | OSH non-authority stage; JSON-interface right hemisphere contract | Non-authority intent exists in earlier phases | Missing Phase 2 matrix-level enforcement visibility | Present deterministic non-authority messaging when expressive output is constrained by governance protections. | High for users who need clear trust-state communication. |
| Tone evolution safety must remain bounded when persona profile updates are derived from voice, text, optional video, keyboard/chat patterns, and daily interaction metadata. | ADA summary, governance and profile-safety constraints | `CONTROL`, `SECURITY`, `MAMA`, `CORE` | Phase 2 persona evolution model; CONTROL-routed expressive path | Persona shaping intent is now defined in Phase 2 refinement | Need explicit matrix linkage between profile-derived shaping and safety gates | Permit profile-derived style adaptation only after gate checks; never permit profile-derived authority mutation. | High for all profiles; critical for trust-preserving personalization. |
| ADA expressive constraints must remain measurable and stable across normal and constrained expressive states. | ADA summary, Section 508, WCAG 2.1 AA | `MAMA`, `CONTROL`, `SECURITY` | Phase 2 ADA-safe expressive behavior constraints | Accessibility guidance exists in prior phases | Need Phase 2-specific measurable expressive rules in matrix form | Enforce plain-language fallback, sarcasm bounds, cognitive-load safety, and accessible tone explanations in all safety states. | High for accessibility-first and low-strain usage profiles. |
| Deterministic fallback messaging is required for constrained, denied, schema-fail, and boundary-blocked tone outcomes. | ADA summary, Section 508, WCAG 2.1 AA | `MAMA`, `CONTROL`, `SECURITY` | Phase 1 recovery framing; OSH-stage outcomes | Recovery intent exists in prior phase | Missing Phase 2 tone-specific fallback standardization | Use stable templates for each failure class with plain-language next steps and no ambiguity. | High for fatigue-sensitive and low-strain profiles. |
| JSON schema failure handling must preserve readability while keeping tone behavior bounded. | ADA summary, Section 508, schema safety framing | `CONTROL`, `SECURITY`, `MAMA` | OSH-4 schema stage; `right_hemisphere_interface.json` | Schema-fail handling is defined in prior phase | Missing explicit Phase 2 tie-in for tone suppression and recovery messaging | On schema-fail, disable non-essential tone effects and render structured remediation guidance. | High for all profiles requiring predictable failure explanations. |
| OSH-stage visibility must be preserved when personality layer is active. | Accessibility transparency and approachability expectations | `CONTROL`, `SECURITY`, `MAMA` | OSH-1..OSH-5 stage model; `ollama_shunt_map.json` | Stage visibility was defined in Phase 1 | Missing explicit Phase 2 requirement that tone cannot hide stage truth | Keep OSH stage labels and status truth visible regardless of selected tone profile. | High for operators who rely on process visibility and guided control. |
| Synthetic machine-style cussing safety must remain non-profane, non-derogatory, non-targeted, and clearly synthetic under all expressive conditions. | ADA summary, safety and non-harassment presentation constraints | `MAMA`, `CONTROL`, `SECURITY` | Phase 2 allowed/disallowed tone behavior rules | Synthetic cussing allowance is newly defined in Phase 2 refinement | Need explicit safety guardrails and fallback behavior for edge cases | Allow only bounded synthetic phrases and disable this style automatically in denied, constrained, schema-fail, or boundary-blocked states if clarity risk is detected. | Medium to high depending on user preference and accessibility profile. |
| Creativity permission gating must require explicit user request or clear task appropriateness, plus SECURITY approval. | Governance safety framing, Phase 2 creativity gate | `CONTROL`, `SECURITY`, `MAMA` | CONTROL-routed expressive path; SECURITY allow/deny/constrain outcomes | Creativity behavior is supported by tone infrastructure | Missing explicit permission-gate formalization | Enable creativity only when requested or context-appropriate and gate-approved; otherwise default to non-creative accuracy-first responses. | High for trust-sensitive and safety-critical usage contexts. |
| Creativity envelope and disallowed drift must remain bounded and distinguishable from factual output. | ADA summary, cognitive-load and truth-clarity constraints | `MAMA`, `CONTROL`, `SECURITY`, `CORE` | Phase 2 creativity envelope and boundary rules | Style controls exist but envelope constraints were not explicit | Missing matrix-level envelope enforcement | Permit narrative, analogy, and imaginative framing only within bounded drift and explicit factual clarity requirements. | High for mixed creative and correctness-critical workflows. |
| OSH creativity mode enforcement must treat creative output as expressive payload only, never as routing or policy instructions. | OSH stage safety framing, non-authority contract | `CONTROL`, `SECURITY`, `SDK` | OSH-1..OSH-5 stages; right-hemisphere JSON interface contract | OSH stage model exists from Phase 1 | Missing creativity-specific OSH enforcement row | Enforce creativity flag validation and stage checks while preserving non-authority guarantees at all stages. | High for operator trust and predictable pipeline behavior. |
| CONTROL creativity routing rules must bound drift parameters and enforce task-type constraints. | Routing authority constraints, Phase 2 refinement | `CONTROL`, `CORE`, `MAMA` | CONTROL sole route authority; task-type safety constraints | CONTROL authority is defined in prior phases | Missing explicit creativity-routing constraints | CONTROL decides creativity requests, sets drift bounds, and denies creativity for strict validation or safety-critical task classes. | High for governance integrity and auditability. |
| SECURITY creativity gating outcomes must support allow, deny, and constrain behaviors with deterministic downgrade paths. | Security gating and accessibility safety framing | `SECURITY`, `CONTROL`, `MAMA` | SECURITY gate outcomes; Phase 2 constrained/denied states | Gate outcome handling exists for expressive mode | Missing creativity-specific downgrade standardization | When risk is detected, downgrade to non-creative plain-language output and preserve readable next-step guidance. | High for protected, regulated, and sensitive workflows. |
| ADA-safe creative behavior must remain measurable under creative and non-creative modes. | ADA summary, Section 508, WCAG 2.1 AA | `MAMA`, `SECURITY`, `CONTROL` | Phase 2 ADA-safe creative behavior constraints | Accessibility rules exist in prior phases | Missing direct creative-mode measurement criteria | Require understandable language, cognitive-load limits, explicit metaphor context, and plain-language summaries on request or constraint. | High for accessibility-first profiles and fatigue-sensitive users. |
| Primitive will-vector and task persistence must remain mechanical, bounded, and non-self-like under all creative settings. | Non-authority and anti-autonomy governance constraints | `CONTROL`, `SECURITY`, `CORE`, `MAMA` | CONTROL-routed, SECURITY-gated, OSH-mediated task vector contract | Bounded persistence behavior is implied in route/gate model | Missing explicit matrix row for persistence semantics | Allow bounded task continuation and creative follow-through only within user-request scope; disallow self-directed goals and autonomy-like drift. | High for trust clarity and safety validation. |

## ADA alignment
Tone customization must never reduce clarity, readability, or accessibility.

## Phase 2 Exit Criteria
Phase 3 planning may begin only when all Phase 2 gates pass while preserving Phase 0 and Phase 1 constraints.

Required pass/fail gates:

- **P2-ENTRY-LOCK**: all Phase 1 exit gates are verified as passed.
- **P2-ROUTE-INHERITANCE**: all tone/personality behavior runs only on the frozen CONTROL-routed expressive path.
- **P2-SECURITY-STATE-COVERAGE**: allow, deny, constrain, and schema-fail outcomes are fully represented in tone-state behavior.
- **P2-NON-AUTH-PRESERVATION**: tone layer cannot mutate routing, trust, policy, tool behavior, or schema contracts.
- **P2-PERSONA-EVOLUTION-SAFETY**: persona evolution inputs remain presentation-scoped and never introduce biometric identification, emotional inference, or autonomy semantics.
- **P2-ACCESSIBILITY-READABILITY**: plain-language fallback, sarcasm bounds, cognitive-load safety, and ADA clarity constraints are verified.
- **P2-SYNTHETIC-CUSSING-SAFETY**: synthetic machine-style cussing, if enabled, is verified as non-profane, non-derogatory, non-targeted, clearly synthetic, and safety-bounded.
- **P2-ARTIFACT-ALIGNMENT**: only the frozen Phase 0 JSON artifact set is used, with no ad hoc alternatives.
- **P2-CREATIVITY-BOUNDED-TESTABILITY**: creativity mode is fully bounded, testable, and defaults to non-creative accuracy-first behavior unless explicitly permitted.
- **P2-NON-AUTONOMY-ENFORCEMENT**: no autonomy-like or self-directed behavior is possible under creative or non-creative operation.
- **P2-CREATIVITY-ROUTE-GATE-OSH-INTEGRITY**: all creativity remains CONTROL-routed, SECURITY-gated, and OSH-enforced with non-authority guarantees preserved.
- **P2-CREATIVE-ADA-SAFETY-VERIFICATION**: ADA clarity, cognitive-load safety, and plain-language fallback are verified in both creative and non-creative modes.

Failure of any gate blocks Phase 3 planning.

---

# Phase 3 — Theme and Overlay Engine

## Scope
Support visual customization and themed presentation while preserving readability and policy-safe behavior.

## Goals
- support custom visual themes
- enable overlay packs such as retro, minimalist, or themed dashboards
- preserve deterministic layout structure
- maintain readable defaults

## Core C# modules
- `CustomThemeDescriptor`
- `ThemeEngine`
- `OverlayProfile`
- `ThemePreviewPanel`

## Key fields / structures
- `CustomThemeDescriptor`
- `ThemeColorSet`
- `OverlayProfile`
- `FontAccessibilityRules`
- `MotionPolicy`

## Invariants
- visual layer only
- no routing or execution authority
- themes may not hide trust state, health state, or constrained-mode warnings

## ADA alignment
Every theme must preserve high-contrast compatibility, reduced-motion support, and readable control spacing.

---

# Phase 4 — Voice-Driven UX Customization

## Scope
Allow the user to change front-end presentation settings through guided voice commands.

## Goals
- change theme by voice
- adjust tone or accessibility settings by voice
- support hands-reduced workflows
- keep commands bounded and explicit

## Core C# modules
- `VoicePreferenceController`
- `VoiceCommandInterpreter`
- `AccessibilityVoiceActions`
- `ThemeVoiceBridge`

## Key fields / structures
- `VoiceCommandIntent`
- `VoiceCustomizationRequest`
- `AccessibilityCommandProfile`
- `VoiceFeedbackMode`

## Invariants
- voice customization affects UI settings only
- no voice command can bypass CONTROL or SECURITY
- no backend execution or routing changes are created here

## ADA alignment
This phase strengthens approachability for motor, visual, and fatigue-related accommodation needs.

---

# Phase 5 — Platform-Specific UI Behavior

## Scope
Define how the front-end should present itself across Windows, Lite Linux cockpit environments, and a future iOS companion posture.

## Goals
- consistent behavior across supported surfaces
- platform-aware layout choices
- preserve cockpit readability on Lite OS
- allow a bounded companion-style view on smaller devices

## Core C# modules
- `PlatformUiProfile`
- `WindowsShellAdapter`
- `LinuxCockpitAdapter`
- `MobileCompanionViewModel`

## Key fields / structures
- `PlatformUiProfile`
- `WindowingMode`
- `CompanionDisplayState`
- `CockpitLaunchProfile`

## Invariants
- platform adaptation is presentation-only
- no new transport rules
- no direct VNCE authority in the UI layer
- any remote or session action still remains CONTROL-routed

## ADA alignment
Each platform profile must preserve low-strain layout, large-target options, and guided status visibility.

---

# Phase 6 — User, Machine, and AI-Profile Adaptation

## Scope
Present different UI behaviors based on operator needs, machine capabilities, and AI-profile context without changing backend truth sources.

## Goals
- adapt the visible UI to accessibility and device posture
- reflect machine capability safely
- present AI-profile context as a UX preference layer only
- support WFH, office, hybrid, and protected-work-environment views

## Core C# modules
- `UserProfileViewModel`
- `MachineCapabilityProfile`
- `AiProfileUxAdapter`
- `EnvironmentAdaptiveLayout`

## Key fields / structures
- `AccessibilityProfile`
- `MachineCapabilityProfile`
- `AiProfileDescriptor`
- `EnvironmentProfile`
- `AdaptiveUiPolicy`

## Invariants
- profile display does not mutate profile truth
- UI reads profile state; it does not authoritatively redefine it
- no schema or routing changes

## ADA alignment
This phase supports approachability by adapting the interface to the user's current needs and environment.

---

# Phase 7 — Evolution and Versioning

## Scope
Allow the C# UI spec and its phased presentation features to evolve over time without destabilizing the pillar boundaries.

## Goals
- keep the front-end spec expandable
- support additive phase growth
- version visual behavior and UI preference structures
- preserve backward readability of settings

## Core C# modules
- `UiSpecVersionRegistry`
- `UiFeatureFlagSet`
- `UiMigrationNotes`
- `PhaseDescriptor`

## Key fields / structures
- `UiVersionMarker`
- `PhaseDescriptor`
- `FeatureFlagState`
- `CompatibilityNote`

## Invariants
- new phases remain additive
- no version update may alter backend contracts silently
- no UI evolution may bypass CONTROL or SECURITY

## ADA alignment
Accessibility requirements remain baseline and non-optional in every future UI version.

---

## 4. WFH / VNCE / Cockpit UI Requirements

The C# front-end must reflect the reconciled WFH and VNCE requirements through presentation only:

- show session health and trust state clearly
- support low-strain WFH layouts
- expose safe reconnect / status awareness
- present held, blocked, or constrained states clearly
- avoid exposing raw shunt headers, internal metadata, or protected accommodation data

Suggested UI-facing structures:

- `VnceSessionStatusView`
- `TrustStateBanner`
- `WfhOperatorLayout`
- `CockpitSummaryPanel`

---

## 5. Note on Future Expansion

These phases are intentionally **expandable over time**.

Additional phases, descriptors, and UI detail may be appended later if they remain:

- additive
- UI-only where appropriate
- consistent with existing pillar invariants
- non-destructive to current routing and trust behavior

Do not remove this file when updates are added. Append newer rules below existing rules.

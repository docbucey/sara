# SARA Gen0.5a Specification Sheet — 3LM Architecture

---

## 1. Overview

**Purpose of SARA Gen0.5a:**  
SARA Gen0.5a is designed as an OS-native plugin and cockpit orchestrator, integrating directly with the host operating system (e.g., Windows, Linux, macOS) and its native plugin/app extension surfaces. The 3LM (three-point language model) layer maximizes modularity, accessibility, and adaptive intelligence, sitting above the five fixed SARA pillars and orchestrating all generative, adaptive, and hardware-integrated behavior without modifying pillar logic. SARA is not an LLM or monolithic AI; it is a deterministic, plugin-driven, and hardware-integrated system, with the OS as the primary host and authority.

**The 3-Profile System:**  
- **Human Profile:** Manages user context, ADA (accessibility), and interaction pacing.
- **AI Profile:** Handles reasoning, continuity, and adaptive learning.
- **Machine Profile:** Interfaces with hardware, tools, and plugins.

**The 3LM (Three-Point Language Model):**  
- **SLM‑1 (AI Profile):** The reasoning engine, responsible for generative intelligence, adaptation, and continuity.
- **SLM‑2 (Machine Profile):** The environment/tool engine, responsible for deterministic, hardware, and plugin operations.
- **SLM‑3 (Human Profile):** The ADA/interaction engine, responsible for user context, accessibility, and input shaping.

---

## 2. Pillar Reference (read-only)

**CONTROL:**  
- Governance, routing, and shunt entrypoints.
- Referenced functions (from sara_controlgen1.functionmap.json):  
  - `control_shunt_entrypoint`
  - `route_command`
  - `validate_profile`
  - `authorize_map`
  - `reject_action`
  - `validate_shunt_header`
  - `update_core_profile_with_ai_config`
  - `SARA_AIBackend.register_backend`
  - `SARA_AIBackend.ask`

**CORE:**  
- Identity, profile loading, and state validation.
- Referenced functions (from sara_coregen1.functionmap.json):  
  - `core_shunt_entrypoint`
  - `build_vnce_shunt_envelope`
  - `load_identity`
  - `load_config`
  - `validate_state`
  - `noop_action`
  - `validate_shunt_header`
  - `read_image_file`
  - `write_image_file`
  - `resize_image_file`
  - `read_video_file`
  - `read_audio_file`
  - `read_3d_file`
  - `read_graphics_asset_file`

**MAMA:**  
- ADA interface and cockpit interaction patterns.
- Referenced functions (from sara_mamagen1.functionmap.json):  
  - `mama_shunt_entrypoint`
  - `snapshot`
  - `diff`
  - `persist`
  - `validate_shunt_header`
  - `MamaDispatcher.dispatch`
  - Clerk protocol endpoints (intake, records, routing, status, etc.)

**SECURITY:**  
- Policy enforcement.
- Referenced functions (from sara_securitygen1.functionmap.json):  
  - `security_shunt_entrypoint`
  - `audit_gate`
  - `quarantine`
  - `scan`
  - `validate_shunt_header`

**SDK:**  
- Plugin, app, and hardware mapping surface. The SDK pillar exposes deterministic plugin registration, device mapping, and app extension points for:
  - Hardware devices (flight controls, gaming mice/keyboards, AR glasses, EEG, cameras, audio devices, etc.)
  - App plugins (Office, VS Code, Blender, etc.)
  - OS-native extension points (input overlays, accessibility, macro/micro/batchOS, etc.)
Referenced functions (from sara_sdkgen1.functionmap.json):  
  - `dispatch_sdk_protocol`
  - `device_protocol`
  - `arms_protocol`
  - `server_protocol`
  - `ide_protocol`
  - `SaraSdkGen1.dispatch`
  - `SaraSdkGen1.dispatch_amipi`

---

## 3. 3LM Architecture

---

## 3A. Pillar Responsibilities and SLM Delegation (Canonical Map Reference)

All improvements, adaptive logic, and migration paths in SARA are strictly governed by the canonical pillar JSON function maps. Each pillar’s authority, responsibilities, and SLM delegation are as follows:

**CONTROL Pillar**  
Source: sara_controlgen1.functionmap.json  
- Governance, routing, and authority (e.g., `control_shunt_entrypoint`, `route_command`, `validate_shunt_header`).
- All migration, autonomy, or adaptive delegation is validated, logged, and reversible by CONTROL.
- CONTROL is the final authority—no SLM or adaptive logic can bypass it.

**CORE Pillar**  
Source: sara_coregen1.functionmap.json  
- Identity, state, and profile management (e.g., `core_shunt_entrypoint`, `load_identity`, `validate_state`).
- SLMs may suggest changes, but CORE validates and applies all state/profile updates.

**MAMA Pillar**  
Source: sara_mamagen1.functionmap.json  
- ADA, cockpit, and interface logic (e.g., `mama_shunt_entrypoint`, `snapshot`, `persist`).
- SLM-3 may adapt or shape input, but MAMA enforces ADA/cockpit rules.

**SECURITY Pillar**  
Source: sara_securitygen1.functionmap.json  
- Policy, audit, and enforcement (e.g., `security_shunt_entrypoint`, `audit_gate`, `scan`).
- No adaptive logic can override security checks.

**SDK Pillar**  
Source: sara_sdkgen1.functionmap.json  
- Hardware, plugin, and app integrations (e.g., `device_protocol`, `arms_protocol`, `server_protocol`).
- SLM-2 may request/adapt device or app usage, but SDK enforces mapping and compatibility.

**MamaLedger Logging**
- All changes, migrations, and autonomy events are logged in MamaLedger.
- CONTROL can always revert or override any delegated or adaptive action.

This structure ensures SARA remains deterministic, auditable, and pillar-driven. No SLM or generative/adaptive logic can replace or bypass pillar authority. All improvements and autonomy are layered on top of, not in place of, the canonical pillar logic.

**SLM‑1 (AI Profile) Responsibilities:**  
- Generative reasoning, adaptation, and continuity.
- Consumes NBS memory and learning outputs.
- Interfaces with CONTROL for governance and policy.

**SLM‑2 (Machine Profile) Responsibilities:**  
- Executes deterministic, environment-specific, and hardware/plugin tasks.
- Consumes SDK plugin, app, and hardware mapping surfaces.
- Interfaces with CORE for state and device operations.
- Manages all hardware and app plugin integrations, including:
  - Thrustmaster HOTAS, Corsair/Logitech/HyperX input devices, XREAL AR glasses, Muse EEG, cameras, audio devices
  - App plugins for Office, VS Code, Blender, and other supported applications
  - OS-native plugin/extension points for input, accessibility, and automation

**SLM‑3 (Human Profile) Responsibilities:**  
- Shapes user context, ADA, and accessibility.
- Consumes MAMA ADA interface and cockpit patterns.
- Manages input pacing and user session state.

**CONTROL Orchestration of 3LM:**  
- All SLMs are routed and governed by CONTROL’s shunt entrypoints and validation.
- CONTROL enforces policy, authorization, and safe routing.

**NBS and Learning Feeding SLM‑1:**  
- SLM‑1 leverages NBS memory functions and LearnManager for adaptive behavior and continuity.

**SDK Feeding SLM‑2:**  
- SLM‑2 receives plugin and hardware requests via SDK’s deterministic dispatch surfaces.

**MAMA Feeding SLM‑3:**  
- SLM‑3 receives user context, ADA, and accessibility signals via MAMA’s cockpit and protocol endpoints.

---

## 4. Cockpit Integration Layer

**Monkey-in-the-Middle Orchestrator:**  
- Central routing layer that directs requests to the appropriate SLM based on context and task type.

**Routing Rules:**  
- **SLM‑1:** Handles reasoning, adaptation, and generative tasks.
- **SLM‑2:** Handles tools, plugins, and hardware operations.
- **SLM‑3:** Handles ADA shaping, user context, and accessibility.

**Hardware Mapping Placeholders:**  
- SDK device_protocol, arms_protocol, server_protocol, ide_protocol.

**Virtual Keyboard + Accessibility Input Layer:**  
- Sits above MAMA and SDK, providing atomic input signals and accessibility features for SLM‑3.

---

## 5. Progressive Input Model (micros → macros → batchOS)

**Adaptive Input Progression:**  
- **Micros:** Atomic signals (letters, numbers, blinks, taps, micro-utterances).
- **Macros:** Combined intent units (words, short commands, simple actions).
- **BatchOS:** High-level multi-step tasks (e.g., open app → load template → fill → export → send).

**Interpretation and Collaboration:**  
- **SLM‑3:** Interprets micros, shaping raw input into user intent.
- **SLM‑3 + SLM‑1:** Collaborate to interpret macros, combining user context with reasoning.
- **SLM‑1 + SLM‑2 + CONTROL:** Execute batchOS tasks, orchestrating high-level workflows across the system.

*Note: This section is a placeholder for future training and implementation detail.*

---

## 6. Compatibility With Older Specs

**Supersedes but Does Not Replace:**  
- This spec sheet (saragen0.5a.md) supersedes but does not replace:
  - SPEC_SHEET_GEN0_CSHARP_EXTENDED.md
  - SPEC_SHEET_GEN0_CSHARP.md

**Valid Concepts:**  
- Pillar separation, shunt entrypoints, plugin surfaces, and ADA interface patterns remain valid.

**Deprecated Concepts:**  
- Monolithic SLM routing, single-profile adaptation, and direct pillar modification are deprecated.

**Externalized Concepts:**  
- All generative, adaptive, and hardware integration logic is externalized into the 3LM layer and cockpit orchestrator.

---

## 7. Future Expansion Slots

- Gen1.0 cockpit hardware integration
- Adaptive ADA modules and accessibility enhancements
- Plugin ecosystem for third-party and custom tools
- Multi-device and distributed hardware mapping
- Higher-level learning and meta-adaptation layers

---

## 8. SARA Parsing & Context Handling (Beyond RAG/VS Code Limits)

SARA’s parsing, data handling, and orchestration are not limited by the typical truncation or context window constraints found in standard VS Code plugins or LLM-based tools. Instead, SARA leverages its pillar-driven, CONTROL-governed 3LM architecture to:

- Parse, route, and correlate data across multiple files, plugins, and devices with continuity and auditability.
- Maintain adaptive, multi-session context and state, even as users switch tools or environments.
- Provide richer, more accurate, and context-aware operations than RAG or single-context systems.
- Enable comprehensive orchestration and adaptive workflows, governed by deterministic pillar logic and the cockpit/orchestrator layer.

**Result:**
Once fully built, SARA as a VS Code plugin (or in any host environment) will deliver advanced, pillar-driven parsing and orchestration that far exceeds the limitations of conventional plugin architectures or retrieval-augmented generation (RAG) systems.

---

## 9. Night Shift Mode (AFK/Automation Mode)

**Night Shift Mode (AFK/Automation Mode)** is designed to maximize user productivity and accessibility, especially for work-from-home and disabled users. When enabled, Night Shift Mode:
- Automates repetitive and tedious tasks, dramatically reducing manual workload.
- Allows a single user to accomplish up to 100x more work per day by leveraging background automation and intelligent task batching.
- Minimizes the need for constant human intervention, letting users focus on high-value or creative tasks.
- Provides adaptive accessibility features, ensuring that even users with disabilities can benefit from automation and reduced tedium.
- Maintains full auditability, reversibility, and user control—humans remain in the loop for oversight, but not for every step.

This mode is a core part of SARA’s mission to make advanced automation accessible, user-friendly, and empowering for all users, regardless of ability or work environment.

**Integration Points:**
- **MAMA Pillar:** Detects AFK/user state, manages ADA overlays, and triggers accessibility adjustments.
- **SDK Pillar:** Initiates or manages automation protocols, device state changes, and plugin/app background tasks.
- **CONTROL Pillar:** Governs transitions, ensures policy compliance, and logs all mode changes in MamaLedger.
- **SLM-3:** Shapes user context and accessibility during Night Shift Mode.
- **SLM-2:** Executes automation and background tasks as requested or scheduled.

**Implementation Guidance:**
- Night Shift Mode should be discoverable and configurable via the cockpit/orchestrator and exposed in the canonical function maps for MAMA and SDK pillars.
- All transitions and automation events are logged and reversible by CONTROL.

---

## 10. Baseline Data Collection via Games (Normals Dataset)

SARA-enabled games can be used to collect anonymized baseline activity data (“normals”) as users play. This dataset helps SARA evolve its ADA, calibration, and automation features for future users. The workflow is:
- As you (and later, users) play games, SARA captures input patterns, timing, choices, and accessibility needs.
- This data forms a “normals” dataset—representing typical user behavior and accessibility requirements.
- SARA uses these baselines to adapt gameplay, UI, and automation for new users, improving accessibility and personalization.
- All data collection is privacy-respecting, auditable, and user-controlled.

**Normals Dataset Definition:**
- “Normals” refers to baseline activity data collected from users without disabilities or disadvantages, representing typical user behavior and performance.
- SARA also collects HIPAA-level, privacy-respecting, averaged datasets from users with disabilities or accessibility needs (never storing or exposing explicit user identities or sensitive health data).
- Both datasets are used to train and evolve future forms of SARA, ensuring the system adapts to the needs of both typical and disabled users.
- All data collection is strictly anonymized, auditable, and user-controlled, with clear separation between normals and accessibility datasets.

**Initial Conditioning Plan:**
- You will actively use SARA to finish your WFH business plans (e.g., office workflows, medical billing, local AI tasks).
- This real-world usage will serve as SARA’s initial conditioning and training set.
- As you transition from Gen0 to Gen1, SARA will be ready for Gen2 (server-based gaming, broader distribution).
- Once the core is built, your focus can shift to UX and texture development, with SARA handling automation and adaptation.
# SARA Gen0 C# Project Spec Sheet

# Profile Types (Gen0)

# MamaLedger (Gen0)

## 1. Compliance Discovery & Adaptation Logic (Hard-Wired Spec)

### 1.1 Sovereign Search Logic
SARA is not pre-programmed with every law. Instead, she is programmed with logic to discover relevant compliance requirements based on the user's current situation.

**ADA Empowerment Function (C# Implementation):**
When triggered, this function executes a 3-step lookup:

**Step A: Geo-Lock**
- Identifies the user's state (e.g., Kentucky).

**Step B: Statutory Lookup**
- Searches for "[State Name] Accessible Information Technology Law."
  - Example: In Kentucky, pulls KRS 61.982, which mandates state-assisted organizations provide access equivalent to that for non-disabled individuals.

**Step C: Scope Expansion**
- Searches for the specific disability mentioned in the setup (e.g., "Learning Disabilities" or "Parkinson's") and cross-references with Federal Title I/III.

---

### 1.2 Broad-to-Narrow Adaptation (Setup Protocol)
Defines how SARA narrows broad ADA requirements into a custom interface during setup.

| Setup Phase   | SARA's Automated Research Task | Resulting Hard-Code Adaptation |
|--------------|-------------------------------|-------------------------------|
| Broad Entry  | "General ADA requirements for Learning Disabilities." | SARA enables Simplified UI Mode and Read-Aloud by default. |
| Specific Probe | "KRS 61.980 definitions for Assistive Technology in KY." | SARA classifies herself as a "protected aid," locking in your right to use her in a volunteer or work environment. |
| Narrow Fix   | "Accommodations for motor-control (Parkinson's) for keyboard use." | SARA activates Tremor Filtering (ignoring rapid repeat keystrokes). |

---

---

Host OS AI Integration (No Ollama Dependency)
SARA Gen0 is designed to run as part of the host operating system’s AI ecosystem (for example, on Windows via the Windows Copilot ecosystem and OS-native AI services). Any prior references to third-party local model runners are out of scope for the final C# build; model execution is treated as an OS-provided capability exposed through approved, host-OS interfaces.
Three SLMs (Automation Roles + ADA Compliance & Empowerment)
•	SLM-1 (Workflow Automation): Task decomposition, macro suggestion, and deterministic automation planning. Produces structured intents that route through Control and are logged/audited via MamaLedger.
•	SLM-2 (Accessibility & ADA Compliance): Drives ADA discovery prompts, accommodation mapping (vision, motor, speech, cognitive), and generates accessibility-first UI/interaction recommendations. Outputs must be verifiable and translated into hard rules (locks, pacing, filters) rather than opaque behavior.
•	SLM-3 (Empowerment & Coaching): Plain-language guidance, step-by-step assistance, and user empowerment features (confidence scaffolding, reduced cognitive load modes, consistency cues). Focus is practical enablement in WFH/office/medical contexts, with guardrails enforced by Control.
## 1. Project Purpose
- Provide a C# implementation of the SARA Gen0 core logic, compatible with the MODLES/NBS architecture and the host OS AI ecosystem (e.g., Windows Copilot and OS-native AI services).
- Enable integration with OS-provided on-device SLM capabilities (three role-specialized SLMs for automation, ADA compliance, and user empowerment), while maintaining deterministic Control-routed enforcement and MamaLedger auditability.

---

## 2. Core Requirements
- **Language:** C# (.NET 6 or later recommended)
- **Project Type:** Console Application (or Class Library if embedding)
- **Compatibility:** Windows (primary; aligned to the Windows Copilot ecosystem), cross-platform support preferred where equivalent host-OS AI services exist
- **File IO:** Support for NBS JSON file format (read/write)
- **Data Structures:** Mirror Python Gen0 core data models (NBS wrapper, meta, content)
- **Extensibility:** Modular design for future Gen1/Gen2 upgrades

---

## 3. Key Features
- NBS file creation, reading, and validation
- Proto-Lingua transformation helpers (as in Python Gen0)
- Metadata management (nbs_meta, file_version, last_modified)
- Diagnostic and reference utilities for cross-language validation
- Command-line interface for basic operations (optional)

---

## 4. Directory Structure
```
SARA_Gen0_CSharp/
  |-- Program.cs
  |-- NbsCore.cs
  |-- ProtoLinguaHelpers.cs
  |-- Models/
  |     |-- NbsFile.cs
  |     |-- NbsMeta.cs
  |-- Utils/
  |     |-- FileIO.cs
  |-- Tests/
  |     |-- NbsCoreTests.cs
  |-- README.md
  |-- SPEC_SHEET_GEN0_CSHARP.md
```

---

## 5. Coding Conventions
- Use PascalCase for class and method names
- Use camelCase for local variables and parameters
- Document all public classes and methods with XML comments
- Prefer explicit types over var for clarity
- Follow .NET best practices for error handling and async IO

---

## 6. Example: NBS File Model (C#)
```csharp
public class NbsFile
{
    public NbsMeta NbsMeta { get; set; }
    public object Content { get; set; }
    public string FileVersion { get; set; }
    public DateTime LastModified { get; set; }
}

public class NbsMeta
{
    public string NbsId { get; set; }
    public string NbsType { get; set; }
    public string NbsGen { get; set; }
    public string NbsVer { get; set; }
    public DateTime CreatedAt { get; set; }
    public string Source { get; set; }
    public string ProjectName { get; set; }
    public List<string> Tags { get; set; }
    public double NexusResonanceRadius { get; set; }
    public string NexusStability { get; set; }
}
```

---

## 7. Migration/Interop Notes
- Ensure JSON serialization matches Python Gen0 output for cross-validation
- Provide CLI or API hooks for file conversion and diagnostics
- Maintain clear separation between core logic and platform-specific code

---

## 8. Biometric Learning & Progressive Disability Support

**NEW IN GEN0.1:** SARA now includes comprehensive biometric capture and learning for progressive disabilities.

### 8.1 TechBallCamp Co-Learning Game

SARA learns to filter tremor and motor conditions **by playing drills with the user** through TechBallCamp, a football-training-inspired game suite:

- **Precision Tap** — learns jitter patterns under precision demand
- **Reaction Time** — learns response latency and fatigue impact
- **Sweep** — learns intentional motion vs. tremor oscillation
- **Rhythm** — learns timing consistency and timing drift
- **Endurance** — learns fatigue onset markers and stress response
- **Ball Tracking** — learns smooth pursuit eye-hand coordination
- **Multi-Tap** — learns high-frequency tremor characteristics
- **Hold Steady** — learns baseline tremor at rest

Each drill ramps difficulty. **SARA records at what difficulty tremor interferes most**, then auto-tunes its filter for next session.

### 8.2 Learned Disability Profiles

After 5-10 drills, SARA builds a **comprehensive profile** of the user's specific condition:

```json
{
  "learned_disability_profile": {
    "primary_condition": "parkinsons",
    "tremor_frequency_hz": 4.3,
    "tremor_amplitude_px": 2.4,
    "fatigue_onset_time_sec": 90,
    "optimal_work_intervals": "90_seconds_then_break",
    "personalized_recommendations": {
      "best_time_of_day": "morning_9_11am",
      "medication_sync": "benefits_peak_30min_after_dose"
    },
    "progression_status": "stable"  // or worsening / improving
  }
}
```

### 8.3 Real-Time Adaptive Filtering

SARA uses learned tremor profiles to **filter input in real-time:**

- Kalman filter with learned noise model
- Adaptive sensitivity (1-10 scale based on difficulty/condition)
- Auto-tunes after each session based on filter effectiveness
- User can always override or disable

### 8.4 Progressive Disability Support

Fully specified profiles for:
- **Parkinson's Disease** (4-6 Hz resting tremor, medication cycles)
- **Essential Tremor** (6-12 Hz action tremor, genetic)
- **Tardive Dyskinesia** (1-3 Hz involuntary movement, medication-induced)
- **Age-Related Tremor** (3-8 Hz, worsens with fatigue)

For each condition: optimal drill pacing, filter thresholds, work intervals, best drill sequences.

### 8.5 Condition Progression Tracking

SARA monitors **how the condition evolves over weeks/months:**

- Compares baseline to recent drill history
- Detects: improvement, stability, or worsening
- Recommends filter adjustments if worsening detected
- Celebrates user adaptation if accuracy improving despite worsening tremor

---

## 9. References

**Core Specifications:**
- [SPEC_SHEET_GEN0_CSHARP_EXTENDED.md](SPEC_SHEET_GEN0_CSHARP_EXTENDED.md) — extended C# UI spec
- [BIOMETRIC_PROTOCOL_SPEC.md](BIOMETRIC_PROTOCOL_SPEC.md) — **NEW** complete biometric capture, TechBallCamp, and learned disability profiles
- [ADA_PHASE_1_RECOVERY_REPORT.md](ada_phase1_recovery_report.txt) — ADA recovery behavior validation

**Supporting Architecture:**
- [ACTIVE_FILE_SET.md](ACTIVE_FILE_SET.md)
- [Python Gen0/Gen1 source files]
- [MODLES/NBS documentation]
- [actionmap.updated.json](actionmap.updated.json) — routing and SLM intent mapping
- [sara_controlgen1.py](sara_control/sara_controlgen1.py) — CONTROL pillar (backend routing)
- [sara_mamagen1.py](sara_mama/sara_mamagen1.py) — MAMA pillar (presentation/adaptation)

**Implementation Reference:**
- [DisabilityMapper/Services/HidService.cs](DisabilityMapper/Services/HidService.cs) — raw input capture (tremor signals)
- [DisabilityMapper/Services/MacroEngine.cs](DisabilityMapper/Services/MacroEngine.cs) — keystroke execution
- [DisabilityMapper/ViewModels/MainViewModel.cs](DisabilityMapper/ViewModels/MainViewModel.cs) — MVVM controller

---

*Generated by AI (GitHub Copilot) — April 2026*
# PHASE 6 — HUD Modularity & Geometry Persistence (Refined & Fully Specified)

Phase 6 defines how SARA’s interface behaves:

- modular  
- detachable  
- geometry switchable  
- ADA aware  
- persistent across sessions  
- adaptive to WFH, office, hybrid, or medical environments  

This is the visual backbone of SARA’s cockpit.

We’ll refine it in four layers:

1. **HUD Geometry Types**  
2. **HUD Modularity Rules**  
3. **HUD Persistence Model**  
4. **ADA/Medical/OT/VA Integration**

Let’s go step by step.

---

# **6.1 HUD Geometry Types (Deterministic, Switchable)**

SARA must support **multiple HUD geometries**, each optimized for different environments and accessibility needs.

### **Supported Geometries**
- **Square Grid HUD**  
  - predictable  
  - low cognitive load  
  - ideal for WFH and medical accommodations  

- **Radial HUD**  
  - fast access  
  - gesture friendly  
  - ideal for mobility or motor accommodations  

- **Action Bar HUD**  
  - horizontal or vertical  
  - ideal for office or hybrid environments  

- **High Contrast HUD**  
  - ADA optimized  
  - ideal for vision accommodations  

- **Minimalist HUD**  
  - low sensory load  
  - ideal for PTSD, anxiety, or cognitive fatigue  

### **Switching Rules**
HUD geometry may be switched:

- by user command  
- by ADA mode  
- by medical/OT input  
- by environment change (WFH → office)  
- by sensory overload detection  

Switching must be:

- instantaneous  
- non destructive  
- reversible  
- logged in MamaLedger  

---

# **6.2 HUD Modularity Rules (Detachable, Reconfigurable)**

The HUD must be **modular**, meaning:

- every panel  
- every widget  
- every control  
- every display element  

…can be:

- detached  
- moved  
- resized  
- hidden  
- pinned  
- grouped  

### **Modular Components**
- task panel  
- ambiguity panel  
- ADA panel  
- shunt log viewer  
- macro recorder  
- voice/gesture sensitivity sliders  
- geometry selector  
- system status  
- notifications  
- ledger summaries  

### **Modularity Rules**
- no module may bypass CONTROL  
- no module may store internal metadata  
- no module may expose shunt headers  
- no module may leak ADA/medical/VA data  
- all modules must use the canonical shunt contract  

---

# **6.3 HUD Persistence Model (Deterministic, Ledger Backed)**

HUD layout must persist across sessions.

### **Persistence Storage**
All HUD geometry and layout data must be stored in:

`MamaLedger.HUD.Layout`

### **Stored Fields**
```
{
  "geometry_type": "square | radial | action_bar | high_contrast | minimalist",
  "module_positions": { ... },
  "module_sizes": { ... },
  "module_visibility": { ... },
  "ada_overrides": { ... },
  "environment_profile": "WFH | office | hybrid | medical | VA"
}
```

### **Persistence Rules**
- layout must load on startup  
- layout must adapt if ADA mode is active  
- layout must adapt if medical/OT/VA accommodations apply  
- layout must adapt if environment changes  
- layout must never expose internal metadata  

---

# **6.4 ADA/Medical/OT/VA Integration (Critical)**

HUD geometry must adapt to:

- ADA mode  
- medical accommodations  
- OT recommendations  
- VA protected work environment requirements  
- sensory overload  
- cognitive fatigue  
- mobility limitations  

### **Examples**
- **PTSD or sensory overload** → Minimalist HUD  
- **Vision impairment** → High contrast HUD  
- **Motor limitations** → Radial HUD  
- **Cognitive fatigue** → Square HUD with reduced modules  
- **VA protected work environment** → Reduced sensory load + predictable layout  
- **OT ergonomic recommendations** → Larger buttons, reduced reach distance  

### **Dynamic Adaptation**
When environment changes:

- WFH → office  
- office → hybrid  
- hybrid → medical leave  
- medical leave → WFH  

SARA must:

- re-run ADA discovery  
- re-run ambiguity scan  
- re-run geometry selection  
- adjust HUD layout  
- store new layout in MamaLedger  

---
# PHASE 7 — Macro Recording & Sovereign Proxy (Refined & Fully Specified)

This subsystem has two major responsibilities:

1. **Macro Recording & Mapping**  
2. **Sovereign Proxy (System Wide Input Layer)**  

Both must obey:

- Control only routing  
- canonical shunt contract  
- ADA/medical/OT/VA accommodations  
- deterministic behavior  
- no metadata leakage  
- no direct system access without Control  

Let’s refine each part.

---

# **7.1 Macro Recording (Deterministic, Pillar Safe)**

SARA must allow the user to record macros that capture:

- UI actions  
- keyboard input  
- mouse/gesture input  
- voice commands  
- HUD interactions  
- Control routed pillar calls  

### **Macro Recording Rules**
- All macro events must be captured through **Control**, never directly from UI or OS.  
- Every recorded event must be wrapped in a **Shunt Header**.  
- No raw OS events may be stored.  
- No internal metadata may leak into the macro.  
- ADA/medical/OT/VA accommodations must modify macro playback timing and pacing.  

### **Macro Event Structure**
```
{
  "event_id": "GUID",
  "timestamp": "ISO8601",
  "event_type": "UI | voice | gesture | control_call",
  "payload": { ... },
  "context_tags": [ ... ]
}
```

### **Macro Storage**
All macros must be stored in:

`MamaLedger.Macros.Records`

### **Macro Editing**
Users may:

- rename  
- reorder  
- delete  
- disable  
- duplicate  

Macros must never expose:

- shunt headers  
- ADA data  
- medical/OT/VA data  
- ledger metadata  

---

# **7.2 Macro Mapping (User Defined, ADA Aware)**

Users must be able to map macros to:

- voice commands  
- gestures  
- keyboard shortcuts  
- HUD buttons  
- radial menu items  
- action bar slots  

### **Mapping Rules**
- All mappings must be stored in MamaLedger.  
- ADA mode may override mappings for safety.  
- Medical/OT/VA accommodations may adjust timing.  
- No mapping may bypass Control.  

### **Mapping Storage**
`MamaLedger.Macros.Mapping`

---

# **7.3 Macro Playback (Deterministic, Safe)**

When a macro is executed:

1. Control loads the macro  
2. Control validates ADA/medical/OT/VA constraints  
3. Control replays each event deterministically  
4. Control logs the execution  
5. Control sanitizes any output  

### **Playback Safety Rules**
- No macro may run longer than ADA allowed continuous time.  
- No macro may trigger sensory overload.  
- No macro may violate medical pacing requirements.  
- No macro may bypass ambiguity detection.  
- No macro may produce client output without sanitization.  

---

# **7.4 Sovereign Proxy (System Wide Input Layer)**

This is the **big one**.

The Sovereign Proxy is SARA’s ability to:

- intercept  
- normalize  
- route  
- and replay  

system wide input **through Control**, not directly.

This is what makes SARA:

- hands free  
- low strain  
- ADA compliant  
- WFH optimized  
- safe for medical/OT/VA accommodations  

### **Proxy Responsibilities**
- capture voice commands  
- capture gestures  
- capture keyboard shortcuts  
- capture HUD interactions  
- normalize them into Shunt Headers  
- route them through Control  
- enforce ADA/medical/OT/VA constraints  
- replay macros safely  

### **Proxy Input Types**
- voice  
- gesture  
- keyboard  
- mouse  
- HUD  
- macro triggers  

### **Proxy Output**
Always a **Control validated shunt**.

---

# **7.5 ADA/Medical/OT/VA Integration**

This is where Phase 7 becomes powerful.

### **A. Medical pacing**
Macros must respect:

- maximum continuous work time  
- required break intervals  
- OT pacing recommendations  
- cognitive load limits  

### **B. Sensory load**
Macros must:

- avoid rapid UI changes  
- avoid flashing  
- avoid overload  
- adapt geometry if needed  

### **C. VA protected work environment**
Macros must:

- reduce friction  
- reduce sensory load  
- enforce predictable sequences  
- avoid rapid context switching  

### **D. PTSD/Anxiety accommodations**
Macros must:

- avoid sudden audio  
- avoid sudden geometry changes  
- avoid rapid color transitions  

### **E. Mobility accommodations**
Macros may:

- increase button size  
- reduce gesture complexity  
- slow down playback  

---

# **7.6 MamaLedger & Audit Requirements**

Every macro event and playback must be logged in MamaLedger.Macros.Log.

Each entry must include:
- macro_id
- event_id
- timestamp
- ADA/medical/OT/VA adjustments applied
- success/failure
- sanitized payload

This ensures:
- full auditability
- deterministic replay
- safe debugging
- no metadata leaks

---
---

# PHASE 8 — Sensitivity Controls (0.00 → 10.00, 0.25 increments, Adaptive Filtering)

SARA must support a **0.00 to 10.00 sensitivity scale**, adjustable in **0.25 increments**.

### **Sensitivity Scale**
```
0.00  →  off  
0.25  →  extremely low  
0.50  →  very low  
...  
5.00  →  medium  
...  
9.75  →  extremely high  
10.00 →  maximum sensitivity
```

This gives you **41 discrete levels** of control — perfect for ADA, medical, OT, and VA protected work environments.

---

# **8.1.A — Sensitivity Channels (All Use 0–10 Scale)**

SARA must apply this scale to:

- voice input  
- gesture input  
- keyboard shortcuts  
- macro triggers  
- HUD interactions  
- Sovereign Proxy input  

Each channel is independently adjustable.

---

# **8.1.B — Adaptive Filtering for Disabilities (Critical Upgrade)**

When a disability, medical condition, or OT note is involved, SARA must **automatically apply adaptive filtering** to reduce false triggers and improve comfort.

### **Adaptive Filters Include:**

#### **1. Tremor Filtering**
For motor conditions:

- ignore micro movements  
- ignore jitter  
- require sustained gestures  
- increase gesture smoothing  
- widen gesture recognition windows  

#### **2. Broken Speech Pattern Filtering**
For speech related conditions:

- allow irregular cadence  
- allow pauses  
- allow repeated syllables  
- allow stutters  
- allow breath breaks  
- reduce confidence threshold requirements  

#### **3. Stutter Adaptive Voice Recognition**
SARA must:

- avoid double triggering  
- avoid interpreting stutters as repeated commands  
- avoid cutting off commands prematurely  

#### **4. Cognitive Load Filtering**
If cognitive fatigue or overload is detected:

- reduce required precision  
- widen timing windows  
- slow down input interpretation  
- reduce sensitivity spikes  

#### **5. PTSD/Anxiety Filtering**
SARA must:

- avoid sudden activation  
- avoid rapid geometry changes  
- avoid high sensitivity voice triggers  
- avoid gesture triggers that could misfire  

---

# **8.1.C — Initial Sensitivity Calibration (Disability Aware)**

When ADA mode or medical/OT accommodations are active, SARA must:

1. **Start with a safe baseline sensitivity**  
  Example defaults:
  - voice: 3.00  
  - gesture: 2.50  
  - macro triggers: 2.00  
  - HUD interactions: 4.00  

2. **Run a short calibration session**  
  SARA observes:
  - tremor patterns  
  - speech cadence  
  - stutter frequency  
  - motor control range  
  - reaction time  
  - cognitive pacing  

3. **Adapt the sensitivity curve**  
  SARA adjusts:
  - thresholds  
  - debounce windows  
  - smoothing  
  - timing  
  - gesture amplitude requirements  

4. **Store the personalized profile**  
  Stored in:  
  `MamaLedger.Input.CalibrationProfile`

---

# **8.1.D — Continuous Adaptation (Real Time Learning)**

SARA must continue adapting sensitivity in real time using **deterministic pattern learning** (from Phase 1):

- if tremors increase → increase smoothing  
- if speech cadence slows → widen timing windows  
- if stutters increase → reduce confidence threshold  
- if fatigue increases → reduce sensitivity  
- if environment changes → adjust accordingly  

This is NOT probabilistic.  
This is NOT neural.  
This is deterministic pattern recognition.

---

# **8.1.E — Safety Rules (Updated)**

To prevent overload or accidental triggers:

- no sensitivity may increase automatically above 7.00  
- ADA Lock prevents sensitivity changes above 5.00  
- medical/OT/VA accommodations override user set values if unsafe  
- macro triggers must respect pacing limits  
- gesture triggers must respect tremor filtering  
- voice triggers must respect stutter filtering  

---
# PHASE 9 — UI Hot Reload & Reference Based Layout (Refined & Fully Specified)

Phase 9 has two major responsibilities:

1. **UI Hot Reload**  
   (real time updates from Python → C# without restarting the app)

2. **Reference Based Layout**  
   (UI elements defined by references, not hardcoded positions)

This is the phase that makes SARA’s interface:

- modular  
- adaptive  
- ADA aware  
- medical/OT/VA aware  
- deterministic  
- safe  
- future proof  

Let’s break it down cleanly.

---

# **9.1 UI Hot Reload (Deterministic, Control Routed)**

SARA must support **real time UI updates** triggered by:

- Python pillar instructions  
- ADA mode changes  
- medical/OT/VA accommodations  
- geometry switching  
- macro playback  
- sensitivity changes  
- environment changes (WFH → office → hybrid)  

### **Hot Reload Rules**
- All UI updates must route through **Control**, never directly from Python.  
- All updates must use the **canonical shunt contract**.  
- No UI element may update itself.  
- No UI update may bypass ADA Lock.  
- No UI update may cause sensory overload.  
- No UI update may expose internal metadata.  

### **Hot Reload Flow**
1. Python pillar generates a UI instruction  
2. Python wraps it in a Shunt Header  
3. Control validates the instruction  
4. Control applies ADA/medical/OT/VA filters  
5. Control updates the C# UI  
6. Control logs the update in MamaLedger  

### **Hot Reload Safety**
- No flicker  
- No geometry jump  
- No rapid transitions  
- No overload  
- No nondeterministic behavior  

---

# **9.2 Reference Based Layout (The Backbone of Modularity)**

SARA’s UI must be defined by **references**, not hardcoded positions.

This is what makes the HUD:

- modular  
- detachable  
- reconfigurable  
- persistent  
- ADA aware  
- environment aware  

### **Reference Types**
- `ref_geometry`  
- `ref_module`  
- `ref_position`  
- `ref_size`  
- `ref_visibility`  
- `ref_theme`  
- `ref_accessibility`  

### **Reference Example**
```
{
  "ref_module": "task_panel",
  "ref_geometry": "square",
  "ref_position": "top_left",
  "ref_size": "medium",
  "ref_visibility": true
}
```

### **Reference Rules**
- No UI element may define its own geometry.  
- No UI element may define its own position.  
- No UI element may bypass Control.  
- All references must be stored in MamaLedger.  
- All references must be ADA aware.  

---

# **9.3 Layout Persistence (Ledger Backed, Deterministic)**

All layout data must be stored in:

`MamaLedger.HUD.Layout`

### **Stored Fields**
```
{
  "geometry_type": "...",
  "module_positions": { ... },
  "module_sizes": { ... },
  "module_visibility": { ... },
  "theme": "light | dark | high_contrast",
  "ada_overrides": { ... },
  "environment_profile": "WFH | office | hybrid | medical | VA"
}
```

### **Persistence Rules**
- Layout loads on startup  
- Layout adapts to ADA mode  
- Layout adapts to medical/OT/VA accommodations  
- Layout adapts to environment changes  
- Layout never exposes internal metadata  

---

# **9.4 ADA/Medical/OT/VA Integration (Critical)**

UI hot reload must adapt to:

- tremors  
- stutters  
- broken speech patterns  
- cognitive fatigue  
- PTSD/anxiety triggers  
- sensory overload  
- mobility limitations  
- VA protected work environment rules  

### **Examples**
- If tremors increase → enlarge buttons  
- If stutters increase → widen voice timing windows  
- If sensory overload → switch to minimalist HUD  
- If cognitive fatigue → reduce module count  
- If PTSD triggers → disable animations  
- If VA mode → enforce predictable layout  

---

# **9.5 Environment Aware UI Behavior**

When environment changes:

- WFH → office  
- office → hybrid  
- hybrid → medical leave  
- medical leave → WFH  

SARA must:

- re-run ADA discovery  
- re-run ambiguity scan  
- re-run geometry selection  
- adjust HUD layout  
- adjust sensitivity  
- adjust pacing  
- adjust macro behavior  

All through **Control**, using the **canonical shunt contract**.

---

# **9.6 Hot Reload Safety Rules**

To prevent overload or instability:

- no more than 1 geometry change per second  
- no more than 3 module changes per second  
- no animation longer than 250ms in ADA mode  
- no animation at all in PTSD/anxiety mode  
- no color flashes  
- no rapid transitions  
- no UI updates during sensory overload  

---

# 🌘 **Phase 9 Status: COMPLETE**

You now have:

- a fully specified hot reload system  
- reference based layout  
- ADA/medical/OT/VA aware UI adaptation  
- environment aware UI behavior  
- deterministic Control routed updates  
- zero ambiguity  

## Profile Types (Gen0)

SARA Gen0 operates against three canonical profile types. These are required for routing, compliance, ADA adaptation, and deterministic behavior.

- **User Profile:**  
  Represents the human operator’s identity, ADA/medical/OT/VA accommodations, and environment (WFH, office, hybrid).  
  Used for HUD adaptation, ADA Lock, pacing rules, and environment switching.

- **AI Profile:**  
  Represents SARA’s internal state and configuration: active modules, learning modes, and capability flags.  
  Used for deterministic feature gating and internal logic.

- **Machine Profile:**  
  Represents the hardware and OS environment SARA is running on (CPU/RAM/GPU, sensors, custom/ADA devices).  
  Used for affordability constraints, feature enable/disable, and device enumeration.

## MamaLedger (Gen0)

MamaLedger is the canonical backend store for all profile and compliance state in SARA Gen0. It is never UI-facing and is only accessed through CONTROL and MAMA.

MamaLedger must store:

- **Profiles**
  - MamaLedger.Profiles.User  
  - MamaLedger.Profiles.AI  
  - MamaLedger.Profiles.Machine  

- **Learning & Context**
  - MamaLedger.Learning.Patterns  
  - MamaLedger.Learning.Structure  
  - MamaLedger.Learning.Predictions  

- **Ambiguity & Audit**
  - MamaLedger.Ambiguity.Reports  
  - MamaLedger.Audit.Shunts  

- **NBS Continuity**
  - MamaLedger.NBS.Continuity (snapshot/diff metadata only)  

Rules:
- UI must never access MamaLedger directly.  
- All reads/writes flow: UI → CONTROL → MAMA → MamaLedger → MAMA → CONTROL → UI.  
- No pillar or module may bypass CONTROL when interacting with MamaLedger.


# SARA — Symbolic Adaptive Remapping Architecture
### *Current Working Prototype: SARA — Systematic Adaptive Reasoning Architecture*

**A non-kernel adaptive input platform for motor-impaired veterans. Tremor filtering, device remapping, therapeutic activity sessions, and zero-trust profile mobility — all in user-space.**

SARA is not an LLM wrapper. It is a pillar-based orchestration system with a deterministic protocol, a clinical-grade signal filter pipeline, and a therapeutic delivery layer built around the VA Adaptive Sports Program and occupation-based rehabilitation science.

---

## Clinical Purpose

SARA restores digital autonomy to individuals with motor-control impairments by replacing standard keyboard/mouse interaction with filtered, remapped, accessible input from any HID device.

| Population | Primary Impairments Addressed |
|---|---|
| **Parkinson's Disease** | Intention tremor, resting tremor, bradykinesia, rigidity |
| **Tardive Dyskinesia** | Involuntary hyperkinetic movement from long-term neuroleptic use |
| **TBI / Stroke** | Residual hemiparesis, spasticity, upper-extremity ataxia |
| **SCI / Limb Difference** | Gross-movement HOTAS/switch input replacing fine-motor keyboard |

**Deployment continuum:** VAMC PM&RS clinics → outpatient OT/RT → home use (same profile, no reconfiguration) → telehealth via Raspberry Pi server (`SARA_HOST` env var).

---

## Architecture

SARA runs as two decoupled applications. All inter-component communication uses the BuceyShunt 8-field JSON envelope over HTTP POST.

```
  ┌──────────────────────────────────────────────────────────────┐
  │           VALANCE / DISABILITYMAPPER  (SARA.exe)             │
  │  SharpDX DirectInput   · Tremor Filter Pipeline              │
  │  GlobalHookService     · Steno Chord Engine                  │
  │  Patient Console       · Office Suite Bridge                 │
  │  Session Recorder      · Zero-Trust Envoy Tunnel             │
  └──────────────────┬───────────────────────────────────────────┘
                     │  BuceyShunt  (JSON / HTTP POST → :5050/shunt)
  ┌──────────────────┴───────────────────────────────────────────┐
  │              SARA PYTHON BACKEND                             │
  │  [sara_core]     FSM · Document I/O · Memory                 │
  │  [sara_control]  Routing Authority · Port 5050 · ADA Init    │
  │  [sara_mama]     Presentation · 5-Pillar HID Discovery       │
  │  [sara_security] Paladin Black-Hole · Sheriff Audit · Envoy  │
  │  [sara_sdk]      HID Database · Clinical Mapping Defaults    │
  └──────────────────────────────────────────────────────────────┘
```

**Dependency direction (one-way, no backflow):**
`SDK / MAMA / SECURITY → CONTROL → CORE`

---

## Python Backend Pillars

~14,100+ lines across five pillars. Decomposition in progress (see `SARA_MONOLITH_DECOMPOSITION.md`).

| Pillar | Lines | Role |
|---|---|---|
| **CONTROL** | ~5,544 | Sole routing authority. BuceyShunt FSM, AI backend orchestration, King/Paladin/Sheriff chain, ADA enforcement |
| **CORE** | ~3,800 | Engine only — file I/O (image, video, audio, 3D, Office), NBS persistence, proto-lingua, memory |
| **MAMA** | ~2,050 | Presentation layer — biometrics, hardware discovery orchestration, adaptive jargon lexicon |
| **SECURITY** | ~2,350 | Paladin (threat/injection detection), Sheriff (audit), Deputy, Archeologist, Conservator, Envoy, King |
| **SDK** | ~370+ | HID device database, DirectInput axis/button specs, `build_default_mapping()`, external adapters |

---

## BuceyShunt Protocol

Every message — pillar-to-pillar and C# to Python — uses the same envelope:

```json
{
  "shunt_id": "<uuid>",
  "source_pillar": "MAMA",
  "target_pillar": "CONTROL",
  "timestamp": "<ISO8601>",
  "intent": "<command>",
  "ACT": "00",
  "payload": {},
  "context_tags": [],
  "requires_response": true
}
```

**ACT codes:** `00` = route · `01` = validate/normalize · `10` = build/office · `11` = dispatch/audit

The Flask HTTP bridge listens on `127.0.0.1:5050/shunt`. Override target with `SARA_HOST` env var (e.g., `192.168.42.1:5050` for clinic Raspberry Pi).

---

## VALANCE Feature Inventory

All features below are implemented and wired in the current codebase.

### Tremor Filter Pipeline (`TremorFilterService.cs`)

Three-stage signal attenuation applied to every input event before command execution:

| Stage | Mechanism | Clinical Target |
|---|---|---|
| **1 — Debounce** | Nullifies button events shorter than configurable ms threshold | Micro-presses from clonus / intention tremor |
| **2 — Dead Zone** | Configurable radius; ignores axis movement within bounds | Resting tremor on joystick / HOTAS axes |
| **3 — Low-Pass Smooth** | Exponential filter, variable alpha coefficient | High-frequency tremor spikes without adding control lag |

Live signal monitor displays raw vs. filtered values side-by-side for real-time clinician calibration.

### WFH Global Tremor Filter (`GlobalHookService.cs`)

System-wide keyboard debounce + mouse dead zone via Windows low-level hooks. Active across all applications (browser, Word, email) without requiring device profiles. One-click toolbar toggle.

### Input Adapter Output Layer (`VirtualDeviceService.cs`)

Routes filtered input to keyboard/mouse events via Windows `SendInput` API (same API used by JAWS, NVDA, Dragon). **No kernel driver required.** Runs on locked VA workstations with no IT approval needed.

Default mapping: left stick → mouse cursor · right stick → scroll · triggers → mouse buttons · D-pad → arrow keys · face buttons → Space/Escape/E/Q. All mappings overridable via hot-reloaded `input_map.json`.

### Session Recording (`SessionRecorderService.cs`)

Automatic JSONL telemetry for every input event, started when mapping activates:

```json
{"timestamp":"2026-05-17T16:20:01.002Z","device":"HOTAS_T16000M","role":"Patient","input":"AXIS_X","raw_value":0.421,"filtered_value":0.210}
```

Location: `%AppData%\DisabilityMapper\sessions\session_YYYYMMDD_HHMMSS.jsonl`

Raw and filtered values are captured simultaneously. PT/OT can review tremor amplitude delta across sessions — objective, timestamped clinical outcome documentation.

### Patient Console (`PatientConsoleWindow.xaml`)

Patient-facing activity launcher. PT/OT prescribes an adaptive sport from the VALANCE clinician panel; Patient Console opens pre-selected on that activity.

Pressing **PLAY** simultaneously activates: Input Adapter + Session Recording. **STOP** ends both and closes the session file. The patient sees only the activity selector and a live "Input Adapter Active" indicator — no clinical UI exposed.

### Steno Chord Keyboard (`StenoChordEngine.cs`)

Chorded input: hold multiple joystick/switch buttons simultaneously → full text string injected into any focused application. On-screen virtual keyboard overlay. Designed for users who cannot isolate individual keys on a standard QWERTY board. `StenoVm.TextReady` → `InjectRaw()` → `SendInput` to active window.

### Office Suite Bridge (`OfficeSuiteWindow`)

Dedicated macro and mapping layouts for Microsoft Word, Excel, VS Code, and media editing. HOTAS throttle axes, analog sticks, and button chords map to navigation, formatting, and command shortcuts. Applies device-filtered input to productivity software without per-application reconfiguration. Enables veterans to manage VA paperwork, benefits claims, and documents without standard keyboard/mouse.

### Device Support

| Type | Interface | Notes |
|---|---|---|
| HOTAS flight controllers | DirectInput | Thrustmaster, Logitech, CH, Saitek, Honeycomb |
| Gamepads | DirectInput / XInput | Xbox 360/One/Series/Elite, PowerA, PDP, 8BitDo, generic |
| Joysticks | DirectInput | All DirectInput-compliant |
| Keyboard / Mouse | Raw Input + WM hooks | GlobalHookService WFH filter applies here |
| Touchscreen / Pen | WM_POINTER | `TouchService.cs` |
| Accessibility switches | HID | Any HID-compliant switch device |
| Wake devices | HID | `WakeDeviceService.cs` |

---

## Therapeutic Gaming Rationale

The Patient Console exists because **treatment adherence outside the clinic is the primary barrier to successful motor rehabilitation.** Standard outpatient PT/OT runs 1–3 sessions per week. Neuroplastic adaptation and tremor compensation require daily repetitive motor practice. Traditional home exercise programs have documented low compliance.

**Games are the delivery vehicle. The therapy is the motor activation.**

When a veteran plays a sports simulation using a HOTAS or joystick through SARA:
- Every axis movement is filtered, recorded, and compared to their baseline profile
- The game provides immediate sensory feedback on motor output quality — which standard exercises do not
- The HOTAS/joystick hardware provides proportional multi-axis tracking, capturing the *exact degree* of tremor variance across 3D space — not just binary present/absent
- SARA records every session, so PT/OT receives home-practice data at the next clinical appointment

The high-engagement, persistent design of these activities is intentional. Compliance shifts from obligation to intrinsic motivation. A veteran who voluntarily plays for two hours outside PT/OT has performed two hours of clinician-prescribed motor practice. This is the definition of occupation-based therapy — using personally meaningful, chosen activity as the therapeutic medium.

Supporting evidence base (search terms for Gemini citations in works cited):
- *Virtual reality and video game-based rehabilitation in Parkinson's Disease* — dopaminergic engagement, motor pathway reinforcement
- *Wii and Xbox Kinect rehabilitation RCTs for PD* — balance, gait, upper extremity function
- *Exergaming systematic reviews in neurological rehabilitation*
- VA MOVE! Program — gamified adherence in veteran populations
- Occupation-based therapy (AOTA framework) — meaningful activity as therapeutic medium

**VA Adaptive Sports Program alignment:** Public Law 110-389 (Veterans' Benefits Improvement Act of 2008, §901). CTRS staff at VAMCs already prescribe adaptive sport activities as therapy. SARA provides the technology layer that makes those activities accessible to veterans who are locked out of standard commercial controllers. The PT/OT prescription field in VALANCE maps directly to CTRS clinical workflow.

---

## Security Architecture

### Paladin Black-Hole Defense

Drop posture by default. Non-compliant packets are silently dropped — the system does not acknowledge the connection attempt. All external data is sanitized and audited by the SECURITY pillar before reaching CONTROL or CORE. Injection characters stripped at the MAMA layer (`_sanitize_name()`).

### Envoy Zero-Trust Profile Tunnel

Based on a 31F Signal Corps proximity handshake model. A veteran carries their validated tremor profile on a mobile device or wearable running the SARA mobile app. Walking up to any institutional terminal equipped with barebones-ai64 triggers a proximity handshake via `Envoy`. The veteran's full device profile, tremor filter settings, and learned mappings are cryptographically tunneled to that terminal — no manual login, no reconfiguration. Profile follows the veteran terminal-to-terminal across the VA ecosystem.

---

## Federal & Institutional Compliance

**Section 508 (29 U.S.C. § 794d):** SARA uses Windows `SendInput` — the federally-approved standard for assistive technology output (JAWS, NVDA, Dragon). No kernel driver installs. Compatible with VA workstation lock-down policies.

**Driver hygiene:** Nefarius ViGEmBus (`Nefarius.ViGEm.Client`) was fully removed from the codebase — trademark dispute status and VA TRM incompatibility. Zero third-party kernel dependencies remain.

**ADA enforcement:** CONTROL pillar enforces `ada_accessibility_mapping_initialization_enforcement` at startup. MAMA biometrics provide always-on adaptive calibration. Phase 1 ADA recovery validated against four test vectors (see `ada_phase1_recovery_report.txt`).

---

## Build & Run

**Start the Python backend:**
```
SARA_RUN.bat
```
or
```
python sara_control/sara_control_http.py
```
CONTROL available at `http://127.0.0.1:5050`

**Build the C# client:**
```
cd DisabilityMapper/DisabilityMapper
dotnet build DisabilityMapper.slnx -c Debug
```
Output: `bin\Debug\net10.0-windows\SARA.exe`

**Verify connection:** VALANCE calls `GET /health` on startup. Status bar shows CONTROL connected/disconnected.

**Client dependencies:**

| Package | Version | Purpose |
|---|---|---|
| `SharpDX.DirectInput` | 4.2.0 | Physical HID device polling |
| `InputSimulatorStandard` | 1.0.0 | SendInput (keyboard/mouse output) |
| `CommunityToolkit.Mvvm` | 8.3.2 | MVVM framework |
| `Newtonsoft.Json` | 13.0.3 | Profile serialization |

---

## Key Spec Documents

| File | Contents |
|---|---|
| `SARA_MONOLITH_DECOMPOSITION.md` | Architectural decomposition — what each module contains, what leaked where, rebuild structure |
| `BIOMETRIC_PROTOCOL_SPEC.md` | Tremor detection, ADA biometric protocol |
| `SARA_MONOLITH_DECOMPOSITION.md` | PLM/pillar spec, data flow rules |
| `ada_phase1_recovery_report.txt` | ADA compliance test results |
| `sara_architecture_log.md` | Full architectural lineage and design decisions |

---

## Repository Structure

```
SARA/
├── sara_control/       # CONTROL pillar (routing authority, port 5050)
├── sara_core/          # CORE pillar (engine, I/O, NBS memory)
├── sara_mama/          # MAMA pillar (presentation, HID discovery)
├── sara_security/      # SECURITY pillar (Paladin, Sheriff, Envoy)
├── sara_sdk/           # SDK pillar (HID database, device adapters)
├── DisabilityMapper/   # C# WPF client (SARA.exe)
│   └── Services/       # TremorFilter, HidService, VirtualDevice, Steno, Recorder
└── [spec docs]         # Architecture, ADA, installer, decomposition specs
```

---

## License & Clinical Contributions

Open-source. Clinical input requested from CTRS, ATP, PT, and OT professionals within VHA and private practice — particularly around default filter parameters, adaptive device configurations, and therapeutic activity catalogs.

**Repository:** https://github.com/docbucey/sara.git

---

## Works Cited

### Neuroplasticity, Motivation & Patient Adherence

**Barry, G., Galna, B., & Rochester, L. (2014).** The role of exergaming in Parkinson's disease rehabilitation: a systematic review of the evidence. *Journal of NeuroEngineering and Rehabilitation, 11*(1), 33.
> Validates that high-engagement interactive digital media triggers striatal dopamine release, reinforcing motor learning and boosting patient compliance outside the clinic.

**Mirelman, A., et al. (2016).** Virtual reality for gait and balance disorders in neurodegenerative diseases: A systematic review and meta-analysis. *Journal of Neurology, 263*(12), 2363–2374.
> Demonstrates that closed-loop audio-visual feedback inherent to simulated environments produces equivalent or superior neuroplastic adaptation compared to conventional physical therapy exercises.

**Rüth, M., & Kaspar, K. (2023).** Commercial exergames for rehabilitation of physical health and quality of life: a systematic review of RCTs with adults in unsupervised home environments. *Frontiers in Psychology, 14*, 1155569.
> Establishes the clinical efficacy and ecological validity of unsupervised home-based gamified telerehabilitation to maintain motor progress.

---

### Upper-Limb Rehabilitation & Proportional Multi-Axis Input

**Cano-Porras, D., et al. (2019).** Leap motion controlled video game-based therapy for upper limb rehabilitation in Parkinson's disease: a feasibility study. *Journal of NeuroEngineering and Rehabilitation, 16*(1), 1–11.
> Proves that serious games targeting gross upper-extremity movements yield statistically significant improvements in manual dexterity, grip strength, and Box and Blocks Test scores in neurological disorders.

**Herz, N. B., et al. (2013).** Active video gaming, exergaming, and Parkinson's disease: An emerging alternative to traditional physical therapy. *Movement Disorders, 28*(10), 1339–1343.
> Supports use of multi-axis proportional controller input to bypass fine-finger motor constraints while still capturing fine movement telemetry for clinical outcome tracking.

---

### Identity-Driven Engagement & Occupation-Based Therapy

**American Occupational Therapy Association (AOTA). (2020).** Occupational Therapy Practice Framework: Domain and Process (4th ed.). *American Journal of Occupational Therapy, 74*(Suppl. 2).
> Clinical standard for occupation-based therapy — embedding therapeutic motor activity into personally meaningful tasks (sport identity, competitive context) reduces patient resistance and increases voluntary engagement.

**Bosch-Barceló, P., et al. (2025).** Gamification integration in technological devices for motor rehabilitation in Parkinson disease: Scoping review. *JMIR Serious Games, 13*, e69433.
> Establishes the necessity of user-centric, disorder-specific gamification over off-the-shelf commercial game use; directly supports SARA's Patient Console prescription model targeting specific movement profiles.

---

### Federal Accessibility & Systems Usability

**U.S. Department of Veterans Affairs.** Section 508 Resource Office Compliance Guidelines. Under the authority of 29 U.S.C. § 794d.
> Dictates user-space UI Automation and standard `SendInput` event routing required for deployment on federal networks without kernel-level administrative modifications — the basis for SARA's zero-kernel-driver architecture.

---

### Federal Disability & Accessibility Law

**Americans with Disabilities Act of 1990 (ADA), 42 U.S.C. §§ 12101–12213**, as amended by the **ADA Amendments Act of 2008 (ADAAA), Pub. L. 110-325.**
> Establishes the federal definition of disability and the non-discrimination mandate across employment, public accommodations, and government services. ADAAA broadened the "substantially limits" standard — expanding SARA's eligible user population to include episodic and mitigating-measures conditions (e.g., medicated Parkinson's, intermittent spasticity).

**Section 504 of the Rehabilitation Act of 1973, 29 U.S.C. § 794.**
> Prohibits disability discrimination by any program or activity receiving federal financial assistance. Establishes baseline reasonable-accommodation obligations that SARA's configurable filter profiles directly satisfy for VA clinical and telehealth contexts.

**Section 508 of the Rehabilitation Act of 1973 (as amended), 29 U.S.C. § 794d; Access Board ICT Standards (36 C.F.R. Part 1194).**
> Federal procurement mandate requiring electronic and information technology to be accessible to people with disabilities. The 2017 Refresh (WCAG 2.0 AA harmonization) governs SARA's UI and output layer compliance obligations.

**Assistive Technology Act of 1998 (AT Act), Pub. L. 105-394, 29 U.S.C. § 3001 et seq.**, reauthorized 2004 (Pub. L. 108-364).
> Funds state AT programs (Kentucky, Tennessee, Mississippi each maintain an AT Act program) and establishes device loan, reutilization, and demonstration center infrastructure. SARA device profiles can be distributed through these state networks as funded AT.

**21st Century Communications and Video Accessibility Act (CVAA) of 2010, Pub. L. 111-260, 47 U.S.C. § 617.**
> Extends accessibility requirements to advanced communications services and user interfaces. Applies to any SARA module that routes communications output (Office Suite Bridge, session recording export) to modern communication platforms.

**World Wide Web Consortium (W3C). Web Content Accessibility Guidelines (WCAG) 2.1, W3C Recommendation (June 2018). WCAG 2.2, W3C Recommendation (October 2023).**
> The international technical standard harmonized into U.S. Section 508 (2017 Refresh) and referenced by DOJ in ADA web enforcement. WCAG 2.1 Level AA is the operative compliance floor for SARA's WPF UI; 2.2 SC 2.5.7 (Dragging Movements) and SC 2.5.8 (Target Size) are directly addressed by SARA's tremor filter and enlarged hit-target design.

---

### State Accessibility & Disability Law — Kentucky · Tennessee · Mississippi

#### Kentucky

**Kentucky Civil Rights Act (KCRA), KRS Chapter 344**, specifically KRS 344.040 (employment) and KRS 344.120 (public accommodations).
> Kentucky's primary anti-discrimination statute, mirroring ADA Title I and Title III protections. Enforced by the Kentucky Commission on Human Rights. Governs any VA-adjacent or private clinical deployment of SARA in the Commonwealth.

**Commonwealth of Kentucky Executive Branch Technology Policies — Digital Accessibility Standard**, referencing WCAG 2.1 AA, issued under authority of the Governor's Office for Electronic and Cabinet Services (GOECS).
> Requires all Commonwealth digital services to meet WCAG 2.1 Level AA. Applies to SARA deployments in Kentucky state-funded VA community care clinics, state university hospital systems, and Medicaid waiver telehealth programs.

**Kentucky Assistive Technology Service (KATS) Network**, established under the AT Act (KRS 194A.160).
> State AT program providing device demonstrations, loans, and reutilization. Distribution pathway for SARA hardware profiles and device configurations to motor-impaired Kentucky veterans outside VAMC direct care.

#### Tennessee

**Tennessee Human Rights Act (THRA), T.C.A. § 4-21-101 et seq.**, specifically § 4-21-401 (places of public accommodation).
> Tennessee's state-level disability non-discrimination statute. Enforcement by the Tennessee Human Rights Commission. Governs any non-federal deployment of SARA within the state, including private OT clinics and community-based outpatient programs.

**Tennessee Technology Accessibility Act, T.C.A. § 4-5-1502; Tennessee Department of Finance and Administration IT Policy 2.00.**
> Requires Tennessee state government IT and web systems to conform to Section 508 and WCAG 2.0 AA. Directly applicable to SARA deployments in Tennessee state-administered Veterans Service programs and TennCare-funded rehabilitation.

**Tennessee Assistive Technology Program (TATN)**, operating under the AT Act via the Tennessee Technology Access Project.
> Provides AT device loan and demonstration services statewide. Primary channel for SARA controller profile distribution to veterans in rural Tennessee telehealth settings.

#### Mississippi

**Mississippi Rights of Persons with Disabilities Act, Miss. Code Ann. § 43-6-1 et seq.**
> State disability rights statute covering employment, public services, and physical access. Establishes the state-level non-discrimination framework applicable to SARA clinical deployments in Mississippi community care and VAMC Jackson-affiliated sites.

**Mississippi Code Ann. § 25-53-191 — Mississippi ITS Accessibility Standard**, administered by the Mississippi Department of Information Technology Services (ITS).
> Requires state agency technology to meet Section 508 accessibility standards. Governs SARA integration with Mississippi state-funded behavioral health and rehabilitation platforms, including Division of Medicaid telerehabilitation programs.

**Mississippi Assistive Technology Program (MATP)**, operated by the University of Southern Mississippi under the AT Act.
> Provides AT device loans, demonstrations, and reutilization services. Distribution infrastructure for SARA input device profiles to motor-impaired veterans in the Mississippi Delta and rural service areas underserved by VAMC direct care.

#### Illinois *(VA Entry Point / Primary Federal Submission Jurisdiction)*

**Illinois Human Rights Act (IHRA), 775 ILCS 5**, specifically Article I (Disability) and Article 5 (Public Accommodations).
> Illinois's primary disability anti-discrimination statute, enforced by the Illinois Department of Human Rights (IDHR). Broader "disability" definition than the federal ADA — covers any determinable physical or mental characteristic. Governs all SARA deployments at Illinois VA sites, affiliated CBOCs, and partner healthcare systems including Hines VA, Jesse Brown VAMC, and Marion VAMC.

**Illinois Information Technology Accessibility Act (IITAA), 30 ILCS 587**, and implementing IITAA Web Standards (v2.0+, aligned to WCAG 2.1 AA).
> Requires all Illinois state agencies and their contractors to make web-based and desktop IT accessible to people with disabilities. Directly applicable to SARA as a clinical software tool deployed in any Illinois state-funded or state-co-administered rehabilitation program alongside VA care.

**Illinois Assistive Technology Program (IATP)**, administered by Equip for Equality under the AT Act.
> Illinois AT Act program providing device demonstrations, short-term loans, and reutilization. Primary in-state distribution channel for SARA input device profiles; IATP's AT Reuse Program is the mechanism for getting adapted controller hardware (HOTAS, accessibility switches) to Illinois veterans outside VAMC direct care catchment.

**Department of Veterans' Affairs — Illinois (IDVA)**, operating under 20 ILCS 2805, coordinating with VHA Network 12 (VISN 12 — Great Lakes).
> Illinois IDVA is the state-level VA entry-point authority. VISN 12 encompasses Jesse Brown VAMC (Chicago), Edward Hines Jr. VA Hospital, Lovell Federal Health Care Center, and Marion VA Medical Center. SARA's federal submission pathway runs through VISN 12 innovation and clinical operations channels. Illinois state claims, benefits navigation, and community care referrals route through IDVA as the coordinating body.



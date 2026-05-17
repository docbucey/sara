# SARA — Symbolic Adaptive Remapping Architecture

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
{"timestamp":"2026-05-17T16:20:01.002Z","device":"HOTAS_T16000M","input":"AXIS_X","raw_value":0.421,"filtered_value":0.210}
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


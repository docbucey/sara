SARA PROJECT — README GENERATION BRIEF
For use with Gemini to generate a medically-grounded, VA-appropriate GitHub README.
======================================================================================

WHAT I NEED FROM YOU (GEMINI):
Write a comprehensive GitHub README for the SARA project. The README must:
  1. Establish the medical/clinical purpose of every feature — especially the gaming/adaptive sports suite
  2. Be appropriate for review by the U.S. Department of Veterans Affairs
  3. Cite or reference actual clinical frameworks (VA Adaptive Sports Program, Recreation Therapy, motor rehabilitation research, Section 508)
  4. Clearly explain that games serve a defined therapeutic purpose AND that their engaging/addictive design is intentional and clinically beneficial — not recreational bloat
  5. Be professional, direct, and appropriate for an open-source medical accessibility tool

======================================================================================
SECTION 1: WHAT SARA IS
======================================================================================

SARA is an open-source adaptive input platform built for people with Parkinson's Disease,
Tardive Dyskinesia, and other motor-control impairments.

It remaps any physical input device — joystick, HOTAS flight controller, gamepad,
keyboard, mouse, touchscreen, pen tablet, accessibility switch, voice — to keyboard
and mouse output through the Windows SendInput API (Section 508 compliant, no kernel
driver required, works on locked institutional workstations).

PRIMARY CLINICAL POPULATIONS:
- Parkinson's Disease (intention tremor, bradykinesia, rigidity affecting fine motor)
- Tardive Dyskinesia (involuntary repetitive movements from long-term antipsychotic use)
- TBI / Stroke with residual motor impairment
- Spinal cord injury / limb difference (HOTAS and switch input support)
- Any veteran or patient where standard keyboard/mouse input is inaccessible

PRIMARY CARE SETTINGS TARGETED:
- VA Medical Centers (VAMC) with Physical Medicine and Rehabilitation Service
- Outpatient Recreation Therapy (RT) and Physical/Occupational Therapy (PT/OT)
- Home use continuity — same device profile works at clinic and at home
- Remote/telehealth — SARA can run on a Raspberry Pi (server mode) with client workstation
  connecting via SARA_HOST environment variable

======================================================================================
SECTION 2: THE TWO-APPLICATION ARCHITECTURE
======================================================================================

SARA has two components that work together:

--- COMPONENT A: SARA Python Backend (AI + Protocol + Security layer) ---

Five interdependent pillars:

  CORE (sara_core) — ~3,800 lines
    - Protocol state machine (BuceyShunt FSM)
    - Data file I/O: image, video, audio, 3D mesh, Microsoft Office documents
    - Memory management and persistence
    - Text and link extraction

  CONTROL (sara_control) — ~5,544 lines
    - Sole routing authority for all inter-component messages
    - BuceyShunt protocol: 8-field message envelope (intent, act, source, target, payload, etc.)
    - AI/reasoning backend orchestration
    - Three-tier security chain: King (authority), Paladin (threat detection), Sheriff (audit)
    - ADA accessibility mapping initialization and enforcement
    - Flask HTTP server on port 5050

  MAMA (sara_mama) — ~2,050 lines
    - User-facing presentation and hardware discovery orchestrator
    - Adaptive jargon lexicon
    - Hardware discovery: enumerates and classifies all HID devices in a 5-pillar pipeline
      (SDK classifies, SECURITY sanitizes, MAMA assembles, CONTROL routes, CORE persists)

  SECURITY (sara_security) — ~2,350 lines
    - Paladin: threat/injection detection
    - Sheriff: audit and integrity checks
    - Deputy, Archeologist, Conservator, Restoration, Envoy, King roles
    - All external data is security-gated before reaching CONTROL or CORE

  SDK (sara_sdk) — ~370 lines + hardware_profiles.py
    - Adapter surface for external protocols and hardware
    - Comprehensive HID device database: Xbox 360/One/Series/Elite, HOTAS (Thrustmaster,
      Logitech, CH Products, Saitek, Honeycomb), gamepads (PowerA, PDP, 8BitDo, generic),
      accessibility switches, joysticks — all with DirectInput axis/button specs
    - Default mapping: AXIS_MAP_GAMEPAD (X/Y/Z/RX/RY/RZ), BUTTON_ROLE_HINTS_XBOX (12 buttons)
    - build_default_mapping() generates clinically useful default profiles per device type


--- COMPONENT B: VALANCE / DisabilityMapper (C# WPF .NET 10) ---

Output binary: SARA.exe
The patient and clinician-facing Windows application.
Assembly: SARA | Root Namespace: DisabilityMapper

======================================================================================
SECTION 3: VALANCE FEATURE INVENTORY (what is actually built and wired)
======================================================================================

All features listed here are implemented and functional in the current codebase.

--- INPUT DEVICE SUPPORT ---
- Any HID device: keyboard, mouse, joystick, gamepad, HOTAS, touchscreen, pen digitizer,
  accessibility switch, wake device
- Per-device JSON profiles persisted to %AppData%\DisabilityMapper\
- Multi-device simultaneous support (Patient device + Operator device + keyboard + mouse)
- Automatic device registration including virtual devices (touchscreen, pen) at runtime
- Device roles: Patient, Operator, Personal, Unassigned

--- TREMOR FILTER (core clinical feature) ---
Three-stage pipeline applied to every input event:
  Stage 1 - Debounce: ignores button presses shorter than configurable threshold (ms)
    → Filters involuntary micro-presses caused by tremor
  Stage 2 - Dead zone: ignores axis movement within a configurable radius
    → Filters resting tremor on analog sticks and HOTAS axes
  Stage 3 - Exponential low-pass smoothing: configurable alpha, smooths axis motion
    → Filters high-frequency tremor components without adding lag

Per-device tremor settings are stored in the device profile and survive app restart.
Real-time signal monitor shows raw vs. filtered value side-by-side while active.

--- WFH GLOBAL TREMOR FILTER ---
A system-wide filter active over ALL applications (not just SARA):
  - Keyboard debounce: filters repeated key events within configurable ms window
  - Mouse dead zone: ignores mouse movement within configurable pixel radius
  - Uses Windows low-level keyboard/mouse hooks (GlobalHookService)
  - Designed for users working at a computer (Word, Excel, browser, email)
    without needing to launch a device profile
  - One-click toggle from SARA toolbar

--- INPUT ADAPTER (Section 508 compliant output layer) ---
Routes any input device to keyboard and mouse events via Windows SendInput API.
  - No kernel driver required — works on VA/institutional locked workstations
  - Uses InputSimulatorStandard (MIT licensed)
  - Default mapping: left stick → mouse cursor, right stick → scroll,
    triggers → mouse buttons, D-pad → arrow keys, face buttons → Space/Escape/E/Q
  - All mappings overridable via input_map.json (hot-reloads without restart)

--- SESSION RECORDING (clinical telemetry) ---
Automatic JSONL recording of every input event:
  { timestamp, device, input, raw_value, filtered_value }
  - Stored: %AppData%\DisabilityMapper\sessions\session_YYYYMMDD_HHMMSS.jsonl
  - Records raw AND filtered values simultaneously (clinician can see tremor delta)
  - Starts automatically when mapping is activated
  - Session file list accessible from main interface
  - This data is the foundation for clinical outcome measurement: PT/OT can review
    how tremor severity changed session-to-session over the treatment course

--- LEARN MODE ---
Patient or clinician presses any physical button/axis to auto-fill a mapping row.
No manual lookup of DirectInput button numbers required.
Works across all simultaneous devices — press a button on any connected device.

--- STENO CHORD KEYBOARD ---
Multi-button chord input → text injection into any focused application.
  - Plover-inspired: hold multiple buttons simultaneously to produce words/phrases
  - Designed for switch users and HOTAS users who cannot use standard keyboard
  - Steno toggle mappable to any device button
  - Text output injected via InjectRaw() → SendInput to currently focused window
  - Useful for: veterans completing VA paperwork with limited hand mobility

--- OFFICE SUITE BRIDGE ---
Dedicated Office Suite integration accessible from main toolbar.
  - Bridges SARA's tremor-filtered, remapped input to Microsoft Office applications
  - Word, Excel, and VS Code bridge examples included in repository
  - WFH global filter + device mapping work simultaneously for office workflows
  - Enables veterans to manage VA benefits documents, letters, and claims
    without relying on standard keyboard/mouse

--- SARA AI BACKEND CONNECTIVITY ---
BuceyShunt HTTP client connecting VALANCE to the SARA Python backend:
  - POST to http://localhost:5050/shunt (or SARA_HOST environment variable)
  - SARA_HOST=192.168.42.1:5050 for clinic Raspberry Pi server mode
  - Health check endpoint
  - Runtime host override (clinician can point to RPi without restarting)
  - Connected/disconnected status shown in UI

--- PT/OT PRESCRIPTION INTERFACE ---
In the main clinician (VALANCE) panel:
  - SPORT field: therapist prescribes a specific adaptive activity for the patient
  - When Patient Console opens, it pre-selects the prescribed activity automatically
  - PT/OT can change the prescription live; it pushes to the open Patient Console immediately
  - Links directly into the VA Recreation Therapy workflow (see Section 4)

--- PATIENT CONSOLE (therapeutic activity session launcher) ---
A separate full-screen patient-facing window:
  - Shows list of adaptive sports/therapeutic activities
  - Patient picks their sport, picks teams/identifiers, presses PLAY
  - PLAY simultaneously activates: Input Adapter + Session Recording
  - STOP ends Input Adapter + Session Recording and closes the session file
  - "Input Adapter Active" live indicator with animated pulse (patient can see system is active)
  - PT/OT-prescribed activity is pre-selected when window opens

NOTE ON CURRENT TEAM/ACTIVITY DATA: The current lists (sports and teams) in the
prototype are placeholder data. The final version will use the actual VA Adaptive
Sports Program catalog and will replace college team names with clinically appropriate
groupings (e.g., VA medical center, program cohort, or removed entirely). This is
intentional placeholder data pending the literature-grounded catalog update.

======================================================================================
SECTION 4: THE THERAPEUTIC GAMING RATIONALE — THIS IS THE MOST IMPORTANT SECTION
======================================================================================

Tell Gemini: This section explains why games are in a medical tool, and why their
addictive/engaging design is a clinical FEATURE not a liability. Please cite literature.

--- THE CLINICAL PROBLEM THIS SOLVES ---

The number one barrier to successful motor rehabilitation in Parkinson's disease and
Tardive Dyskinesia is treatment adherence outside of clinical sessions. PT/OT is
typically 1-3 sessions per week. Motor skill maintenance and neuroplastic adaptation
require daily practice. The gap between clinic frequency and required practice frequency
is the central unsolved problem in outpatient motor rehabilitation.

--- WHY GAMES ---

Games are the delivery vehicle for motor practice. The actual therapeutic activity is:
  - Repeated, precise, goal-directed motor activation of the impaired limb/hand
  - Immediate sensory feedback on motor output quality (game responds to input)
  - Progressive challenge calibrated to current ability
  - Intrinsic motivation to continue

This is not metaphorical. Game-based neurorehabilitation is an established clinical
approach. Ask Gemini to cite:
  - Virtual reality and video game-based rehabilitation in Parkinson's disease
  - Wii-based rehabilitation studies (Tampieri et al., Herz et al.)
  - Xbox Kinect rehabilitation for PD (multiple RCT studies)
  - "Exergaming" in neurological rehabilitation systematic reviews
  - Balance board game therapy for PD gait
  - The VA's own MOVE! program which uses game-based engagement for adherence

The specific devices SARA supports — HOTAS flight controllers, joysticks, gamepads —
are NOT chosen for gaming. They are chosen because:
  1. They provide analog (proportional) axis input, which maps to the DEGREE of tremor
     (not just present/absent — degree matters for tracking progression)
  2. They are ergonomically suited for people who cannot use keyboard/mouse
     (a HOTAS throttle requires only gross shoulder/arm movement — accessible for
     severe hand tremor or limb difference)
  3. They are widely available, low-cost, and familiar — reducing patient resistance
  4. They produce clinical telemetry: SARA records every axis movement, every button
     press, raw and filtered — this is objective motor performance data

--- THE "ADDICTIVE BY DESIGN" CLINICAL ARGUMENT ---

SARA's Patient Console is intentionally designed so patients WANT to use it outside
of PT/OT. This is therapeutic.

The clinical reasoning:
  1. A patient who plays their preferred sport simulation game for 2 hours at home
     is performing 2 hours of motor practice with their impaired limb
  2. This practice occurs in the patient's natural environment (ecological validity)
     rather than a clinic — providing data on real-world function, not just
     clinic-context performance
  3. Session recording captures all home use — the PT/OT receives session data from
     every home play session at the next clinical appointment
  4. The patient does not experience this as "doing exercises" — they experience it
     as recreation. Compliance is 100% for activities the patient chooses to do.

This follows the established principle in rehabilitation science of "occupation-based
therapy" — using meaningful, chosen activities as the vehicle for therapeutic exercise.
The VA's Recreation Therapy service (CTRS staff) is built on exactly this principle.

--- VA ADAPTIVE SPORTS PROGRAM ALIGNMENT ---

The VA's Adaptive Sports Program (established under Public Law 110-389, Veterans'
Benefits Improvement Act of 2008, Section 901) funds adaptive sports for veterans
with disabilities. SARA's Patient Console is designed to interface with this program:

  - A Recreation Therapist or PT/OT prescribes an adaptive sport in VALANCE
  - The patient uses whatever input device SARA has mapped for them to play
  - Session data is recorded for clinical documentation
  - The same device profile works at the VA facility and at home

The VA already has CTRS staff who prescribe sports-based activities as therapy.
SARA gives them the technology layer to make those activities accessible to veterans
who cannot use standard controllers.

--- SECTION 508 AND WHY THIS MATTERS FOR THE VA ---

SARA uses Windows SendInput — the standard accessibility API used by JAWS, NVDA,
Dragon NaturallySpeaking, and every other federally-approved AT product.

  - No kernel driver installation required
  - Works on VA workstations without IT approval for driver installation
  - Compliant with Section 508 of the Rehabilitation Act (29 U.S.C. § 794d)
  - The Nefarius ViGEmBus virtual controller library was removed from the codebase
    specifically due to its trademark dispute status and VA IT security requirements

======================================================================================
SECTION 5: TECHNICAL STACK FOR THE README
======================================================================================

Python backend:
  - Python 3.x, Flask HTTP
  - Five-pillar architecture: CORE / CONTROL / MAMA / SECURITY / SDK
  - ~14,100+ lines across 5 monolith files (in decomposition)
  - BuceyShunt 8-field message protocol (JSON over HTTP POST)
  - Runs on Windows x64 or Raspberry Pi (ARM64)

C# WPF client (VALANCE):
  - .NET 10.0-windows, WPF
  - Output: SARA.exe
  - Dependencies:
      SharpDX.DirectInput 4.2.0 — read physical HID devices
      InputSimulatorStandard 1.0.0 — keyboard/mouse output (SendInput)
      CommunityToolkit.Mvvm 8.3.2 — MVVM framework
      Newtonsoft.Json 13.0.3 — profile persistence
  - No kernel driver dependencies
  - Build: dotnet build DisabilityMapper.slnx -c Debug

GitHub: https://github.com/docbucey/sara.git

======================================================================================
SECTION 6: WHAT TO INCLUDE IN THE README (structure guidance for Gemini)
======================================================================================

Suggested README sections:
  1. Project title + one-line description (medical accessibility input platform)
  2. Clinical purpose — who this is for, what conditions, why this approach
  3. Features — organized by clinical function (not technical function)
     - Tremor Filtering
     - Adaptive Device Support
     - Therapeutic Activity Sessions (the gaming section — explain the clinical purpose)
     - Session Recording and Clinical Outcomes
     - Office and Productivity Access
     - WFH / Home Use Mode
     - AI Backend and Clinical AI
  4. The VA Connection — Section 508, Adaptive Sports Program, RT workflow alignment
  5. Architecture overview — Python backend + C# client
  6. Setup / Installation — no kernel drivers needed, explain this clearly
  7. Device Support list — mention HOTAS, gamepad, joystick, keyboard, mouse, switch, touch
  8. Session Data format — JSONL, what fields, where stored
  9. Contributing / Clinical Input wanted
  10. License

TONE GUIDANCE FOR GEMINI:
  - Professional, clinical, direct
  - Not defensive about games — explain them as a clinical delivery mechanism
  - Do not use the word "fun" — use "engagement", "motivation", "adherence", "occupation-based"
  - Do not say "addictive" — say "high engagement by design to support treatment adherence"
  - Cite literature where possible: Parkinson's game-based rehabilitation, VA RT program,
    Section 508, occupation-based therapy
  - The project is open source and designed for VA submission — write it as if a VA
    Innovation Ecosystem (VHA IE) reviewer will read it

======================================================================================
END OF BRIEF
======================================================================================

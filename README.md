# SARA — Systematic Adaptive Reasoning AI

**A deterministic, plugin-driven, hardware-integrated AI assistant built for accessibility-first human interaction.**

SARA is not an LLM. It is a structured, pillar-based orchestration system designed to run locally, route all intelligence through a formal protocol (BuceyShunt), and adapt to users with disabilities including Parkinson's disease and Tardive Dyskinesia.

---

## Architecture Overview

SARA is built on **five fixed pillars**. All communication flows through the **BuceyShunt protocol** — a universal 8-field envelope that every pillar and the C# front end uses identically.

```
[DisabilityMapper.exe]  ← C# WPF front end (accessibility, input, UI)
         |
    BuceyShunt (HTTP POST → 127.0.0.1:5050/shunt)
         |
[sara_control]          ← Sole routing authority. Nothing bypasses CONTROL.
    /    |    \
 CORE  MAMA  SECURITY  SDK
```

**Dependency direction (one-way, no backflow):**
`SDK / MAMA / SECURITY → CONTROL → CORE`

---

## Pillars

| Pillar | Folder | Role |
|--------|--------|------|
| **CONTROL** | `sara_control/` | Routing authority, FSM, session, jobs, identity, learning |
| **CORE** | `sara_core/` | Engine only — file I/O, NBS persistence, proto-lingua, media, scene |
| **MAMA** | `sara_mama/` | Presentation only — biometrics, UX adaptation, jargon, ledger |
| **SECURITY** | `sara_security/` | Gating — Paladin, Sheriff, Deputy, King, Conservator, Envoy |
| **SDK** | `sara_sdk/` | Adapter surface — AI models, devices, external protocols |

---

## Front End: DisabilityMapper

Located in `DisabilityMapper/`. A C# WPF application built specifically for users with physical disabilities.

**Key services:**
- `TremorFilterService.cs` — Real-time tremor filtering for Parkinson's/TD
- `StenoChordEngine.cs` — Steno keyboard input for reduced-motion users
- `RawInputService.cs` — Windows Raw Input + WM_POINTER hooks
- `HidService.cs` — Gamepad, joystick, mouse, touch device enumeration
- `ProfileStore.cs` — Per-user device profile persistence
- `BuceyShunt` (in `SaraControlClient.cs`) — Sends shunt envelopes to CONTROL over localhost HTTP

**Windows in the app:**
- `MainWindow` — Primary cockpit UI
- `StenoKeyboardWindow` — Steno input overlay
- `OfficeSuiteWindow` — Office task launcher
- `AssetDeckWindow` — Asset/media deck
- `SaraFallbackShellWindow` — Fallback shell when CONTROL is offline

---

## BuceyShunt Protocol

Every message in SARA — internal pillar-to-pillar and C# to Python — uses the same envelope:

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

**ACT codes:** `00` = route, `01` = validate/normalize, `10` = build/office, `11` = dispatch/audit

The HTTP bridge (`sara_control_http.py`) listens on `127.0.0.1:5050/shunt` and feeds envelopes directly into `control_shunt_entrypoint()`. The C# `BuceyShunt` class speaks this same protocol — there is no separate bridge layer.

---

## ADA / Accessibility Compliance

SARA is designed from the ground up for users with disabilities:

- **Biometrics are always-on** — tremor detection, baseline calibration, progressive disability profiling (MAMA → `biometrics.py`)
- **ADA mapping is enforced by CONTROL** — `ada_accessibility_mapping_initialization_enforcement`
- **SLM-3 (Human Profile)** — The ADA/interaction engine manages user context, accessibility, and input shaping
- **Phase 1 ADA recovery** passed all four test vectors: constrained readability, denied recovery guidance, schema fail recovery, boundary blocked safety (see `ada_phase1_recovery_report.txt`)
- **DisabilityMapper** provides physical input layer: raw input hooks, tremor filtering, steno chords, device profiles

---

## Running SARA

1. **Start the Python backend:**
   ```
   SARA_RUN.bat
   ```
   or
   ```
   python sara_control/sara_control_http.py
   ```
   CONTROL will be available at `http://127.0.0.1:5050`

2. **Launch the front end:**
   Build and run `DisabilityMapper/DisabilityMapper/DisabilityMapper.csproj` (.NET 8, WPF)
   ```
   dotnet run --project DisabilityMapper/DisabilityMapper/DisabilityMapper.csproj
   ```

3. **Verify the connection:**
   DisabilityMapper will call `GET /health` on startup. The status bar will show CONTROL as connected.

---

## Key Spec Documents

| File | Contents |
|------|----------|
| `SARA_MONOLITH_DECOMPOSITION.md` | Full architectural decomposition map — what each module contains, what leaked where, proposed rebuild structure |
| `SARA_SYSTEM_ARCHITECTURE_SPEC.md` | PLM/pillar spec, data flow rules |
| `saragen0.5aspec.md` | Gen0.5a OS-native plugin and 3LM architecture |
| `BIOMETRIC_PROTOCOL_SPEC.md` | Tremor detection, ADA biometric protocol |
| `SARA_INSTALLER_SPEC.md` | Build, package, and installer spec for DisabilityMapper.exe + Python backend |
| `ada_phase1_recovery_report.txt` | ADA compliance test results |
| `sara_architecture_log.md` | Full architectural lineage and design decisions |

---

## Requirements

**Python backend:** See `requirements.txt`

**C# front end:** .NET 8, Windows, WPF — build with Visual Studio or `dotnet build`

---

## Repository Structure

```
SARA/
├── sara_control/       # CONTROL pillar (routing authority)
├── sara_core/          # CORE pillar (engine, I/O)
├── sara_mama/          # MAMA pillar (presentation, biometrics)
├── sara_security/      # SECURITY pillar (gating, audit)
├── sara_sdk/           # SDK pillar (adapters, AI, devices)
├── sara_common/        # Shared utilities
├── DisabilityMapper/   # C# WPF front end
└── [spec docs]         # Architecture, ADA, installer specs
```

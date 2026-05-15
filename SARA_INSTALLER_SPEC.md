# SARA Installer Specification

## Overview

Single installer EXE that deploys SARA to any Windows laptop (IdeaPad, ThinkPad, any).
The C# front end (DisabilityMapper) is the user-facing application.
The Python backend (pillars) runs as a background service.
No Ollama. No cloud dependency. Fully local.

---

## 1. Installer Package Contents

```
SARA_Installer.exe
├── DisabilityMapper.exe          ← C# WPF front end (published self-contained)
├── sara_backend/                 ← Python SARA pillars (all 5 + common)
│   ├── sara_common/
│   ├── sara_core/
│   ├── sara_control/
│   ├── sara_mama/
│   ├── sara_security/
│   ├── sara_sdk/
│   └── requirements.txt
├── python_embedded/              ← Embedded Python 3.11 (no system install needed)
│   ├── python.exe
│   ├── python311.dll
│   ├── Lib/
│   └── Scripts/
├── models/                       ← Pre-bundled GGUF model
│   └── (selected model .gguf)
└── installer_assets/
    ├── sara_icon.ico
    └── first_run_config.json
```

### Build Notes

- **C# front end**: `dotnet publish -c Release -r win-x64 --self-contained`
  Self-contained means no .NET runtime install needed on target.
- **Python embedded**: Use python.org "embeddable package" (ZIP, ~25MB).
  No system Python install needed. Ships with the installer.
- **Model**: Default bundle = TinyLlama 1.1B Q4_K_M (~670MB).
  User can swap for larger model later by dropping .gguf into models/.
- **Installer framework**: Inno Setup or WiX (both free, produce single EXE).

---

## 2. Install Flow

### Step 1: Choose Install Location
- Default: `C:\SARA\`
- Portable option: any folder (thumb drive `E:\SARA\` works)
- Creates folder structure:

```
C:\SARA\
├── DisabilityMapper.exe
├── sara_backend/
├── python/                    ← extracted embedded Python
├── models/
├── data/                      ← NBS, profiles, session logs
│   ├── identity/
│   │   ├── user/
│   │   ├── sara/
│   │   └── machine/
│   ├── persona/
│   ├── sessions/
│   └── nbs/
└── SARA.bat                   ← launches both backend + frontend
```

### Step 2: Install Dependencies
- Extracts embedded Python
- Runs: `python\python.exe -m pip install -r sara_backend\requirements.txt --target python\Lib\site-packages`
- All deps go into the local Python, nothing touches system

### Step 3: Extract Model
- Copies bundled .gguf into `models/`
- If no model bundled (slim installer), shows download dialog with size estimates

### Step 4: First-Run Wizard
→ See Section 3

### Step 5: Create Shortcuts
- Desktop shortcut → `SARA.bat` (or direct to DisabilityMapper.exe)
- Start Menu → SARA folder
- Optional: Start with Windows (background service)

---

## 3. First-Run Wizard (C# WPF)

Launches automatically on first run. Keyboard-navigable throughout.
Simple screens, large text, high contrast. Fatigue-aware (no time pressure).

### Screen 1: Welcome
```
Welcome to SARA.

SARA is your personal assistant. She adapts to you.
Everything stays on this computer — nothing is sent anywhere.

[Next →]
```

### Screen 2: Name Your SARA
```
What would you like to call her?

[ SARA          ]  ← text field, pre-filled with "SARA"

She'll remember this name. You can change it anytime.

[← Back]  [Next →]
```
- Writes to: `data/identity/sara/sara_profile_gen0_1.0_nbs.json`
  - Sets `identity.name` = user's choice
  - Sets `identity.persona` = "protocol_droid_female"

### Screen 3: Your Name
```
What's your name?

[ (empty)       ]  ← text field

This is how she'll address you.

[← Back]  [Next →]
```
- Writes to: `data/identity/user/doc_bucey_profile_gen0_1.0_nbs.json`
  - Sets `identity.display_name` = user's input

### Screen 4: Device Discovery
```
Discovering your devices...

✓ Keyboard:    HID\VID_046D&PID_C534  (Logitech K540)
✓ Mouse:       HID\VID_046D&PID_C52B  (Logitech M510)
✓ Joystick:    HID\VID_045E&PID_02FF  (Xbox Controller)
✓ Touchscreen: VIRTUAL_TOUCH

[Refresh]  [Next →]
```
- Uses `HidService.EnumerateDevices()` (already built in DisabilityMapper)
- Auto-creates a `DeviceProfile` for each discovered device
- Writes to: `data/identity/machine/pc_host_profile_gen0_1.0_nbs.json`
  - Records: hostname, OS version, RAM, CPU cores, GPU (if any), discovered HID devices

### Screen 5: Accessibility Check
```
Would you like SARA to adapt to your input style?

SARA can learn how you type and move, then adjust
to reduce strain. This helps with tremors, fatigue,
or any motor difficulty.

( • ) Yes, adapt to me        ← default
(   ) No, use standard settings

[← Back]  [Next →]
```
- If yes: enables constant biometrics in MAMA
- Sets `data/identity/user/` → `accessibility.adaptation_enabled: true`
- Tremor filter starts at conservative defaults (debounce 80ms, deadzone 0.15)
- SARA will refine these through use (biometric learning via LearnManager)

### Screen 6: AI Model Check
```
Checking AI capability...

✓ Model found: TinyLlama 1.1B (670 MB)
  Speed: ~15 tokens/sec on this hardware
  Quality: Basic conversation, document drafting

Want to download a better model? (optional, needs internet)
  [ ] Phi-3 Mini 3.8B (2.3 GB) — recommended for 8GB+ RAM
  [ ] Keep current model

[← Back]  [Finish →]
```
- Tests model load speed with a short benchmark
- Estimates tokens/sec for the user

### Screen 7: Done
```
                    ✓

  (Sara's name) is ready.

  She'll learn your rhythm as you use her.
  The more you use her, the better she gets.

  [Launch SARA]
```

---

## 4. Runtime Architecture (Installed)

```
DisabilityMapper.exe (C# WPF)
    │
    │ ← Bucey Shunt JSON envelopes over HTTP
    │    POST http://127.0.0.1:5050/shunt
    │
    ▼
python\python.exe sara_backend\sara_control\server_con.py --http
    │
    ├── CONTROL (FSM routing, AMIP dispatch, SHI governor)
    ├── CORE (NBS, file I/O, proto_lingua)
    ├── MAMA (biometrics, UX adaptation, presentation)
    ├── SECURITY (Paladin gating, trust, audit)
    └── SDK (local LLM, steno, macros, tremor filter, HID)
            │
            └── llama-cpp-python → models/*.gguf (direct GGUF, no Ollama)
```

### Startup Sequence
1. `DisabilityMapper.exe` launches
2. Starts Python backend as child process (hidden console)
   - `python\python.exe sara_backend\sara_control\server_con.py --http`
3. Polls `http://127.0.0.1:5050/health` until `control_loaded: true`
4. Status bar shows "SARA ready" (green) or "Starting..." (yellow)
5. On exit: kills Python child process

### The C# Side Manages the Backend Process
```csharp
// In App.xaml.cs or a startup service:
Process.Start(new ProcessStartInfo
{
    FileName = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "python", "python.exe"),
    Arguments = "sara_backend\\sara_control\\server_con.py --http",
    WorkingDirectory = AppDomain.CurrentDomain.BaseDirectory,
    CreateNoWindow = true,
    UseShellExecute = false,
});
```

---

## 5. Profile Discovery (SARA Learns the Machine)

On every launch, SARA auto-discovers and updates:

### Machine Profile (`pc_host_profile_gen0_1.0_nbs.json`)
```json
{
  "hostname": "DESKTOP-ABC123",
  "os": "Windows 10 22H2",
  "cpu": "Intel Core i5-6200U",
  "cores": 4,
  "ram_gb": 8,
  "gpu": "Intel HD 520",
  "has_dedicated_gpu": false,
  "storage_free_gb": 45.2,
  "hid_devices": [
    {"guid": "HID\\VID_046D...", "name": "Logitech K540", "type": "Keyboard"},
    {"guid": "HID\\VID_045E...", "name": "Xbox Controller", "type": "Gamepad"}
  ],
  "performance_class": "low",
  "updated_at": "2026-05-12T15:00:00Z"
}
```

### SARA Profile (`sara_profile_gen0_1.0_nbs.json`)
```json
{
  "identity": {
    "name": "Rosie",
    "persona": "protocol_droid_female",
    "language": "en-US"
  },
  "instance_id": "a3f7c...",
  "created_at": "2026-05-12T14:30:00Z",
  "sessions_total": 0,
  "model_info": {
    "name": "tinyllama-1.1b-chat-v1.0.Q4_K_M",
    "path": "models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
    "size_mb": 670,
    "tokens_per_sec": 15.2
  }
}
```

### User Profile (`doc_bucey_profile_gen0_1.0_nbs.json`)
```json
{
  "identity": {
    "display_name": "Chris",
    "created_at": "2026-05-12T14:30:00Z"
  },
  "accessibility": {
    "adaptation_enabled": true,
    "tremor_filter": {
      "debounce_ms": 80,
      "axis_dead_zone": 0.15,
      "axis_smooth_alpha": 0.3
    },
    "fatigue_tracking": true,
    "last_fatigue_color": "green"
  },
  "preferences": {
    "font_size": "large",
    "high_contrast": false,
    "keyboard_only": true
  }
}
```

---

## 6. Installer Build Options

### Option A: Inno Setup (Recommended — simplest)
- Free, single EXE output
- Built-in Pascal scripting for first-run logic
- Handles shortcuts, uninstaller, registry
- ~10MB overhead

### Option B: WiX Toolset
- MSI output (enterprise/IT-friendly)
- More complex but better for managed deployments
- C# custom actions possible

### Option C: Self-Extracting Archive + Launcher
- Simplest to build: 7-Zip SFX + SARA_SETUP.bat
- No uninstaller, no Start Menu, but works immediately from thumb drive
- Good for brother's machine / quick deploys

### Recommended Path
- **For you to test**: Option C (self-extracting, fastest to build)
- **For distribution**: Option A (Inno Setup, polished)

---

## 7. Thumb Drive Deployment (Your Brother)

Specific to the immediate use case:

1. You build + test on your machine
2. Run `build_portable.bat` → creates `SARA_PORTABLE/`
3. `SARA_PORTABLE/` contains everything including embedded Python + model
4. Copy to thumb drive
5. On brother's IdeaPad:
   - Plug in thumb drive
   - Run `SARA_SETUP.bat` (installs venv, ~2 min)
   - Run `SARA_RUN.bat` or launch DisabilityMapper.exe
   - First-Run Wizard appears
   - He names his SARA, devices discovered, done
6. After first run: can copy from thumb to local `C:\SARA\` if desired

Total size estimate:
- Python embedded:  ~25 MB
- SARA code:        ~5 MB  
- Dependencies:     ~40 MB
- TinyLlama model:  ~670 MB
- DisabilityMapper: ~30 MB (self-contained .NET)
- **Total: ~770 MB** (fits on any thumb drive)

With Phi-3 instead: ~2.4 GB total. Still fits a 4GB+ drive.

---

## 8. What Needs Building (Ordered)

| # | Task | Status |
|---|------|--------|
| 1 | Finish C# UIs in Maya → Godot → remap into MAMA | **You (in progress)** |
| 2 | C# backend process launcher (start/stop Python) | Spec'd above (Section 4) |
| 3 | First-Run Wizard WPF screens | Spec'd above (Section 3) |
| 4 | Machine discovery (CPU/RAM/GPU/HID auto-detect) | HID done, system info needs ~20 lines C# |
| 5 | Profile creation on first run | Python side exists (`identity_con.py`), C# calls via Bucey Shunt |
| 6 | Inno Setup script or self-extracting archive | After testing |
| 7 | `dotnet publish` self-contained build | One command |

---

## 9. Model Recommendations by Hardware

| Machine | RAM | Model | Size | Speed (est.) |
|---------|-----|-------|------|-------------|
| Old IdeaPad (i3/i5, no GPU) | 4 GB | TinyLlama 1.1B Q4 | 670 MB | ~8 tok/s |
| Old IdeaPad (i5, no GPU) | 8 GB | Phi-3 Mini 3.8B Q4 | 2.3 GB | ~5 tok/s |
| Your machine (better specs) | 16+ GB | Llama3 8B Q4 (from Ollama cache) | 4.7 GB | ~10 tok/s |

All CPU-only. No GPU required. `llama-cpp-python` handles this natively.

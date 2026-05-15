Language‑agnostic spec sheet for Copilot auto‑build

Overview
Build a localhost test harness that orchestrates isolated worker processes to run the full protocol suite on selected files. The harness must be language‑agnostic so Copilot can generate code in any implementation language. It executes a two‑phase BuceyShunt protocol (Text → Binary), runs the ten canonical checks per attempt, batches 10 repeats per file to reach 100 attempts per protocol target, and writes deterministic, atomic pass/fail artifacts to the exact Markdown summary files you specified.

Core components (abstracted)
- Local HTTP server — listens only on 127.0.0.1; exposes control/status endpoints and serves a minimal static UI for local file selection.
- Orchestrator — validates environment, creates run_id, schedules batches, aggregates results, writes markers and summaries.
- Worker runner — invoked as a separate process for each attempt; performs the 10 canonical tests and returns structured JSON results to the orchestrator.
- Docstring stripper — separate utility that performs an AST rewrite (or equivalent) to remove docstrings and write reversible working copies.
- Storage layout — work/<run_id>/original/, work/<run_id>/stripped/, artifacts/<run_id>/binary/, logs/<run_id>.ndjson, work/<run_id>/markers/.
- Event logger — newline‑delimited JSON (NDJSON) with ts, trace_id, event_type, actor, payload.
- Marker writer — atomic temp→replace writes for per‑run markers and atomic append for the two global .md files at the exact paths you provided.

API contract (endpoints and payloads)
- POST /api/tests/start — payload: { file_paths: [string], run_id?: string, protocols?: [string], keep_artifacts?: bool } → returns { run_id }.
- GET /api/tests/{run_id}/status — returns phase, attempts, successes, raw_pass_rate, pass_rate_int, progress.
- GET /api/tests/{run_id}/log — streams NDJSON events for the run.
- POST /api/tests/{run_id}/control — payload: { action: "pause"|"resume"|"abort" }.
- / — static local UI for file selection and live progress (served only on localhost).

Test flow and orchestration rules
- Startup checks — verify write access to both global .md files; fail fast if not writable.
- Protocol discovery — inspect each file to enumerate protocols and test functions; run every discovered protocol.
- Phase A (Text) — for each file/protocol: schedule batches of 10 attempts; each attempt runs the 10 canonical text checks; continue until 100 attempts attempted per protocol.
- Docstring removal — create work/<run_id>/stripped/ via AST rewrite; preserve originals; log the transform event; wait for confirmation to proceed.
- Phase B (Binary) — repeat the attempt pattern on stripped copies; perform binary checks and checksum validation.
- Aggregation — compute raw_pass_rate = successes/attempts * 100, pass_rate_int = round(raw_pass_rate); apply integer thresholds.
- Artifacts — atomically write per‑run marker file and append a single‑line summary to the appropriate global .md.
- Cleanup — delete temporary files unless keep_artifacts is true.

The ten canonical tests (run in every attempt)
- Heaviside Step Density Check — ratio of valid characters vs noise; threshold for text phase.
- Line‑End Consistency — detect mixed CR/LF; fail on mixed signals.
- Heaviside Boundary Scan — validate first and last 10% of file for structural integrity.
- Symbol Frequency Analysis — flag excessive high‑ASCII or control codes.
- Pattern Repeat Validation — ensure required headers/delimiters are present.
- MSB Highside Audit — inspect most significant bit behavior in binary phase.
- Bit‑Transition Velocity — measure bit flip frequency; flag impossible patterns.
- Checksum / Heaviside Parity — compute 16‑bit checksum and compare to expected step value.
- Bit‑Weight Balance — validate 1s vs 0s fall within allowed window.
- Distant‑End Loopback — simulate lossy transmission and re‑alignment; require ≥98% recovery.

Thresholds and numeric rules (exact)
- Text phase (strict): integer percent must be between 85 and 98 inclusive.
- Binary phase (strict): integer percent must be ≥ 98.
- Rule-of-thumb fallback: if strict gate fails, apply delta=3% with a hard cap of +/-5%.
- Fallback text band: [85-delta, 98+delta], fallback binary floor: [98-delta].
- Computation: raw_pass_rate = successes/attempts * 100 (float); pass_rate_int = round(raw_pass_rate) (integer). The integer is authoritative for gating; raw value is logged for audit.
- Attempts: batch 10 repeats per file; continue batches until 100 attempts per protocol target are attempted.
- Strictness: use integer rounding only; no fractional comparisons.

Artifact formats (exact examples)
- Per‑run marker work/<run_id>/markers/<run_id>_success_<ts>.md or _fail_<ts>.md with YAML header:
---
run_id: 20260310-001
trace_id: abc123
status: PASS
pass_rate: 98
phase: text
attempts: 100
successes: 98
raw_pass_rate: 98.00
ts: 2026-03-10T15:30:00-05:00
---
Summary: Text shunt header found in output file. See logs/20260310-001.ndjson for details.


- Global single‑line append (atomic):
2026-03-10 15:30 | run_id=20260310-001 | PASS | 98% | phase=text


- NDJSON event (one line per event):
{"ts":"2026-03-10T15:29:01Z","trace_id":"abc123","event_type":"test.attempt","actor":"worker-3","payload":{"file":"mod.py","protocol":"shunt","attempt":42}}


- Binary artifact checksums — record SHA256 in NDJSON event artifact.checksum.

Concurrency, isolation, and safety
- Orchestrator concurrency — thread pool for scheduling; process pool for workers; default concurrency min(8, cpu_count()), configurable.
- Worker isolation — each attempt runs in a separate process with a working directory under work/<run_id>/worker_<n>/; enforce per‑worker timeout (configurable) and resource limits.
- No in‑process execution — server process must never import or execute user code directly.
- Local binding & auth — bind to 127.0.0.1 only and require X-Api-Token header for state‑changing endpoints.
- Atomic writes — use temp file → atomic rename for marker files and single‑line append with exclusive lock for global summaries.
- Permissions check — verify write access to the two global .md files before starting a run.

Implementation guidance (language‑agnostic)
- Use standard libraries for subprocess control, file I/O, JSON, hashing, and AST parsing (or equivalent parsing tools in chosen language).
- Worker invocation pattern: spawn a new process with a job descriptor (JSON) and capture stdout/stderr; parse worker JSON output into NDJSON events.
- Docstring stripper: perform a safe parse/transform/write cycle; preserve originals and log the transformation event.
- Provide a single configuration file for API_TOKEN, concurrency, worker_timeout, paths (global .md locations), and keep_artifacts default.
- Include a small sample job and sample NDJSON + marker files for format validation before running on the full codebase.

Acceptance criteria (must pass)
- Server binds to 127.0.0.1 and enforces token auth.
- Sample job produces logs/<run_id>.ndjson, per‑run marker, and appended global summary at the exact paths.
- Marker writes and global appends are atomic.
- Worker subprocesses run in isolated working directories; server never imports user code.
- Integer threshold logic behaves as specified and is logged with both raw and integer values.
- Docstring stripper preserves originals and writes stripped copies used only for binary phase.

- All ten canonical tests are implemented and run in every attempt; results are logged in NDJSON.
- Concurrency is implemented with configurable limits; system behaves correctly under load.
- Cleanup logic deletes temporary files unless keep_artifacts is true.
Local Machine Test Log File
Path:  
C:\Users\mdbuc\Documents\coding projects\MODLES\test\distand end\philo.mak

Purpose:  
Defines the local machine side of the test harness.
This file contains the rules for:

Local machine logging

JSON output structure

Error formatting

PASS/FAIL logic

Output size limits

VS Code–friendly parsing

Local‑end status reporting

Preventing runaway output
Distant End Test Log File
Path:  
C:\Users\mdbuc\Documents\coding projects\MODLES\test\distand end\machine.mak

Purpose:  
Defines the distant end side of the test harness.
This file contains the rules for:

Transmission integrity

Minimal, terminal‑safe logging

Distant‑end PASS/FAIL logic

Output size limits

Distant‑end JSON structure

Mirroring the local machine side

Preventing terminal overload
Master Aggregator Rules File
Path:  
C:\Users\mdbuc\Documents\coding projects\MODLES\test\master.mak

Purpose:  
Defines how to merge:

Local machine results (philo.mak)

Distant end results (machine.mak)

Into a single master JSON that the harness can walk safely.

This file contains the rules for:

Combining both sides

Final PASS/FAIL logic

Handling UNKNOWN states

Ensuring bounded, structured output

Preventing runaway aggregation
-------------------------------------------
aditional specs will be added below this line as project evolves and adtional test are added  donot remove when it is done any of the original code when the updates are added
-------------------------------------------------
-------------------------------------------------

PRE-GENERATION TEST INTAKE GATE (MANDATORY)
-------------------------------------------------

Before generating or implementing any new test, the harness process MUST run an intake review for that test.

Required intake questions (must be answered in writing for each new test):
1. What is this test for?
2. What failure mode does it detect that current tests do not?
3. How does it improve the harness (accuracy, false-positive reduction, stability, safety, speed, observability)?
4. What metric and threshold does it introduce or change?
5. Is this test redundant with an existing test? If not, why not?

Required intake fields per test:
- test_name
- purpose
- failure_mode_targeted
- improvement_category
- measurable_metric
- threshold_rule
- expected_impact
- overlap_with_existing_tests
- execution_phase (pre-Heaviside / canonical / post-analysis)

Generation rule:
- If any required intake field is missing, generation for that test is blocked.
- Only tests with complete intake and explicit measurable impact may be added.

Audit rule:
- Intake records must be logged in NDJSON as event_type=test.intake.review.
- Event payload must include test_name, decision (approved/rejected), and rationale.

Outcome rule:
- New tests are added only if they provide unique detection value or measurable improvement to harness quality.

EARLY-DATA PIONEER TEST SUITE (14 × 10 TESTS)
-------------------------------------------------

These 14 pioneers represent the foundational pre-Heaviside validation layers.  
Each pioneer contributed a set of 10 tests.  
All 14×10 tests must run BEFORE the Heaviside-based canonical tests.  
Execution order: bottom-to-top in, top-to-bottom out.  
All thresholds follow the absolute two-decimal Heaviside gating rules.

PIONEER 1 — Nathan Stubblefield (Induction & Grounding)
1. Wireless Bleed
2. Grounding Check
3. Soil Resistance
4. Distance Battery
5. Inductive Header
6. Parallel Logic
7. Crosstalk Rejection
8. Signal-to-Earth
9. Atmospheric Noise
10. Proximity Trigger

PIONEER 2 — William Thomson / Lord Kelvin (The Speed of Signal)
1. Kelvin Scale
2. Arrival Curve
3. The Siphon Recorder
4. Atlantic Cable Delay
5. Mirror Galvanometer
6. Submarine Resistance
7. Thermal Noise
8. Electrometer Test
9. Standard Volt
10. Tide Prediction

PIONEER 3 — James Clerk Maxwell (The Field Equations)
1. Displacement Current
2. Flux Density
3. Vorticity Check
4. Aether Drift
5. Maxwell’s Demon
6. Field Uniformity
7. Light-Speed Cap
8. Electromagnetic Pulse (EMP)
9. Scalar Potential
10. The Greatest Synthesis

PIONEER 4 — Michael Faraday (The Shield & The Coil)
1. Faraday Cage
2. Lines of Force
3. Electrolysis Test
4. Rotary Induction
5. Dielectric Constant
6. The Disk Dynamo
7. Spark Gap
8. Magnetic North
9. Faraday Effect
10. Constant Charge

PIONEER 5 — Heinrich Hertz (The Frequency)
1. Hertzian Wave
2. Radio Gap
3. Photoelectric Effect
4. Oscillator Sync
5. Reflector Test
6. Wave Length
7. Dipole Check
8. Resonance Peak
9. The Spark Test
10. Electromagnetic Speed

PIONEER 6 — Nikola Tesla (The Resonant Energy)
1. The Tesla Coil
2. Polyphase Logic
3. Resonant Frequency
4. Wireless Power
5. The Wardenclyffe Fail
6. Alternating Current (AC)
7. The Earthquake Machine
8. Ozone Scent
9. High-Frequency Shield
10. The Teleforce

PIONEER 7 — Charles Proteus Steinmetz (Hysteresis & Lag)
1. Hysteresis Loop
2. Magnetic Saturation
3. Phasor Math
4. The Lightning Bolt
5. The Wizard’s Impedance
6. Transient Response
7. Complex Numbers
8. The Forced Wave
9. Transformer Ratio
10. The Circuit Breaker

PIONEER 8 — Gustav Kirchhoff (Current & Loops)
1. Current Law (KCL)
2. Voltage Law (KVL)
3. Node Analysis
4. Mesh Check
5. Thermal Resistance
6. Black-Body Radiation
7. Spectroscopy Test
7. Bridge Circuit
9. The Junction Test
10. The Closed Loop

PIONEER 9 — Georg Ohm (The Resistance)
1. Resistance Test (R)
2. Voltage Check (V)
3. Current Check (I)
4. V=IR Validation
5. Conductivity
6. Resistor Color Code
7. Short Circuit
8. Open Circuit
9. Power Dissipation
10. Specific Resistance

PIONEER 10 — Edwin Hall (The Drift)
1. The Hall Voltage
2. Magnetic Bias
3. Lateral Drift
4. Carrier Density
5. The Hall Sensor
6. Semiconductor Check
7. Electron Mobility
8. Field Reversal
9. Proton Flow
10. The Hall Effect Fail

PIONEER 11 — John Ambrose Fleming (The Valve)
1. The Vacuum Tube
2. The Diode Gate
3. The Right-Hand Rule
4. Thermionic Emission
5. Rectification
6. The Valve Oscillation
7. Anode/Cathode
8. Grid Bias
9. The Fleming Left-Hand
10. Filament Burn-out

PIONEER 12 — Hendrik Lorentz (The Transformation)
1. Lorentz Force
2. Time Dilation
3. Length Contraction
4. Transformation Check
5. Invariant Logic
6. The Electron Radius
7. Local Time
8. Reciprocity
9. The Lorentz Factor
10. Ether Wind

PIONEER 13 — Walther Nernst (The Third Law)
1. The Third Law
2. Nernst Equation
3. Equilibrium
4. Heat Theorem
5. The Lamp Test
6. Chemical Potential
7. Galvanic Cell
8. Diffusion
9. The Nernst Bridge
10. Solubility

PIONEER 14 — Max Planck (The Constant)
1. Planck’s Constant (h)
2. Quanta Check
3. Black-Body Limit
4. Energy Levels
5. The Radiation Law
6. Quantum Jump
7. Wave-Particle Duality
8. The Constant Ratio
9. Probability Cloud
10. The Absolute Unit

-------------------------------------------------
PASSING GAUNTLET RULES
-------------------------------------------------
- TEXT PHASE (Tests 1–70): If any pioneer’s average < 85%, mark “FAILED TEXT – [NAME] VIOLATION”.
- BINARY PHASE (Tests 71–140): If any pioneer’s average < 98%, mark “FAILED BINARY – [NAME] INSTABILITY”.
- HEAVISIDE GATE: Only if all 14 pioneers pass does the Heaviside Step flip to 1 (PASS).

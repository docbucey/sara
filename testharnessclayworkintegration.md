---

## 🔧 1. BACKEND MANIFEST (`backend_manifest.json`)

This manifest tells VS Code and any AI agent exactly what backend tools exist and how to call them.

**Purpose:**
- Enumerates all backend modules/tools
- Specifies invocation method, arguments, and expected outputs
- Enables discoverability and automation for VS Code and AI agents

**Example Structure:**
```json
{
    "tools": [
        {
            "name": "harness_runner",
            "entry_point": "scripts/run.ps1",
            "args": ["--mode", "gauntlet"],
            "description": "Run full harness in Gauntlet mode"
        },
        {
            "name": "docstring_stripper",
            "entry_point": "scripts/strip_docstrings.py",
            "args": [],
            "description": "Remove docstrings from source files"
        }
    ]
}
```

---

## 🔧 2. DISPATCHER API (`backend_dispatcher.py` contract)

This is the glue layer between VS Code, the AI, and the harness.

**Dispatcher accepts:**
- Structured JSON commands specifying tool, arguments, and context

**Dispatcher returns:**
- Structured JSON results, including NDJSON event logs and summary outputs

**Dispatcher responsibilities:**
- Route commands to correct backend module
- Spawn worker processes
- Enforce isolation (no in-process user code)
- Write NDJSON events
- Return structured results for AI consumption

**Spec compliance:**
The server never imports user code and only communicates via JSON, ensuring deterministic, auditable operation.

---

## 🔧 3. VS CODE TASK DEFINITIONS (`tasks.json`)

This enables running the harness and related tools from VS Code with one command.

**Capabilities:**
- Full Gauntlet mode
- Fast Screen mode
- Docstring stripper
All callable from VS Code’s command palette.

**Example task definition:**
```json
{
    "label": "Run Full Gauntlet",
    "type": "shell",
    "command": "powershell",
    "args": [
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        "${workspaceFolder}/scripts/run.ps1",
        "--mode",
        "gauntlet"
    ]
}
```

---

## 🔧 4. INTEGRATION CONTRACT FOR SARA GEN1

This defines how SARA Gen1 interacts with the harness.

**SARA → Harness contract:**
- SARA Gen1 must send structured requests (JSON) to the harness entry point, specifying scenario, phase, and required parameters.

**Harness → SARA contract:**
- Harness returns the summary schema (see above), marker file, and NDJSON event log.

**SARA’s required behavior:**
- If overall_status == PASS → accept
- If pioneer_failures → regenerate structurally
- If canonical_failures → regenerate semantically
- If text passes but binary fails → regenerate for binary stability
- If fallback band → refine
- If catastrophic failure → full rewrite
This is the AI regeneration decision tree previously approved.

**SARA must never:**
- Bypass the harness
- Modify thresholds
- Skip pioneers
- Write to global .md files
- Run user code in-process

This preserves the deterministic, micro-AI architecture and ensures all results are validated and auditable.
---

## 🔶 1. NDJSON EVENT SCHEMA

(This is the atomic event format your orchestrator and workers already use.)

**Schema:**
```json
{
    "ts": "ISO8601 timestamp",
    "trace_id": "string",
    "event_type": "string",
    "actor": "string",
    "payload": {
        "file": "string",
        "protocol": "string",
        "attempt": "integer",
        "phase": "text|binary",
        "test_name": "string",
        "status": "PASS|FAIL",
        "score_raw": "float",
        "score_int": "integer",
        "checksum_sha256": "string",
        "details": "object"
    }
}
```

**Citations from your spec:**
- “NDJSON event (one line per event)”
- “payload: { file, protocol, attempt }”
- “Binary artifact checksums — record SHA256 in NDJSON event artifact.checksum.”

---

## 🔶 2. MARKER FILE YAML SCHEMA

(This is the per‑run PASS/FAIL artifact written atomically.)

**Schema:**
```yaml
---
run_id: "string"
trace_id: "string"
status: "PASS|FAIL"
phase: "text|binary"
attempts: integer
successes: integer
raw_pass_rate: float
pass_rate: integer
pioneer_failures:
    - "string"
canonical_failures:
    - "string"
binary_checksum: "string"
ts: "ISO8601 timestamp"
---
Summary: "string"
```

**Citations:**
- “Per‑run marker… with YAML header:”
- “status: PASS… pass_rate: 98… raw_pass_rate: 98.00…”
- “Atomic temp→replace writes for per‑run markers.”

---

## 🔶 3. GLOBAL SUMMARY LINE SCHEMA

(This is the single‑line append to the global .md files.)

**Schema:**
```
YYYY-MM-DD HH:MM | run_id=<id> | PASS|FAIL | <pass_rate>% | phase=<text|binary>
```

**Example:**
```
2026-03-10 15:30 | run_id=20260310-001 | PASS | 98% | phase=text
```

**Citations:**
- “Global single‑line append (atomic):
2026-03-10 15:30 | run_id=20260310-001 | PASS | 98% | phase=text”

---

## 🔶 4. AI REGENERATION DECISION TREE

(This is the logic the AI uses after receiving the summary schema. This is the authoritative decision tree for any model assisting you in VS Code.)

**STEP 1 — Did the harness PASS?**
If overall_status == PASS → ACCEPT
Else → go to Step 2.

**STEP 2 — Did any pioneer fail?**
If pioneer_failures.length > 0 → REGENERATE WITH STRUCTURAL FIXES
Reason:
- “If any pioneer’s average < 85%, mark FAILED TEXT – [NAME] VIOLATION.”
- “If any pioneer’s average < 98%, mark FAILED BINARY – [NAME] INSTABILITY.”
AI action:
- Strengthen structure
- Reduce noise
- Improve signal integrity
- Fix formatting or protocol boundaries

**STEP 3 — Did canonical tests fail?**
If canonical_failures.length > 0 → REGENERATE WITH SEMANTIC FIXES
Citations:
- “All ten canonical tests are implemented and run in every attempt.”
AI action:
- Fix headers
- Fix delimiters
- Fix symbol frequency
- Fix MSB/bit‑transition issues
- Fix checksum mismatches

**STEP 4 — Did binary phase fail but text passed?**
If text_phase_pass == true AND binary_phase_pass == false → REGENERATE WITH BINARY‑SAFETY FIXES
AI action:
- Reduce high‑ASCII
- Reduce entropy
- Improve bit‑weight balance
- Improve binary stability

**STEP 5 — Did pass_rate_int fail strict gate but pass fallback?**
If strict_gate == FAIL AND fallback_gate == PASS → REFINE, NOT REGENERATE
Citations:
- “Rule-of-thumb fallback: delta=3% with a hard cap of +/-5%.”
AI action:
- Minor cleanup
- Small structural adjustments
- Keep core logic intact

**STEP 6 — If everything fails catastrophically**
If pioneers + canonical + binary all fail → FULL REWRITE
AI action:
- Regenerate from scratch
- Rebuild structure
- Rebuild protocol compliance
# testharnessclayworkintegration Punchlist

## Purpose
This punchlist defines the integration and unified workflow between the claywork modular backend (core, control, security, mama) and the test harness, based on .mak files, scripts, protocol definitions, and JSON-driven data exchange.

---

## 1. Claywork Directory: Process Overview
- **.mak files:** Define build, orchestration, and process specs for each pillar (core, control, security, mama).
- **Scripts (e.g., .ps1):** Automate environment setup, launching services, or running workflows.
- **Protocol Definitions (.py):** Define data exchange standards and inter-module communication.
- **JSON files:** Used for configuration, state, logs, and as intermediate data packets.

### Process
- Each pillar is modular, with its own .mak file specifying its role and boundaries.
- Protocol files ensure all pillars communicate using shared standards.
- Scripts automate startup and orchestration.
- JSON files are used throughout for state/config/logging.

---

## 2. Test Harness Directory: Process Overview
- **Test scripts:** Drive integration or scenario tests across the pillars.
- **JSON files:** Define test cases, expected results, and log outputs.

### Process
- The test harness launches or simulates workflows, feeding inputs and capturing outputs.
- Uses JSON for test definitions, expected outputs, and result logs.
- Interacts with claywork modules via APIs, scripts, or .mak-defined processes.

---

## 3. Combined Process Map (Unified Backend Tool)

### How They Work Together
- Claywork provides the modular, protocol-driven backend.
- Test Harness acts as orchestrator and validator.
- JSON files are the glue for configuration, state, and validation.

### Unified Flow
1. **Startup:** Scripts initialize environment and services.
2. **Test Execution:** Test harness loads scenarios (JSON), issues commands, records outputs.
3. **Backend Processing:** Each pillar processes its workflow, using protocols and .mak orchestration.
4. **Data Exchange:** JSON files pass state, results, and logs between modules and for validation.
5. **Validation:** Test harness compares outputs (JSON) to expected results, reporting pass/fail.

---

## 4. Visual Process Map

```mermaid
flowchart TD
    subgraph Claywork Backend
        Core[Core (.mak, .py)]
        Control[Control (.mak, .py)]
        Security[Security (.mak, .py)]
        Mama[Mama (.mak, .py)]
        Protocols[Protocol Definitions (.py)]
    end
    Scripts[Startup/Orchestration Scripts]
    JSON[JSON Config/State/Logs]
    TestHarness[Test Harness (scripts, JSON)]
    User[User/Operator]

    User --> Scripts
    Scripts --> Claywork Backend
    Claywork Backend --> Protocols
    Protocols <--> Claywork Backend
    TestHarness --> Claywork Backend
    TestHarness <--> JSON
    Claywork Backend <--> JSON
```

---


## Summary
- Claywork provides modular, protocol-driven backend services, orchestrated by .mak files and scripts.
- The test harness drives and validates workflows, using JSON for test definitions and results.
- Together, they form a robust, testable backend toolchain, with JSON as the common data exchange and validation format.

---

## HARNESS SUMMARY SCHEMA (AI‑Facing / VS Code‑Facing)

This JSON schema defines the summary output for the unified test harness and claywork backend. The schema is designed for compatibility with VS Code agents and AI tools. The file name only needs to be compliant for VS Code agents to use.

```json
{
    "run_id": "string",
    "phase": "text|binary|both",
    "overall_status": "PASS|FAIL",
    "strict_gate": {
        "text_phase_pass": "boolean",
        "binary_phase_pass": "boolean",
        "heaviside_gate": "0|1"
    },
    "attempts": {
        "total_attempts": "integer",
        "successes": "integer",
        "raw_pass_rate": "float",
        "pass_rate_int": "integer"
    },
    "pioneer_suite": {
        "summary_status": "PASS|FAIL",
        "failed_pioneers": ["string"],
        "pioneer_results": {
            "PIONEER_NAME": {
                "average_score": "float",
                "integer_score": "integer",
                "status": "PASS|FAIL",
                "failed_tests": ["string"]
            }
        }
    },
    "canonical_tests": {
        "summary_status": "PASS|FAIL",
        "failed_tests": ["string"],
        "test_results": {
            "TEST_NAME": {
                "score": "float",
                "integer_score": "integer",
                "status": "PASS|FAIL"
            }
        }
    },
    "binary_artifacts": {
        "checksum_sha256": "string",
        "binary_phase_attempts": "integer",
        "binary_phase_successes": "integer",
        "binary_pass_rate_int": "integer"
    },
    "paths": {
        "marker_file": "string",
        "ndjson_log": "string",
        "global_summary_file": "string"
    },
    "timestamps": {
        "started": "ISO8601",
        "ended": "ISO8601"
    }
}
```

This schema should be used for all summary outputs and integration points between the test harness and claywork backend, ensuring consistent, machine-readable results for both AI and VS Code-based workflows.

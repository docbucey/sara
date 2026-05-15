SARA INTERFACE REFACTOR SPEC (GEN0 -> GEN1 TRANSITION)

Purpose:
- Refactor SARA browser interface into two clearly separated modes.
- Keep test harness and blind-study wiring available but not dominant in daily use.
- Make morning startup and practical training simple and repeatable.

Primary separation rule:
- Mode 1: BASIC INTERFACE (default)
- Mode 2: STUDY MODE (blind test / comparative model workflow)

Mode 1: BASIC INTERFACE (default on launch)
- Target user: owner operating SARA directly on local machine.
- Required tabs:
  - Chat Setup
  - Session / NBS Training
  - Health
  - Settings Profile
- Hidden by default in this mode:
  - Blind run compare controls
  - Reveal controls
  - Agent slot scoring details
- Core behavior:
  - chat-first interaction for setup and practical training tasks
  - direct NBS write path for lesson and note capture
  - simple status surfaces, minimal cognitive load

Mode 2: STUDY MODE (operator enabled)
- Target user: controlled experiment session.
- Required tabs:
  - Run Blind Test
  - Run History
  - Compare
  - Reveal
  - Health
- Core behavior:
  - model slot randomization
  - one-time reveal policy
  - result ranking and provenance capture
  - audit event logging

Security boundary requirements:
- Access control remains required for all endpoints.
- Local browser may use trusted local launch flow, but security checks still pass through sara_security gate logic.
- Remote access must always use remote credentials from profile.

Routing requirements:
- UI requests pass through control-style routing function before model execution.
- security gate decision must be recorded for run/compare/reveal/chat actions.

NBS training requirements:
- Chat Setup mode must emit compact NBS packets:
  - session objective
  - operator notes
  - correction notes
  - training lesson
- Packet schema must remain stable across both modes.

Refactor acceptance criteria:
- Default launch opens BASIC INTERFACE mode.
- Operator can switch to STUDY MODE without restarting backend.
- Chat Setup can run and write NBS records without invoking blind-study flow.
- Study controls are available only in STUDY MODE.
- Existing blind-study backend remains functional after refactor.

Implementation boundaries for this refactor:
- No removal of current blind-study backend routes.
- No coupling of basic chat interface to model-slot reveal logic.
- No change to existing result data file names.

Do not remove this file when updates are added.
Append newer rules below existing rules.

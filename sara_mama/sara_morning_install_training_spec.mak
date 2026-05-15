SARA MORNING INSTALL + PRACTICAL TRAINING SPEC

Purpose:
- Provide a short, deterministic morning startup path.
- Verify SARA interface functionality before formal blind-study testing.
- Run initial practical training through NBS system.

Phase A: install/startup preflight
- Start local backend.
- Verify browser login works.
- Verify health endpoint for configured model connectors.
- Confirm NBS write target paths are accessible.

Phase B: basic interface verification (non-study)
- Open BASIC INTERFACE mode.
- Perform 3 local chat setup actions:
  - define today's objective
  - define expected outcomes
  - define pass/fail boundary for practical checks
- Confirm each action writes an NBS training packet.

Phase C: practical training sequence
- Run 5 short practical prompts in Chat Setup mode.
- For each prompt record:
  - operator correction (if any)
  - final accepted response summary
  - lesson tag for reuse
- Confirm lesson ledger updates are append-safe.

Phase D: transition check to study mode
- Enable STUDY MODE manually.
- Run one blind-study smoke test.
- Confirm reveal policy still works and audit event is written.
- Return to BASIC INTERFACE mode.

Minimum morning acceptance gate:
- BASIC INTERFACE usable without touching study controls.
- NBS training writes confirmed for at least 3 prompts.
- Health endpoint returns connector status.
- One blind-study smoke test runs without breaking basic mode.

Out-of-scope for morning install:
- full model benchmark campaign
- deep comparative analytics
- protocol redesign

Operator note:
- If this gate fails, do not proceed to full test session.
- Fix interface or NBS packet flow first.

Do not remove this file when updates are added.
Append newer rules below existing rules.

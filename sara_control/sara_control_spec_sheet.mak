SARA CONTROL SPEC SHEET

Overview
Build the sara_control pillar as the operational shell for SARA Gen 0. Control accepts the bounded plan from sara_core, checks what can run now, sequences allowed actions, and records execution outcomes without taking over architecture ownership.

Core components
- Action router: maps normalized plans to allowed next actions.
- Gate checker: verifies prerequisites before execution.
- Dispatcher: sends allowed work to tool or model layer.
- Result collector: captures outputs, errors, and blocked reasons.
- Status writer: updates result.meta.json, distant_end.json, and master_result.json.

Input contract
- normalized task packet from sara_core
- workspace state
- tool and model availability
- security allow or deny decision
- prior retry hint from sara_mama when present

Output contract
- next action packet
- execution order
- blocked reason
- routed result summary
- bounded status text for JSON artifacts

Execution rules
- Control must not redefine the plan logic owned by Core.
- Control must stop execution on missing prerequisites.
- Control must record why a path was blocked, retried, or completed.
- Control must pass historical lessons to Mama after execution.

Artifact layout
- Local status file: result.meta.json
- Distant status file: distant_end.json
- Master aggregate file: master_result.json
- Local-end rules: local_end/local_end.mak
- Distant-end rules: distant_end/distant_end.mak
- Master rules: master/master.mak
- Log target: logs/

PASS/FAIL logic
- PASS means control routed a valid action path and recorded a coherent outcome.
- FAIL means routing, gating, or result capture broke contract.
- UNKNOWN means no evaluated control run has completed yet.

JSON requirements
- result.meta.json must track file, status, reached, and reason.
- distant_end.json must track mirrored action state, reached, and note.
- master_result.json must expose final_status from local and distant aggregation.

Implementation guidance
- First runtime target is sara_control.py.
- Keep dispatch behavior explicit and reversible.
- Preserve error text in bounded form so VS Code and later tools can parse it safely.
- Prefer state packets over hidden side effects.

Acceptance criteria
- Control can decide the next allowed action from a core plan.
- Control can refuse unsafe or incomplete work with a clear reason.
- Control can capture success, failure, and blocked states in JSON.
- Control can hand outcomes to Mama and Security without shape drift.

Shared evolution protocol governance
- Evolution command is `evolve` and applies to proven baseline files only.
- Every evolvable function must have a predefined shunt mapped to its origin function.
- Evolution is lineage-bound: extensions may improve only their mapped origin function.
- Evolution extends via mirrored bottom-header shunts and must not overwrite validated base behavior.
- Normal live shunt routing is controlled by sara_control to protect sara_core.
- Core keeps architecture authority and may self-evolve only for architecture or machine-facing foundations.
- Generation marker starts at A and increments only when all four pillars evolve in the same cycle.
- Every 10 system-wide expansions records a cycle checkpoint.
- Short marker tags (1-2 component tags) track intra-generation changes under the current capital generation.

Do not remove this file when updates are added.
Append newer rules below existing rules.
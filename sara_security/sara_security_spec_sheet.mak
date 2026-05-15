SARA SECURITY SPEC SHEET

Overview
Build the sara_security pillar as the boundary, validation, and audit layer for SARA Gen 0. Security remains Python-first for initial implementation, while reserving the one future non-Python exception only if hardening or isolation demands it later.

Core components
- Rule gate: evaluates whether an action is allowed.
- Boundary checker: validates file, tool, and execution scope.
- Audit writer: records allow, deny, and rationale.
- Exception handoff point: reserved location for the later hardened non-Python component.
- Status writer: updates result.meta.json, distant_end.json, and master_result.json.

Input contract
- requested action packet
- target path or target tool
- workspace context
- control routing state
- prior deny or allow history when relevant

Output contract
- allow or deny decision
- reason
- audit event summary
- hardened handoff marker when needed
- bounded status text for JSON artifacts

Execution rules
- Security must evaluate before sensitive actions proceed.
- Security must never silently allow a denied path.
- Security must emit audit-friendly reason text.
- Security must keep the later non-Python exception isolated inside this pillar only.

Artifact layout
- Local status file: result.meta.json
- Distant status file: distant_end.json
- Master aggregate file: master_result.json
- Local-end rules: local_end/local_end.mak
- Distant-end rules: distant_end/distant_end.mak
- Master rules: master/master.mak
- Log target: logs/

PASS/FAIL logic
- PASS means Security produced a coherent, bounded allow or deny decision with reason.
- FAIL means boundary evaluation was incomplete, unsafe, or contradictory.
- UNKNOWN means scaffold only; no evaluated security run yet.

JSON requirements
- result.meta.json must track file, status, reached, and reason.
- distant_end.json must track mirrored security state, reached, and note.
- master_result.json must combine the two into final_status.

Implementation guidance
- First runtime target is sara_security.py.
- Keep rules explicit and small enough to audit.
- Reserve the non-Python exception for hardening only, not convenience.
- Make deny reasons stable enough for Control and Mama to consume.

Acceptance criteria
- Security can gate a requested action with allow or deny.
- Security can record an audit-friendly rationale.
- Security can expose a stable handoff point for later hardening work.
- Security JSON artifacts remain bounded and predictable.

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

King and Phoenix sovereign security protocol
- Protocol family: King and Phoenix.
- Methods: Phoenix Fire and Phoenix Ash.
- This lane is a sovereign security execution path and is not controlled by Control during active Phoenix operations.
- Standard flow remains Core -> Control for normal shunt routing; this sovereign lane is a defined exception.
- Core still defines architecture boundaries and policy constraints for sovereign execution.
- Security executes anti-malware and governance actions at OS-facing depth when the sovereign lane is active.
- Control is continuity observer and post-lane coordinator only; it does not override active Phoenix execution.
- Purpose: support anti-malware response, governance enforcement, and future distributed security processing.
- Compatibility rule: OS base security suite remains active; SARA augments and orchestrates rather than replacing base defenses.
- Expansion note: distributed processing is enabled only under Core policy approval and Security trust criteria.

Do not remove this file when updates are added.
Append newer rules below existing rules.
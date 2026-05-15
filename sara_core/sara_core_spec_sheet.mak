SARA CORE SPEC SHEET

Overview
Build the sara_core pillar as the architecture and state-definition layer for SARA Gen 0. The core must stay Python-first, remain model-agnostic at the contract level, and provide stable planning output that sara_control can execute without redefining the system shape.

Core components
- State model: request, normalize, plan, attempt, review, improve.
- Plan builder: converts incoming work into bounded action packets.
- Improvement evaluator: decides whether an attempt meaningfully improves the prior accepted state.
- Handoff formatter: emits stable data for sara_control and sara_mama.
- Status writer: updates result.meta.json, distant_end.json, and master_result.json through the pillar flow.

Input contract
- user request text
- current workspace context
- prior accepted attempt packet
- candidate model response
- security gate result when required upstream

Output contract
- normalized task packet
- plan stages
- improvement target
- core approval or rejection recommendation
- bounded status text for JSON artifacts

Execution rules
- Core defines structure but does not directly execute tools.
- Core must keep output deterministic enough for control-side routing.
- Core must express reasons for approve, reject, or revise.
- Core must preserve prior accepted logic before replacing it.

Artifact layout
- Local status file: result.meta.json
- Distant status file: distant_end.json
- Master aggregate file: master_result.json
- Local-end rules: local_end/local_end.mak
- Distant-end rules: distant_end/distant_end.mak
- Master rules: master/master.mak
- Log target: logs/

PASS/FAIL logic
- PASS means core produced a valid, bounded, handoff-safe plan.
- FAIL means core output is structurally incomplete, contradictory, or unsafe to hand to control.
- UNKNOWN means the pillar scaffold exists but no evaluated run has completed.

JSON requirements
- result.meta.json must track file, status, reached, and reason.
- distant_end.json must track mirrored status, reached, and note.
- master_result.json must combine local and distant outcomes into final_status.

Implementation guidance
- First runtime target is sara_core.py.
- Use Python standard library first.
- Keep model-specific prompts outside the core logic contract.
- Treat architecture decisions as data that can be reviewed later by Mama.

Acceptance criteria
- Core can describe a task as a finite state path.
- Core can emit a bounded plan packet for Control.
- Core can explain why an attempt is accepted or rejected.
- Core artifacts remain small, structured, and stable.

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
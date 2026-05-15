SARA MAMA SPEC SHEET

Overview
Build the sara_mama pillar as the memory and lesson-capture layer for SARA Gen 0. Mama stores what worked, what failed, why it failed, and what retry path should be preferred next time. Mama supports learning from history without replacing Core planning or Control routing.

Core components
- Attempt ledger: stores accepted and failed attempt summaries.
- Lesson extractor: converts errors and user corrections into reusable guidance.
- Retry suggester: offers prior-success paths or better retry paths.
- Memory formatter: returns compact packets for Core and Control.
- Status writer: updates result.meta.json, distant_end.json, and master_result.json.

Input contract
- execution result from Control
- approval or rejection rationale from Core
- user correction or override
- security outcome when relevant
- prior memory packet

Output contract
- memory packet
- lesson summary
- retry suggestion
- prior-success reference
- bounded status text for JSON artifacts

Execution rules
- Mama must preserve provenance for lessons.
- Mama must separate accepted patterns from failed patterns.
- Mama must not invent authority it did not observe.
- Mama must return compact history that can be reused without replaying everything.

Artifact layout
- Local status file: result.meta.json
- Distant status file: distant_end.json
- Master aggregate file: master_result.json
- Local-end rules: local_end/local_end.mak
- Distant-end rules: distant_end/distant_end.mak
- Master rules: master/master.mak
- Log target: logs/

PASS/FAIL logic
- PASS means Mama captured reusable history with clear reason and provenance.
- FAIL means memory output is ambiguous, lossy, or unsafe to reuse.
- UNKNOWN means the scaffold exists but memory flow has not been evaluated yet.

JSON requirements
- result.meta.json must track file, status, reached, and reason.
- distant_end.json must track mirrored memory return state, reached, and note.
- master_result.json must combine the two into final_status.

Implementation guidance
- First runtime target is sara_mama.py.
- Prefer append-safe, bounded records.
- Keep memory packets readable by humans and tools.
- Make user corrections first-class inputs to lesson extraction.

Acceptance criteria
- Mama can store failed and successful attempt summaries distinctly.
- Mama can return a compact retry hint.
- Mama can explain why a past path should or should not be reused.
- Mama JSON artifacts stay small and consistent.

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

PlainJain-first Gen1 Mama baseline
- Baseline source for early Gen1 Mama behavior is ai_llc/plainjainllm.slam.
- Mama must support profile-based model routing so different traditional model files can be used without changing Mama packet schema.
- Required initial profiles:
	- plainjain_native: internal NBS-weighted substrate path
	- ollama_default: external model bridge path
- Profile routing must preserve the same output contract:
	- memory packet
	- lesson summary
	- retry hint
	- provenance reference
- Existing Mama features from Gen0 remain active:
	- attempt ledger
	- lesson extraction
	- prior success lookup
- Acceptance extension for this baseline:
	- A profile can be selected per task.
	- Selected profile is recorded in provenance.
	- Control and Core can consume packet output without profile-specific parsing.

Interface refactor planning anchors
- Interface refactor baseline is defined in sara_interface_refactor_spec.mak.
- Morning startup and practical training gate is defined in sara_morning_install_training_spec.mak.
- Refactor direction separates Basic Interface mode from Study Mode so daily SARA use is not over-wired to blind-study controls.
- Basic Interface mode remains the default launch target for practical operation and NBS training.

Do not remove this file when updates are added.
Append newer rules below existing rules.

--- GEN 2 LANGUAGE AND LAUNCHER DECISIONS (captured 2026-03-12) ---

Launcher direction
- Python is not reliable as a user-facing launcher on target machines (env load friction).
- Gen 2 delivery target is a compiled EXE launcher so the user runs one file with no Python setup required.
- Backend-all-the-way model: desktop shell becomes a thin native launcher that starts the compiled backend and opens a browser window. No PySide/Qt dependency on the user side.

Pillar language assignments for Gen 2
- Control  →  C  (routing, scheduling, harness host; already proven in harness layer)
- Mama     →  C# (profile routing, ledger, memory packets; C# suits structured data + fast iteration)
- Security →  stays current (C harness-compatible; no change needed at this stage)
- Core     →  Python stays (Core handles planning, NBS reasoning, and model connector work; Python is the right tool here)

Rationale
- C for Control keeps the harness/host boundary tight and fast.
- C# for Mama gives structured-data ergonomics without full C overhead, and compiles to an EXE-friendly runtime.
- Core stays Python because model connectors, NBS pattern work, and reasoning helpers are well-served by Python's ecosystem.
- Security is already working in the C harness layer; no Gen 2 rewrite needed unless new gate logic requires it.

Pending Monday
- Connection refused on local backend: root cause is Python env not running at launch time.
- Addressed at Gen 2 stage with compiled launcher; no patch needed on current Gen 0/1 stack.
---
# Project Intent Lock (Control + Gen0 Spec First)

## Primary Objective (authoritative)
The main workstream is:
1. Bring CONTROL up to strength and keep it stable.
2. Complete and operationalize the SARA Gen0 expanded spec sheet in this workspace.

SDK work is secondary and exists to support expansion without repeated CONTROL rewrites.

## What SDK Work Means In This Project
SDK changes are considered successful when they:
1. Make expansion easier.
2. Avoid heavy revisits to CONTROL.
3. Preserve current CONTROL/spec behavior and contracts.

SDK work is not the project center; it is an enablement layer.

## Canonical Docs For This Intent
- nbs/Documentation/mama_native_twin_engine_plan.md
- nbs/Documentation/ollama_dependency_closure_checklist.md
- nbs/Documentation/sdk_micro_ai_install_unified_plan.md

## Completion Snapshot (aligned to intent)
- CONTROL hardening lane is active and passing current protocol gate checks.
- Gen0 expanded spec implementation lane is active and mapped.
- SDK has been expanded as scaffolding so future target installs/adaptations can proceed with fewer CONTROL revisits.

## No-Revisit Rule (unless required)
Revisit CONTROL only when at least one condition is true:
1. A spec contract changed.
2. A security/route integrity issue appears.
3. A target install path proves incompatible with current CONTROL contracts.

Otherwise continue extension work in SDK/MAMA layers.

## Practical Direction For Next Mapping Passes
1. Treat CONTROL as the stability anchor.
2. Continue Gen0 expanded spec completion tasks.
3. Use SDK adapters/planners to absorb per-target differences.
4. Escalate to CONTROL edits only on contract break, not preference.

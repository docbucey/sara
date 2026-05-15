# MAMA-Native Twin Engine Plan (Ollama as Controlled Backup)

## Goal
Build a SARA-native inference lane that behaves like a twin of CONTROL governance and plugs through MAMA, while keeping Ollama available only as controlled fallback during experimental phases.

## What already exists (usable now)
- Native SLAM architecture contract:
  - `claywork/saragen0finish/sara_mama/ai_llc/plainjainllm.slam`
- External bridge contract (fallback only):
  - `claywork/saragen0finish/sara_mama/ai_llc/ollama_bridge.slam`
- Mapping/index scaffold for native path:
  - `claywork/saragen0finish/sara_mama/model_profiles/mapping_manifest_plainjain.json`
- Proto-math layers and engine stubs:
  - `claywork/saragen0finish/sara_mama/proto_math/*`
- CONTROL AMIP routing and SHI governance:
  - `claywork/saragen0finish/sara_control/sara_controlgen1.py`

## What needs to be added for a real twin engine
1. Native executor runtime in MAMA (missing)
- Add `plainjain_executor.py` under `sara_mama/ai_llc/`.
- Responsibilities:
  - Parse/interpret SLAM ops (`tokenize`, `floodsearch_match`, `follow_nexus_links`, `sequian_reconstruction`).
  - Resolve substrate paths and profile context.
  - Produce deterministic envelope output (no direct route authority).

2. Context-to-SLAM binder (missing)
- Add `context_bindings.py` in `sara_mama/ai_llc/`.
- Convert CONTROL envelope fields (`mode`, `strain`, `persona`, `document_context`) into runtime knobs:
  - propagation depth
  - stability threshold
  - provenance weighting
  - resonance radius

3. MAMA adapter lane for native engine (partial)
- Extend model profile/dispatcher to include `plainjain_native` as active runnable backend (not metadata only).
- Keep output schema aligned with current AMIPI response shape.

4. SDK target registration for native engine (missing)
- Add a stable AMI id, e.g. `plainjain_executor`.
- Wire CONTROL target resolution rule to select it for approved intents/personas.

5. Observability + replay harness (missing)
- Add deterministic trace logging for:
  - activated nodes
  - propagation path
  - threshold rejections
  - final synthesis components
- Add replay mode to reproduce outputs from the same envelope.

## Safe migration order
1. Keep `SARA_OLLAMA_POLICY=backup`.
2. Implement native executor in shadow mode (compute result but do not return to user).
3. Compare native output vs current output in blind runs.
4. Promote native executor for selected routing intents.
5. Keep Ollama fallback only for denied native confidence windows.
6. When stable, set `SARA_OLLAMA_POLICY=off` as default for production-like runs.

## Decision policy (recommended)
- `SARA_OLLAMA_POLICY=off` for strict runs.
- `SARA_OLLAMA_POLICY=backup` for development and recovery windows.
- `SARA_OLLAMA_POLICY=full` only for temporary diagnostics.

## Generation profile policy (implemented in CONTROL)
- `creative_probabilistic`: higher expressiveness, default for interactive requests.
- `stable_probabilistic`: lower variance, default for night_shift and constrained contexts.
- `strict_deterministic`: fixed-seed deterministic profile for repeatability and high-risk states.

Automatic fallback rules:
- SHI `warn`: creative -> stable
- SHI `clamp`: non-strict -> stable
- SHI `deny`: force strict
- `requires_repeatability=true`: force strict

Current integration note:
- MAMA now consumes CONTROL generation policy via `generation_surface` in AMIP UX summaries.
- MAMA->CONTROL shunt payload now passes through generation hints (`generation_profile`, `requires_repeatability`, `allow_ollama_backup`).
- MAMA now applies executor-level runtime knobs (`sampling_width`, `propagation_depth`, `stability_threshold`, `temperature`, `top_p`, `seed`) into `amipi_result.native_runtime` for plainjain-native execution surfaces.
- A dedicated native executor module is now present at `sara_mama/ai_llc/plainjain_executor.py` and wired into MAMA result processing (`native_execution` + `model_output.generated_text`).
- Replay mode is supported for audit reproducibility: pass `replay_mode=true` with optional `replay_key` or explicit `replay_seed` to force deterministic replayable outputs on the native executor.
- Replay ledger is enabled in native execution by default and appends NDJSON audit records to `sara_mama/logs/plainjain_replay_ledger.ndjson` (prompt hash, output hash, profile, seed, replay key, correlation id).

Replay ledger query utility:
- Script: `claywork/saragen0finish/sara_mama/tools/replay_ledger_query.py`
- Example by replay key:
  - `python claywork/saragen0finish/sara_mama/tools/replay_ledger_query.py --replay-key arm-audit-01 --summary-only`
- Example by correlation id:
  - `python claywork/saragen0finish/sara_mama/tools/replay_ledger_query.py --correlation-id <id> --latest-first --limit 10`
- CSV export:
  - `python claywork/saragen0finish/sara_mama/tools/replay_ledger_query.py --replay-key arm-audit-01 --csv claywork/saragen0finish/sara_mama/logs/arm-audit-01.csv --limit 100`

MAMA convenience wrapper:
- Function: `query_replay_ledger_mama(...)` in `sara_mamagen1.py`
- Supports replay key, correlation id, hash-prefix filters, summary-only mode, and CSV export path.

Cross-device continuity compare:
- Script: `claywork/saragen0finish/sara_mama/tools/replay_ledger_compare.py`
- Example:
  - `python claywork/saragen0finish/sara_mama/tools/replay_ledger_compare.py --ledger-a <desktop-ledger.ndjson> --ledger-b <arm-ledger.ndjson> --replay-key arm-audit-01 --summary-only`
- CSV compare export:
  - `python claywork/saragen0finish/sara_mama/tools/replay_ledger_compare.py --ledger-a <desktop-ledger.ndjson> --ledger-b <arm-ledger.ndjson> --replay-key arm-audit-01 --csv claywork/saragen0finish/sara_mama/logs/arm-compare.csv`
- MAMA wrapper: `compare_replay_ledgers_mama(...)` in `sara_mamagen1.py`

## Completion criteria for uninstall-ready native twin
- Native executor covers required intents with deterministic pass rates.
- SHI trend stable under native lane in both interactive and night_shift modes.
- Fallback usage drops below agreed threshold (example: <2% of requests over 7 days).
- No CONTROL route depends on Ollama-only schema/fields.

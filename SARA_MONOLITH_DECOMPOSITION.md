# SARA Monolith Decomposition & Rebuild Map

**Date:** 2026-05-11 (updated with full project lineage)
**Purpose:** Break the five gen1 monoliths back into modular files aligned with original architectural intent, legacy structure, gen0.5 spec sheets, the BIOMETRIC_PROTOCOL_SPEC, and the full genealogy of precursor projects.

---

## 1. Architectural Rules (from sara_architecture_log.md)

These rules are **non-negotiable** and apply to every module in the rebuild:

1. **Dependency direction**: `SDK / MAMA / SECURITY → CONTROL → CORE` (one-way, no backflow)
2. **CONTROL is sole routing authority** — nothing bypasses it
3. **CORE is engine only** — agnostic to high-level logic, responds only to CONTROL
4. **MAMA is presentation only** — captures input, presents output, does not route or gate
5. **SECURITY provides gating services** — validates, audits, scans; does not orchestrate
6. **SDK is adapter surface** — external protocols, devices, special-case lanes
7. **Data flow**: `Input → Store → Process → Store → Output`
8. **Biometrics are constant** — always-on for local human/ADA adaptation (SECURITY-gated disable only)

---

## 2. Current Monolith Inventory

| Pillar | File | Lines | Functions | Classes |
|--------|------|-------|-----------|---------|
| CONTROL | `sara_control/sara_controlgen1.py` | ~5,544 | 120+ | 5 (ShuntFSM, SARA_AIBackend, SecurityManager, LearnManager, ControlIngestBufferGuard, ControlSystemStrainBudget) |
| CORE | `sara_core/sara_coregen1.py` | ~3,800+ | 90+ | 6 (ShuntFSM ×2, BuceyShunt, TextExtractor, SaraMemoryIO, LinkExtractor, UserLocationRuleRegistry, LocationShuntRegistry) |
| MAMA | `sara_mama/sara_mamagen1.py` | ~2,050 | 60+ | 4 (ShuntFSM, MamaDispatcher, AdaptiveJargonLexicon, MamaLedger, PlainJainMama) |
| SECURITY | `sara_security/sara_securitygen1.py` | ~2,350 | 65+ | 1 (ShuntFSM) |
| SDK | `sara_sdk/Sara_sdk.gen1.py` | ~370 | 15 | 2 (SDKRequest, SaraSdkGen1) |

**Total: ~14,100+ lines in 5 files, ~350+ functions**

---

## 3. Original Intent (from gen0.5 function_maps & breaking_maps)

### CONTROL was supposed to be:
- `validate_shunt_header` — envelope validation
- `protocol_enforcement` — FSM state/transition
- `reasoning_math_engine_selection_execution_management` — orchestrate AI/math backends
- `audit_authorization_launch_routines` — king/paladin/sheriff security chain
- `protocol_extension_authority` — new codes/lanes
- `ada_accessibility_mapping_initialization_enforcement` — ADA compliance

### CORE was supposed to be:
- `validate_shunt_header` — envelope validation
- `ShuntFSM` — protocol state machine
- `data_file_io_handlers` — image, video, audio, 3D, office
- `proto_lingua_tagging_resonance_validation` — data normalization
- `compatibility_bridge` — legacy imports/runtime safety

### MAMA was supposed to be:
- `mama_shunt_entrypoint` + `ShuntFSM` — protocol interface
- `ACT_mapped_functions` — snapshot, diff, persist
- `scout, yard, house, mapper` — UX/presentation subsystems

### SECURITY was supposed to be:
- `Paladin` — defense/threat detection
- `Sheriff` — auditor/integrity scans
- `Deputy` — janitor/gatekeeper
- `Archeologist` — catalog/inventory
- `Conservator` — repair/stabilize
- `Restoration` — capability scan/upgrade
- `Envoy` — secure transport/proxy
- `King` — authority/lockdown
- `SecurityKeep` — role orchestration

### SDK was supposed to be:
- `adapter_wrapper_modules` — targets, compilers, external systems
- `ai_plugin_extension_scaffolding` — AI adapter scaffolding
- `integration_lanes` — AI/model adapters
- `protocol_extension_points` — new codes/lanes
- `security_audit_inherited` — inherited audit

---

## 4. What Leaked Where (Violations of Original Intent)

### CONTROL has absorbed:
- **Office document creation** (write_docx_con, edit_docx_con, write_xlsx_con, edit_xlsx_con, write_pdf_con, compose_image_con, edit_image_con) — should be CORE I/O or SDK
- **MAMA's calculation/research domain** (mama_research_calc_run_con, mama_validate_real_world_excel_con, mama_traditional_calc_run_con, mama_business_calc_run_con, mama_calc_run_con) — should be in MAMA
- **Mechanic subsystem** (mechanic_calendar_run_con, mechanic_email_run_con, mechanic_sheets_run_con, etc.) — should be SDK or its own module
- **Chat/transcript parsing** (parse_chat_con, emit_transcript_nbs_con, ingest_chat_con) — should be CORE persistence
- **Concept extraction** (extract_concepts_con, query_concepts_con) — should be CORE or a learning module
- **Ingest pipeline** (ingest_artifacts_con with 270+ lines of file scanning) — should be CORE I/O
- **Strain budget / buffer guard classes** — should be its own governor module
- **SecurityManager class** — belongs in SECURITY pillar
- **LearnManager class** — should be its own learning module (referenced by CONTROL)
- **AI Backend class** (SARA_AIBackend) — should be SDK adapter

### CORE has absorbed:
- **HTTP client** (http_get, extract_text, extract_links) — should be SDK network adapter
- **Email transport** (core_smtp_send_email, core_imap_fetch_inbox) — should be SDK or CONTROL-routed
- **Phoenix/location systems** (compose_phoenix_snapshot, LocationShuntRegistry, malware hooks) — should be SECURITY or SDK
- **Duplicate ShuntFSM** — defined twice (lines 1090 and 1996)
- **Legacy compatibility wrappers** (_to_proto_lingua_legacy, create_nbs_file_legacy) — should be isolated legacy module
- **FSM state diagram export** (export_fsm_state_diagram) — diagnostic, not core I/O

### MAMA has absorbed:
- **Clerk protocol endpoints** (15+ clerk_* functions) — dispatching logic that should be in CONTROL
- **MamaDispatcher** with local Office/geek protocol handling — violates "CONTROL is sole routing authority"
- **Direct CORE fallback** in learning_action — bypasses CONTROL on error

### SECURITY is mostly clean but has:
- **Document scanning** (scan_image_con, scan_docx_con, scan_xlsx_con, scan_pdf_con, audit_files_con) — reasonable but could be separate file
- **Windows Defender integration** (_find_windows_defender_cli, _scan_with_windows_defender) — platform-specific, should be isolated

---

## 5. Proposed Module Decomposition

### CONTROL pillar → `sara_control/`

| Module | Contents | Source Lines (approx) |
|--------|----------|-----------------------|
| `__init__.py` | Package init, exports | 10 |
| `shunt.py` | `control_shunt_entrypoint`, `validate_shunt_header`, ACT dispatch, `_dispatch_to_pillar`, `launch_all_pillars` | ~150 |
| `fsm.py` | `ShuntFSM`, `ControlFSM`, state constants, transition validation, logging | ~120 |
| `dispatch.py` | `dispatch()` main entry, king→paladin→sheriff→FSM flow, `_cmd_*` wrappers, command registry | ~400 |
| `routing.py` | `route_io_con`, `route_bucey_shunt_con`, `_build_operator_flow_con`, `wfh_protocol_con`, `abbucey_protocol_con` | ~250 |
| `amip.py` | `dispatch_amipi_con`, `_normalize_amip_request_con`, `_resolve_ami_target_con`, Ollama policy, SHI governor | ~400 |
| `session.py` | `start_session_con`, `end_session_con`, `append_event_con`, `checkpoint_con`, `heartbeat_con`, narrative profile sync | ~250 |
| `vnce.py` | `vnce_lifecycle_con`, `start_vnce_session_con`, `resume_vnce_session_con`, STABLES notification | ~150 |
| `jobs.py` | Job pipeline: `job_intake_filter`, `job_feasibility_classifier`, `spec_sheet_generator`, `refinement_*`, `deliverable_plan_generator` | ~300 |
| `identity.py` | `identity_resolve_con`, `ensure_narrative_profile_con`, `load_persona_con`, profile bridge | ~150 |
| `learning.py` | `LearnManager` class, `learn_overlay_con`, experiential learning loop | ~200 |
| `governor.py` | `ControlIngestBufferGuard`, `ControlSystemStrainBudget`, `_process_memory_percent_con`, `_user_interactive_active_con` | ~200 |
| `loader.py` | Module loaders: `_load_core_module`, `_load_mama_module`, `_load_gen1_security`, `_load_sdk_gen1_module_con`, `_load_mechanic_adapter_contract` | ~80 |
| `http_bridge.py` | Already exists: `sara_control_http.py` (HTTP bridge server) — keep as-is | 170 |
| `server.py` | `control_server()` interactive loop — to be replaced with proper dispatch | ~30 |

**Move OUT of CONTROL:**
- `office_file_action` → CORE I/O
- `write_docx_con`, `edit_docx_con`, `write_xlsx_con`, `edit_xlsx_con`, `write_pdf_con`, `compose_image_con`, `edit_image_con` → CORE document I/O
- `mama_research_calc_run_con`, `mama_*_calc_run_con` → MAMA research/calc module
- `mechanic_*_run_con` → SDK mechanic adapter or its own module
- `parse_chat_con`, `emit_transcript_nbs_con`, `ingest_chat_con` → CORE persistence
- `ingest_artifacts_con` → CORE persistence
- `extract_concepts_con`, `query_concepts_con` → CORE or learning module
- `SecurityManager` class → SECURITY pillar
- `SARA_AIBackend` class → SDK adapter
- `route_mail_transport_con` → SDK mail adapter (CONTROL just routes the shunt)

---

### CORE pillar → `sara_core/`

| Module | Contents | Source Lines (approx) |
|--------|----------|-----------------------|
| `__init__.py` | Package init, exports | 10 |
| `shunt.py` | `core_shunt_entrypoint`, `validate_shunt_header`, `build_vnce_shunt_envelope` | ~80 |
| `fsm.py` | Single canonical `ShuntFSM` class (remove duplicate) | ~60 |
| `nbs.py` | `create_nbs_file`, `create_nbs_reference`, `in_out_nbs_file`, `create_characterbase_nbs_profile`, `create_nbs_project_profile`, `update_nbs_project_profile` | ~400 |
| `client_projects.py` | `create_client_projects_sheet`, `update_client_projects_sheet`, `remove_client_project_preserve_critical`, `list_client_projects_sheet` | ~300 |
| `proto_lingua.py` | `_classify_value_suffix`, `_to_proto_lingua`, `validate_resonance` | ~100 |
| `amip.py` | `resolve_machine_profile_core`, `build_amip_payload_core`, `build_bucey_shunt_envelope_core`, `unwrap_bucey_shunt_core`, `build_core_lite_bundle_core` | ~200 |
| `file_io.py` | All file readers/writers: `read_image_file`, `write_image_file`, `read_video_file`, `read_audio_file`, `read_3d_file`, `read_word_docx`, `write_word_docx`, `read_excel_xlsx`, `write_excel_xlsx`, `read_powerpoint_pptx`, `write_powerpoint_pptx` | ~350 |
| `document_compose.py` | Document creation (moved from CONTROL): `write_docx`, `edit_docx`, `write_xlsx`, `edit_xlsx`, `write_pdf`, `compose_image`, `edit_image` | ~600 |
| `persistence.py` | `append_event`, `memory_set/get/delete`, `SaraMemoryIO`, chat parsing, transcript emit, artifact ingest (moved from CONTROL) | ~400 |
| `compression.py` | `core_compress_bytes`, `core_decompress_bytes`, `core_detect_compression_format`, `core_checksum_bytes`, `core_extract_full`, `core_extract_target` | ~80 |
| `network.py` | `http_get`, `extract_text`, `extract_links`, `TextExtractor`, `LinkExtractor`, `BuceyShunt` HTTP class | ~150 |
| `email.py` | `core_smtp_send_email`, `core_imap_fetch_inbox` (or move to SDK) | ~150 |
| `media.py` | Media sequence: `import_media_sequence`, `export_media_sequence`, `edit_timeline`, `query_timeline_media`, `submit_render_job`, `query_render_job`, `cancel_render_job`, `retrieve_render_output` | ~400 |
| `scene.py` | 3D scene: `create_update_scene`, `query_scene_state`, `delete_scene_object`, `import_3d_asset`, `export_3d_asset`, `convert_3d_asset`, `validate_3d_asset` | ~350 |
| `phoenix.py` | Phoenix snapshots, location file handling, malware hooks, user location rules | ~300 |
| `legacy.py` | All `*_legacy` functions isolated here for backward compatibility | ~100 |

---

### MAMA pillar → `sara_mama/`

| Module | Contents | Source Lines (approx) |
|--------|----------|-----------------------|
| `__init__.py` | Package init, exports | 10 |
| `shunt.py` | `mama_shunt_entrypoint`, `validate_shunt_header`, ACT dispatch (snapshot, diff, persist) | ~100 |
| `fsm.py` | `ShuntFSM` for MAMA | ~30 |
| `slm.py` | `mama_slm_entrypoint`, `terminal_window_action`, `ide_protocol_action`, `device_input_action`, `learning_action`, `mama_stagework_action` | ~200 |
| `ux_adapt.py` | `adapt_amip_ux_mama`, UX profile resolution, `_resolve_native_runtime_knobs_mama`, `_apply_native_runtime_policy_mama` | ~200 |
| `biometrics.py` | `_extract_biometric_context_mama`, `_predict_contextual_state_mama` + new: tremor detection, baseline calibration, progressive disability profiling (from BIOMETRIC_PROTOCOL_SPEC) | ~300+ |
| `reasoning.py` | `_extract_validated_reasoning`, `_build_reasoning_overlay` | ~80 |
| `osh.py` | `_phase1_outcome_from_result_mama`, `_phase1_osh_surface_mama` | ~60 |
| `presentation.py` | `summarize_bucey_shunt_mama`, `present_amipi_result_mama` | ~80 |
| `jargon.py` | `AdaptiveJargonLexicon`, `_normalize_term`, `_tokenize_words`, `_is_acronymish`, `_is_technical_token` | ~250 |
| `ledger.py` | `MamaLedger` class, replay ledger query/compare | ~200 |
| `plainjain.py` | `PlainJainMama` class, `run_mama_proof` | ~300 |
| `calc.py` | Research/business/traditional calc functions (moved from CONTROL) | ~350 |
| `clerk.py` | Clerk protocol endpoints — BUT these should **route through CONTROL**, not dispatch locally. Refactor to shunt-based. | ~200 |
| `dispatcher.py` | `MamaDispatcher` — refactor to remove local protocol handling, delegate to CONTROL | ~80 |

**Existing submodules to keep:**
- `ai_llc/plainjain_executor.py` — already separate
- `ai_llc/ollama_bridge.slam`, `deepseeker_coder_bridge.slam` — bridge configs
- `envoy_web/agents.py` — already separate
- `tools/replay_ledger_query.py`, `replay_ledger_compare.py` — already separate
- `reasoning_protocols.py` — already separate
- `mailroom_protocol.py` — already separate
- `settings_protocol.py` — already separate

---

### SECURITY pillar → `sara_security/`

| Module | Contents | Source Lines (approx) |
|--------|----------|-----------------------|
| `__init__.py` | Package init, exports | 10 |
| `shunt.py` | `security_shunt_entrypoint`, `validate_shunt_header`, ACT dispatch | ~80 |
| `fsm.py` | `ShuntFSM` for SECURITY | ~50 |
| `king.py` | `king_sovereignty_check`, `evaluate_sovereignty_sec`, ROYAL_SIGNET | ~120 |
| `paladin.py` | `paladin_gate`, hostile signature scanning | ~30 |
| `sheriff.py` | `sheriff_audit`, audit event generation | ~40 |
| `stables.py` | `stables_init_session_sec`, `stables_validate_session_sec`, `stables_close_session_sec`, `stables_mark_session_drop_sec`, session token management | ~200 |
| `validation.py` | `validate_ami_id_sec`, `validate_amip_payload_sec`, `validate_bucey_shunt_sec`, `validate_mail_transport_sec` | ~200 |
| `dispatch.py` | `dispatch_security`, `_cmd_*` wrappers, command registry | ~200 |
| `trust.py` | `_default_trust_policy_sec`, `_load_trust_policy_sec`, `scout_house_posture_sec` | ~80 |
| `vault.py` | `security_vault_lifecycle_sec`, `safe_zeroize_sec`, `security_incident_lifecycle_sec` | ~150 |
| `scanner.py` | Document/image scanning: `scan_image_con`, `scan_docx_con`, `scan_xlsx_con`, `scan_pdf_con`, `audit_files_con` | ~500 |
| `platform.py` | Windows Defender integration, platform-specific scanning (`_find_windows_defender_cli`, `_scan_with_windows_defender`, `_quarantine_file`, `_scan_file_policy`) | ~150 |
| `envoy.py` | `_validate_vnce_envoy_record`, envoy scanning | ~100 |
| `harness.py` | `run_security_harness_check`, `_cmd_harness_proof` | ~80 |

---

### SDK pillar → `sara_sdk/`

| Module | Contents | Source Lines (approx) |
|--------|----------|-----------------------|
| `__init__.py` | Package init, exports | 10 |
| `shunt.py` | SDK shunt entrypoint (missing — needs to be created per actionmap: `build_local_bucey_shunt`, `send_bucey_shunt`) | ~80 |
| `identity.py` | `sdk_identity_catalog`, `SDKRequest`, `sdk_status` | ~50 |
| `dispatch.py` | `dispatch_sdk_protocol`, `dispatch_amipi_backend`, `build_amipi_dispatch_record` | ~120 |
| `protocols.py` | `device_protocol`, `arms_protocol`, `server_protocol`, `ide_protocol`, `build_sdk_header` | ~80 |
| `ai_backend.py` | `SARA_AIBackend` class (moved from CONTROL), backend registry | ~40 |
| `mail.py` | Mail transport adapter (wrapping CORE email functions, routing through CONTROL) | ~60 |
| `mechanic.py` | Mechanic adapters (moved from CONTROL): calendar, email, sheets, export, voice, model, smoke check | ~200 |
| `ollama.py` | Ollama-specific adapter, policy, bridge | ~60 |

**Existing submodules to keep:**
- `systems/hardware_profiles.py`, `server_adapter.py`, `pc_adapter.py`
- `ios/device_api.py`, `android/device_api.py`, `tv/dashboard_api.py`
- `arm/board_api.py`
- `common/micro_ai_installer.py`
- `kernels/` (reference, don't touch)

---

## 6. Missing Pieces (from specs but not implemented)

### From BIOMETRIC_PROTOCOL_SPEC.md:
- [ ] `TremorProfile` data class and `analyze_tremor_signature()` — not in any pillar
- [ ] Baseline calibration flow — not implemented
- [ ] Signal processing pipeline (velocity, acceleration, FFT) — not implemented
- [ ] Adaptive filter algorithm (`apply_adaptive_filter`) — not implemented
- [ ] TechBallCamp drill framework — not implemented
- [ ] Progressive disability profiling — not implemented
- [ ] Condition progression tracking — not implemented
- [ ] MamaLedger biometric storage schema — not implemented
- [ ] Filter effectiveness measurement and auto-tuning — not implemented

### From actionmap.updated.json SDK entries:
- [ ] `build_local_bucey_shunt` — not found in SDK code
- [ ] `send_bucey_shunt` — not found in SDK code

### From gen0.5 SECURITY function_map:
- [ ] `Deputy` (janitor/gatekeeper) — no dedicated implementation
- [ ] `Archeologist` (catalog/inventory) — no dedicated implementation
- [ ] `Conservator` (repair/stabilize) — no dedicated implementation
- [ ] `Restoration` (capability scan/upgrade) — no dedicated implementation
- [ ] `SecurityKeep` (role orchestration) — no dedicated implementation

### From gen0.5 MAMA function_map:
- [ ] `scout` — not implemented as named
- [ ] `yard` — not implemented as named
- [ ] `house` — not implemented as named
- [ ] `mapper` — not implemented as named

### From gen0.5 CONTROL function_map:
- [ ] `ada_accessibility_mapping_initialization_enforcement` — stub only, no real ADA enforcement
- [ ] `reasoning_math_engine_selection_execution_management` — AI backend exists but not wired to math/reasoning selection

### From architecture:
- [ ] `control_server()` does not call `dispatch()` — the interactive loop is disconnected
- [ ] HTTP bridge exists (`sara_control_http.py`) but is not integrated into startup
- [ ] LearnManager has no real `try_fn`/`reflect_fn`/`adapt_fn` implementations
- [ ] Experiential learning is not connected to biometric context
- [ ] No longitudinal biometric history in NBS

---

## 7. Rebuild Order

### Phase 0: Shared Infrastructure
1. Create `sara_common/` with shared `ShuntFSM` (one canonical definition), `shunt_header.py` (shared validation), and `types.py` (shared type definitions)
2. Remove duplicate `ShuntFSM` from all pillars — import from `sara_common`

### Phase 1: CORE (The Engine)
1. Split `sara_coregen1.py` into modules listed above
2. Verify all file I/O works
3. Move document composition functions from CONTROL into CORE
4. Consolidate legacy wrappers into `legacy.py`
5. Remove duplicate ShuntFSM

### Phase 2: SECURITY (The Keep)
1. Split `sara_securitygen1.py` into modules listed above
2. Implement the missing roles (Deputy, Archeologist, Conservator, Restoration, SecurityKeep) as stubs
3. Move `SecurityManager` class from CONTROL into SECURITY

### Phase 3: CONTROL (The Loom)
1. Split `sara_controlgen1.py` into modules listed above
2. Remove everything that doesn't belong (document creation, calc functions, mechanic adapters, chat parsing)
3. Wire `control_server()` to actually call `dispatch()`
4. Integrate HTTP bridge into startup
5. Connect LearnManager to real functions

### Phase 4: MAMA (The Gate)
1. Split `sara_mamagen1.py` into modules listed above
2. Create `biometrics.py` with the full pipeline from BIOMETRIC_PROTOCOL_SPEC.md
3. Wire biometric context into LearnManager via CONTROL shunts
4. Refactor clerk endpoints to route through CONTROL
5. Remove local dispatch from MamaDispatcher

### Phase 5: SDK (The Identity Assembler)
1. Add missing `build_local_bucey_shunt` and `send_bucey_shunt`
2. Move `SARA_AIBackend` from CONTROL to SDK
3. Move mechanic adapters from CONTROL to SDK
4. Wire mail transport through SDK adapter

### Phase 6: Integration
1. Verify all cross-pillar shunt routing works through CONTROL
2. Verify biometric → MAMA → CONTROL → CORE persistence pipeline
3. Run security harness checks
4. Verify HTTP bridge accepts and dispatches real envelopes

---

## 8. File Cross-Reference: Legacy → Gen1 → Rebuild

| Legacy / Gen0.5 | Current Gen1 Monolith | Rebuild Target |
|------------------|-----------------------|----------------|
| `Sara_core.py` (archive) | `sara_core/sara_coregen1.py` | `sara_core/{nbs,file_io,proto_lingua,amip,...}.py` |
| `sara_control.py` (archive) | `sara_control/sara_controlgen1.py` | `sara_control/{dispatch,routing,session,amip,...}.py` |
| — | `sara_control/sara_control_http.py` | `sara_control/http_bridge.py` (keep) |
| `sara_mama.py` (archive) | `sara_mama/sara_mamagen1.py` | `sara_mama/{ux_adapt,biometrics,presentation,...}.py` |
| `sara_security.py` (archive) | `sara_security/sara_securitygen1.py` | `sara_security/{king,paladin,sheriff,stables,...}.py` |
| `Sara_sdk.py` (archive) | `sara_sdk/Sara_sdk.gen1.py` | `sara_sdk/{dispatch,protocols,ai_backend,...}.py` |
| BIOMETRIC_PROTOCOL_SPEC.md | Partial in sara_mamagen1.py | `sara_mama/biometrics.py` (full implementation) |
| gen0.5 function_maps | Partially implemented | See §6 for gaps |

---

## 9. Key Decisions for Your Review

1. **sara_common/ package** — Do you want a shared package, or should each pillar keep its own copy of ShuntFSM? (Shared is cleaner, pillar-local is more isolated.)

2. **Mechanic subsystem** — Lives in CONTROL now. Should it move to SDK (as an adapter) or become its own top-level module?

3. **Document composition** (write_docx, write_xlsx, etc.) — These are in CONTROL but feel like CORE I/O. Should they live in CORE, or in MAMA (since they produce "presentation" output)?

4. **Learning module** — LearnManager is a stub. Should learning live in CONTROL (as orchestration) or become its own cross-cutting module that CONTROL coordinates?

5. **Biometric implementation priority** — The BIOMETRIC_PROTOCOL_SPEC is detailed and personal. Should biometrics be Phase 1 of the rebuild, or should we stabilize the pillar decomposition first?

6. **Government pillar (Pillar 6)** — Referenced in the architecture log. Is this implemented anywhere, or is it a future concern?

---

---

## 10. Project Lineage — Where SARA's DNA Came From

The `coding projects` folder contains 8 other projects besides SARA, each contributing architectural DNA to what SARA became. Understanding these explains **why** certain things are in SARA and **where** they should live in the rebuild.

### Chronological Evolution

```
c# (scaffold)
  → ncrtech (first deterministic agent: SaraCore + SaraControl + FsmAgent in F#)
    → MODLES/NBS (SARA Gen0 workspace: pillars, microservices, NBS format)
      → slam (language substrate formalized: 25 kernel specs, SlamRuntime, CartiGene)
        → blenderide (creative tool integration → becomes Smithy concept)
          → biometric_ai_dev (facial recognition module, Nov 2025)
            → blanchfield_protocol (clinical journaling + 4FA security, Nov 2025)
              → disabilitymapper (WPF accessibility/tremor filtering for Parkinson's/TD)
                → project_mechanic (business automation, March 2026 → optional SARA-side adapter hooks; MechanicUI desktop client not shipped with SARA)
                  → SARA (current: all of the above unified under 5-pillar architecture)
```

### Per-Project → Pillar Mapping

| Precursor Project | What It Built | Where It Belongs in SARA |
|---|---|---|
| **ncrtech** | `SaraCore`, `SaraControl`, `FsmAgent` classes in F#; NBS file format; agent profile system ("Doc" + "Patersongen0"); bare-metal `.NET` runtime spec | **CORE** (NBS format), **CONTROL** (FSM agent, dispatch), **sara_common** (ShuntFSM lineage) |
| **MODLES/NBS** | Gen0/Gen1 pillar development; `sara_stack/` microservices (api-gateway, llm-backend, hardware-discovery, muse-service); `SARA.Gen1.Cockpit` WPF; `sara-mapper/device_probe/`; compliance audits | **All pillars** (this IS earlier SARA); microservices architecture → informs HTTP bridge and SDK adapters |
| **slam** | SLAM language (Puppy/Dog/Breed/Kennel/Trainer/Funk types); SXF capsules; compiler pipeline; KING lockout; Tagger provenance; `sara_sdk/proto_lingua/` with CartiGene math; solution file literally `SARA.sln` | **CORE** (Proto-Lingua, data types, resonance validation), **SECURITY** (KING lockout, Tagger), **SDK** (SlamRuntime, proto_lingua core), **Pillar 6/Government** (SLAM distribution control) |
| **blenderide** | Blender-as-IDE add-on; Ollama/DeepSeek integration; `OllamaBlenderBridge` | **SDK** (Smithy/Blender bridge), **MAMA** (AI LLC bridge definitions — ollama_bridge.slam came from here) |
| **biometric_ai_dev** | ORB facial recognition; multi-factor auth (face + PIN); AuthMode enum; camera capture with graceful fallback; FastAPI biometric server; embedded (Raspberry Pi) variant; wearable (Android/iOS) variant | **MAMA** (biometric context extraction), **SECURITY** (trust/auth gating), **SDK** (device-specific biometric adapters: embedded, wearable, server) |
| **blanchfield_protocol** | 4-Factor Auth (F1 challenge + F2 biometric + F3 ephemeral key + F4 hardware); persistent 15-min background tracking; local SQLite first + cloud sync; clinical/creative data segregation; "Flo" persona; edge gateway (BLG) | **SECURITY** (4FA → King/Paladin/Sheriff/Stables chain), **MAMA** (constant monitoring, persona), **CORE** (local-first NBS philosophy), **SDK** (edge gateway → ARM adapter) |
| **disabilitymapper** | WPF Raw Input + WM_POINTER hooks; tremor filtering; debounce; steno chord engine; gamepad/joystick/mouse/touch remapping; device profile persistence; built specifically for Parkinson's and Tardive Dyskinesia | **MAMA** (biometric tremor detection → BIOMETRIC_PROTOCOL_SPEC.md), **SDK** (HidService, device profiles, hardware_profiles.py), **CORE** (profile persistence) |
| **project_mechanic** | FastAPI business ops; Google Sheets/Calendar/Email; Gemini AI + Ollama fallback; PDF-to-Excel; browser automation; VoIP/SIP calling; C# terminal UI (external repo; not bundled with SARA) | **SDK** (mechanic adapters — `mechanic_calendar_run`, `mechanic_email_run`, etc.), **CONTROL** (optional routing, documented in `PROJECT_MECHANIC_FOLD_IN_PREP.md`) |

### Key Insight: The Biometric Pipeline's True Lineage

The biometric/disability adaptation system wasn't an afterthought — it has a **three-project pedigree**:

1. **biometric_ai_dev** (Nov 2025) — Built standalone facial recognition with ORB feature matching
2. **blanchfield_protocol** (Nov 2025) — Wrapped it in 4-Factor Auth for clinical use, added persistent background tracking
3. **disabilitymapper** (2026) — Built the physical input layer: Raw Input hooks, tremor filtering, steno chords, device profiles for Parkinson's/TD

These three converge in SARA as:
- `BIOMETRIC_PROTOCOL_SPEC.md` (the spec — tremor signatures, TechBallCamp drills, Kalman filtering)
- `sara_mama/sara_mamagen1.py` → `biometrics.py` (the MAMA presentation layer)
- `sara_security/` → trust gating (the 4FA evolved into King/Paladin/Sheriff)
- `sara_sdk/` → device adapters (HidService, hardware profiles, wearable/embedded variants)

### Key Insight: ncrtech Was the First SARA

The `ncrtech` project contains F# classes literally named `SaraCore` and `SaraControl` with an `FsmAgent` — this is SARA's first implementation. Its NBS format (`nbs_id`, `nbs_meta`, `nexus_resonance_radius`, `nexus_stability`) became CORE's canonical format. Its agent profile system ("Doc" as user, "Patersongen0" as agent) is the lineage of CONTROL's identity resolution and persona loading.

### Key Insight: SLAM Is Not Separate From SARA

The `slam` repo's solution file is `SARA.sln`. It contains `sara_sdk/proto_lingua/` with CartiGene (resonance stabilization math). SLAM's type system (Puppy, Dog, Breed, Kennel) IS Proto-Lingua. The 25 kernel spec versions document the evolution of SARA's data substrate. The rebuild should treat SLAM not as an external dependency but as **CORE's mathematical and data-type foundation**.

### Key Insight: Project Mechanic and SARA (Optional Bridge)

`PROJECT_MECHANIC_FOLD_IN_PREP.md` (dated 2026-03-31) documents **optional** Control routing when an external Mechanic stack is present; the Mechanic desktop client is **not** part of SARA shipping. The mechanic functions in `sara_controlgen1.py` (mechanic_calendar_run_con, mechanic_email_run_con, etc.) are thin Control wrappers — long term they should live in **SDK** as adapters, not in CONTROL, while the actual Mechanic services remain in the separate Mechanic repository.

---

## 11. Updated Rebuild Priorities (Incorporating Lineage)

Given the full lineage, the rebuild order should respect where capabilities **actually came from**:

### Phase 0: Shared Infrastructure
- Canonical `ShuntFSM` in `sara_common/` (lineage: ncrtech `FsmAgent` → MODLES/NBS → current)
- Shared types, shunt header validation

### Phase 1: CORE (The Engine) — Foundation from ncrtech + SLAM
- NBS format (from ncrtech's original implementation)
- Proto-Lingua / data types (from SLAM's Puppy/Dog/Breed/Kennel)
- CartiGene resonance math (from SLAM's proto_lingua/core.py)
- File I/O, persistence, compression
- Profile storage (from disabilitymapper's ProfileStore pattern)

### Phase 2: SECURITY (The Keep) — Foundation from blanchfield_protocol + biometric_ai_dev
- King/Paladin/Sheriff/Stables chain (evolved from 4FA: F1/F2/F3/F4)
- Trust policy, sovereignty checks
- Biometric auth gating (from biometric_ai_dev's AuthMode/BiometricAuth)
- Audit/scan/quarantine
- Restore the 10 Gen0 security roles (Paladin, Sheriff, Deputy, Archeologist, Conservator, Restoration, Envoy, King, SecurityKeep + Scout/Yard/House/Mapper)

### Phase 3: CONTROL (The Loom) — Foundation from ncrtech's FsmAgent
- Strip it to orchestration only
- Dispatch, routing, session management
- Security chain integration
- AMIP/AMIPI routing
- LearnManager (wired to real functions)
- Remove everything that doesn't belong

### Phase 4: MAMA (The Gate) — Foundation from disabilitymapper + biometric_ai_dev + blanchfield_protocol
- Biometric pipeline: tremor detection → baseline calibration → adaptive filtering → progression tracking
- TechBallCamp drill framework (from BIOMETRIC_PROTOCOL_SPEC.md)
- UX adaptation (constant biometrics, no opt-out)
- Presentation layer, reasoning overlay
- Jargon lexicon, PlainJain

### Phase 5: SDK (The Identity Assembler) — Foundation from project_mechanic + blenderide + SLAM
- Mechanic adapters (external `project_mechanic` stack when deployed; not shipped inside SARA)
- Blender/Smithy bridge (from blenderide)
- AI backend adapters (Ollama, Gemini — from project_mechanic and blenderide)
- Device adapters (from disabilitymapper's HidService pattern)
- SLAM runtime integration
- Missing actionmap functions: `build_local_bucey_shunt`, `send_bucey_shunt`

### Phase 6: Integration + HTTP Bridge
- Wire `control_server()` → `dispatch()`
- HTTP bridge (already exists as `sara_control_http.py`)
- Cross-pillar shunt verification
- Biometric → MAMA → CONTROL → CORE persistence pipeline
- End-to-end security harness

---

## 12. Updated Decisions for Your Review

1. **sara_common/ package** — Shared ShuntFSM, types, header validation. (Recommended: yes, it traces back to ncrtech's single FsmAgent definition.)

2. **Mechanic adapters** — Move from CONTROL to SDK. (Confirmed: `PROJECT_MECHANIC_FOLD_IN_PREP.md` says "invoked through Control routing" — Control routes, SDK executes.)

3. **Document composition** — Move from CONTROL to CORE. (These are file I/O operations; CORE is the engine.)

4. **Learning module** — Keep in CONTROL as orchestration, but wire to CORE for persistence and MAMA for biometric context. (LearnManager needs real try/reflect/adapt functions, not stubs.)

5. **Biometrics priority** — Phase 4, after pillar decomposition. (The three-project pedigree means the spec is solid; we stabilize the pillars first, then implement the full pipeline from BIOMETRIC_PROTOCOL_SPEC.md.)

6. **Pillar 6 (Government)** — Policy documentation for now. (The SLAM kernel specs define the encoding/distribution rules; implementation is future work.)

7. **disabilitymapper integration** — The WPF Raw Input / HidService code should inform SDK device adapters. The tremor filtering algorithms should inform MAMA's `biometrics.py`. (These are the "rods in dirt" — the physical layer.)

8. **SLAM substrate** — Treat as CORE's mathematical foundation, not a separate project. Proto-Lingua and CartiGene are CORE's data type system. (The solution file is literally `SARA.sln`.)

---

*This document is the map. The monoliths are the territory. Eight precursor projects are the geological survey. Let's rebuild SARA the way she was always meant to be.*

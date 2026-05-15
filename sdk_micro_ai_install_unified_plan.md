# SDK Unified Micro-AI Install Plan (Gen0/Gen1 Bridge)

This SDK setup treats the current micro-AI runtime as the universal installer payload for:
- wearable installs
- ARM board installs
- TV installs
- laptop/PC installs
- backend-on-existing-OS installs

## What is now wired
- Unified planner module:
  - `claywork/saragen0finish/sara_sdk/common/micro_ai_installer.py`
- SDK core dispatch can emit install plans via actions:
  - `install_micro_ai`, `prepare_install`, `install_plan`
  - file: `claywork/saragen0finish/sara_sdk/Sara_sdk.gen1.py`
- Lane adapters now expose plan + dry-run install methods:
  - Android: `sara_sdk/android/device_api.py`
  - iOS: `sara_sdk/ios/device_api.py`
  - TV: `sara_sdk/tv/dashboard_api.py`
  - PC: `sara_sdk/systems/pc_adapter.py`
  - Server/backend: `sara_sdk/systems/server_adapter.py`
  - ARM: `sara_sdk/arm/board_api.py`

## Target adaptation behavior
- Planner selects runtime profile by target + host constraints.
- Continuity tier defaults are mapped per class:
  - compact: wearable/arm/mobile constrained
  - balanced: tv/pc
  - extended: backend/server
- Repeatability requirement forces strict deterministic inference profile.
- Post-install defaults currently set:
  - replay_mode_default = true
  - ollama_policy_default = backup
  - self_tuning = true

## Example SDK call shape
- protocol: `arm` (or android/ios/tv/server/device)
- action: `install_micro_ai`
- payload fields (optional):
  - `install_target`
  - `ram_mb`
  - `storage_mb`
  - `continuity_tier`
  - `requires_repeatability`

Result includes `local_result.install_dry_run.plan` with host-adaptive steps.

## Remaining for GN0 implementation pass
1. Connect planner output to actual package writer / installer scripts per target OS.
2. Add signed artifact verification stage.
3. Add rollback checkpoints and post-install health probes.
4. Add service registration templates for backend installs.
5. Add encrypted continuity store options per target class.

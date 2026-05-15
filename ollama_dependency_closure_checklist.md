# Ollama Dependency Closure Checklist (Uninstall-Ready)

Scope: local runtime closure for Gen1 CONTROL/SDK/MAMA pathways.
Policy target: no accidental Ollama execution unless explicitly opted in.

## 1. Runtime policy gate (completed)
- [x] CONTROL blocks implicit `ollama_local` selection unless `SARA_ALLOW_OLLAMA` is truthy.
- [x] CONTROL falls back deterministically to non-Ollama AMI lane.
- [x] SDK AMIPI dispatch blocks Ollama AMI by default and reroutes to non-Ollama AMI.
- [x] Envoy web agent runtime treats Ollama as disabled by policy and falls back to heuristic output.
- [x] Envoy backend health reports Ollama as `disabled` when policy is off.

## 2. Profile and manifest posture (completed)
- [x] MAMA model profile notes now mark Ollama as opt-in only.
- [x] Existing bridge references are preserved for compatibility, but no longer active by default.

## 3. Verification sequence (run in order)
- [ ] Ensure environment does NOT set `SARA_ALLOW_OLLAMA`.
- [ ] Run control protocol gate and confirm pass.
- [ ] Trigger a route with payload `backend=ollama_local`; verify resolved backend is non-Ollama.
- [ ] Run envoy backend health; verify Ollama entries show `disabled`.
- [ ] Run a blind agent cycle; verify outputs source as `local` or `fallback` (not live Ollama).

## 4. Uninstall-ready cutover (manual ops)
- [ ] Stop any running Ollama services.
- [ ] Remove Ollama package/binary from host machine.
- [ ] Remove local model caches and residual data directories.
- [ ] Keep `SARA_ALLOW_OLLAMA` unset to preserve hard-off posture.

## 5. Optional hard-removal follow-up (future pass)
- [ ] Remove `ollama_local` IDs from AMI catalogs after all downstream consumers are migrated.
- [ ] Remove `ollama_default` profile entries and bridge files after spec update approval.
- [ ] Rewrite historical sample data labels if you want a no-Ollama artifact set.

## Toggle semantics
- Default (safe): Ollama disabled (`SARA_OLLAMA_POLICY=off`).
- Situational backup mode (recommended during experiments):
  - PowerShell session: `$env:SARA_OLLAMA_POLICY='backup'`
  - Ollama is only used where request/profile explicitly allows backup.
- Full opt-in mode (temporary):
  - PowerShell session: `$env:SARA_OLLAMA_POLICY='full'`
- Legacy toggle compatibility:
  - `$env:SARA_ALLOW_OLLAMA='1'` behaves like full mode if `SARA_OLLAMA_POLICY` is unset.
- Disable again:
  - `Remove-Item Env:SARA_OLLAMA_POLICY -ErrorAction SilentlyContinue`
  - `Remove-Item Env:SARA_ALLOW_OLLAMA -ErrorAction SilentlyContinue`

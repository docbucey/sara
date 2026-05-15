"""
settings_protocol.py
SARA Settings Protocol (Gen1)

Purpose:
- Manage persistent user/system/global settings for all SARA pillars.
- Enable/disable and configure "night shift" protocol for WFH automation.
- Provide add/get/update/remove settings API.

Features:
- JSON-backed settings store (settings.json).
- Settings are namespaced (core, control, security, mama, custom).
- Night shift protocol: If enabled and WFH queue has jobs, snapshot open apps, clear system management, run distributed/multithreaded processing, ignore 3% CPU rule except for terminal cooling, process queue, then sleep/restore.
- CLI/dispatcher integration ready.
"""
import os
import json
import threading
from typing import Any, Dict, Optional

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), 'settings.json')

class SettingsProtocol:
    # --- Bridge AI Role Assignments ---
    def set_bridge_roles(self, ai_name: str, roles: list):
        with self._lock:
            self._settings.setdefault('bridge_roles', {})[ai_name] = roles
            self._save_settings()
        return {'status': 'PASS', 'bridge_roles': self._settings['bridge_roles']}

    def get_bridge_roles(self, ai_name: Optional[str] = None):
        roles = self._settings.get('bridge_roles', {})
        if ai_name:
            return roles.get(ai_name, [])
        return roles

    # --- SARA Training Mode ---
    def enable_training_mode(self, targets: Optional[list] = None):
        with self._lock:
            self._settings['training_mode'] = {'enabled': True, 'targets': targets or []}
            self._save_settings()
        return {'status': 'PASS', 'training_mode': self._settings['training_mode']}

    def disable_training_mode(self):
        with self._lock:
            self._settings['training_mode'] = {'enabled': False, 'targets': []}
            self._save_settings()
        return {'status': 'PASS', 'training_mode': self._settings['training_mode']}

    def training_mode_enabled(self) -> bool:
        return bool(self._settings.get('training_mode', {}).get('enabled', False))

    def get_training_targets(self) -> list:
        return self._settings.get('training_mode', {}).get('targets', [])

    def __init__(self):
        self._lock = threading.RLock()
        self._settings = self._load_settings()

    def _load_settings(self) -> Dict[str, Any]:
        if not os.path.exists(SETTINGS_FILE):
            return {}
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_settings(self):
        with self._lock:
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, indent=2)

    def get(self, key: str, default: Any = None) -> Any:
        return self._settings.get(key, default)

    def set(self, key: str, value: Any):
        with self._lock:
            self._settings[key] = value
            self._save_settings()
        return {'status': 'PASS', 'key': key, 'value': value}

    def remove(self, key: str):
        with self._lock:
            if key in self._settings:
                del self._settings[key]
                self._save_settings()
                return {'status': 'PASS', 'removed': key}
            return {'status': 'ERROR', 'reason': 'Key not found'}

    def all(self) -> Dict[str, Any]:
        return dict(self._settings)

    # --- Night Shift Protocol ---
    def night_shift_enabled(self) -> bool:
        return bool(self._settings.get('night_shift', {}).get('enabled', False))

    def enable_night_shift(self, config: Optional[Dict[str, Any]] = None):
        with self._lock:
            self._settings.setdefault('night_shift', {})['enabled'] = True
            if config:
                self._settings['night_shift'].update(config)
            self._save_settings()
        return {'status': 'PASS', 'night_shift': self._settings['night_shift']}

    def disable_night_shift(self):
        with self._lock:
            self._settings.setdefault('night_shift', {})['enabled'] = False
            self._save_settings()
        return {'status': 'PASS', 'night_shift': self._settings['night_shift']}

    def run_night_shift(self, wfh_queue: list, snapshot_fn, process_fn, cooling_fn):
        if not self.night_shift_enabled() or not wfh_queue:
            return {'status': 'SKIP', 'reason': 'Night shift not enabled or queue empty'}
        # 1. Snapshot open apps
        snapshot = snapshot_fn()
        # 2. Clear system management (stub)
        # 3. Start distributed/multithreaded processing
        threads = []
        for job in wfh_queue:
            t = threading.Thread(target=process_fn, args=(job,))
            t.start()
            threads.append(t)
        # 4. Ignore 3% CPU rule except for terminal cooling
        cooling_fn()
        for t in threads:
            t.join()
        # 5. Restore state or allow sleep
        return {'status': 'DONE', 'snapshot': snapshot, 'jobs_processed': len(wfh_queue)}

    # --- ADA voice I-O (read-aloud + STT contract; blind / fallback path) ---
    def get_ada_voice_profile(self) -> Dict[str, Any]:
        from sara_core.ada_voice_profile import merge_with_defaults

        raw = self._settings.get("ada_voice_profile")
        if not isinstance(raw, dict):
            raw = {}
        return merge_with_defaults(raw)

    def set_ada_voice_profile(
        self,
        partial: Optional[Dict[str, Any]] = None,
        preset: Optional[str] = None,
    ) -> Dict[str, Any]:
        from sara_core.ada_voice_profile import apply_preset, merge_with_defaults

        with self._lock:
            stored = self._settings.get("ada_voice_profile")
            if not isinstance(stored, dict):
                stored = {}
            merged = merge_with_defaults(stored)
            if preset:
                merged = apply_preset(str(preset), {} if str(preset) == "factory_reset" else merged)
            if partial and isinstance(partial, dict):
                merged = merge_with_defaults({**merged, **partial})
            self._settings["ada_voice_profile"] = merged
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self._settings, f, indent=2)
        return merged

# Example usage:
# settings = SettingsProtocol()
# settings.set('core.backup_frequency', 'daily')
# settings.enable_night_shift({'cooling_policy': 'terminal_only'})
# settings.run_night_shift(wfh_queue, snapshot_fn, process_fn, cooling_fn)

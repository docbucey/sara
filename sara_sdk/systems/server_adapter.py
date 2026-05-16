"""Server adapter stubs for SARA SDK Gen1."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any, Dict


def _load_installer():
    installer_path = Path(__file__).resolve().parents[1] / "common" / "micro_ai_installer.py"
    if not installer_path.exists():
        return None
    spec = importlib.util.spec_from_file_location("sara_sdk_server_installer", str(installer_path))
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class ServerAdapter:
    """Server lane with host-adaptive micro-AI install planning."""

    def describe(self) -> Dict[str, Any]:
        return {
            "status": "ready",
            "system": "server",
            "note": "Server lane can emit host-adaptive install plans for backend micro-AI deployment.",
        }

    def plan_install(self, payload: Dict[str, Any] | None = None, machine_profile: Dict[str, Any] | None = None) -> Dict[str, Any]:
        installer = _load_installer()
        if installer is None or not hasattr(installer, "plan_micro_ai_install"):
            return {"success": False, "status": "INSTALLER_UNAVAILABLE", "target": "server"}
        return installer.plan_micro_ai_install(target="server", payload=payload or {}, machine_profile=machine_profile or {})

    def dry_run_install(self, payload: Dict[str, Any] | None = None, machine_profile: Dict[str, Any] | None = None) -> Dict[str, Any]:
        installer = _load_installer()
        if installer is None or not hasattr(installer, "apply_micro_ai_install_dry_run"):
            return {"success": False, "status": "INSTALLER_UNAVAILABLE", "target": "server"}
        return installer.apply_micro_ai_install_dry_run(target="server", payload=payload or {}, machine_profile=machine_profile or {})

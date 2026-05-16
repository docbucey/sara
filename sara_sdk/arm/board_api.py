"""ARM board mode and filesystem prep helpers for SARA SDK Gen1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List
import importlib.util


class ARMBoardAPI:
    """Manifest-driven ARM board helpers for repeatable experimentation setups."""

    def __init__(self, manifest_path: str | None = None):
        default_manifest = (
            Path(__file__).resolve().parent.parent
            / "kernels"
            / "reference_kernel"
            / "arm_boards"
            / "arm_modes.json"
        )
        self.manifest_path = Path(manifest_path) if manifest_path else default_manifest

    def _load_manifest(self) -> Dict[str, Any]:
        if not self.manifest_path.exists():
            return {"version": "missing", "modes": []}
        try:
            return json.loads(self.manifest_path.read_text(encoding="utf-8"))
        except Exception:
            return {"version": "invalid", "modes": []}

    def list_modes(self) -> List[Dict[str, Any]]:
        manifest = self._load_manifest()
        modes = manifest.get("modes") if isinstance(manifest.get("modes"), list) else []
        out: List[Dict[str, Any]] = []
        for mode in modes:
            if not isinstance(mode, dict):
                continue
            out.append(
                {
                    "name": str(mode.get("name") or ""),
                    "board": str(mode.get("board") or ""),
                    "filesystem": str(mode.get("filesystem") or ""),
                    "purpose": str(mode.get("purpose") or ""),
                }
            )
        return out

    def get_mode(self, mode_name: str) -> Dict[str, Any] | None:
        mode_name = str(mode_name or "").strip().lower()
        if not mode_name:
            return None
        for mode in self.list_modes_full():
            if str(mode.get("name") or "").strip().lower() == mode_name:
                return mode
        return None

    def list_modes_full(self) -> List[Dict[str, Any]]:
        manifest = self._load_manifest()
        modes = manifest.get("modes") if isinstance(manifest.get("modes"), list) else []
        return [m for m in modes if isinstance(m, dict)]

    def prepare_mode_filesystem(self, mode_name: str, workspace_root: str | None = None, dry_run: bool = False) -> Dict[str, Any]:
        mode = self.get_mode(mode_name)
        if mode is None:
            return {
                "success": False,
                "status": "MODE_NOT_FOUND",
                "requested_mode": mode_name,
                "available_modes": [m.get("name") for m in self.list_modes()],
            }

        arm_boards_root = self.manifest_path.parent
        target_root = Path(workspace_root) if workspace_root else (arm_boards_root / "workspaces")
        mode_root = target_root / str(mode.get("name"))

        directories = mode.get("directories") if isinstance(mode.get("directories"), list) else []
        files = mode.get("files") if isinstance(mode.get("files"), list) else []

        created_dirs: List[str] = []
        created_files: List[str] = []

        if not dry_run:
            mode_root.mkdir(parents=True, exist_ok=True)

        for rel_dir in directories:
            rel_dir_s = str(rel_dir or "").strip().replace("\\", "/")
            if not rel_dir_s:
                continue
            abs_dir = mode_root / rel_dir_s
            if not dry_run:
                abs_dir.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(abs_dir))

        for file_def in files:
            if not isinstance(file_def, dict):
                continue
            rel_path = str(file_def.get("path") or "").strip().replace("\\", "/")
            if not rel_path:
                continue
            content = str(file_def.get("content") or "")
            abs_path = mode_root / rel_path
            if not dry_run:
                abs_path.parent.mkdir(parents=True, exist_ok=True)
                abs_path.write_text(content, encoding="utf-8")
            created_files.append(str(abs_path))

        return {
            "success": True,
            "status": "MODE_FILESYSTEM_READY" if not dry_run else "MODE_FILESYSTEM_DRY_RUN",
            "mode": str(mode.get("name") or ""),
            "board": str(mode.get("board") or ""),
            "filesystem": str(mode.get("filesystem") or ""),
            "workspace_root": str(mode_root),
            "directories": created_dirs,
            "files": created_files,
            "dry_run": bool(dry_run),
        }

    def _load_installer(self):
        installer_path = Path(__file__).resolve().parents[1] / "common" / "micro_ai_installer.py"
        if not installer_path.exists():
            return None
        spec = importlib.util.spec_from_file_location("sara_sdk_arm_installer", str(installer_path))
        if spec is None or spec.loader is None:
            return None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def plan_install(self, payload: Dict[str, Any] | None = None, machine_profile: Dict[str, Any] | None = None) -> Dict[str, Any]:
        installer = self._load_installer()
        if installer is None or not hasattr(installer, "plan_micro_ai_install"):
            return {"success": False, "status": "INSTALLER_UNAVAILABLE", "target": "arm"}
        return installer.plan_micro_ai_install(target="arm", payload=payload or {}, machine_profile=machine_profile or {})

    def dry_run_install(self, payload: Dict[str, Any] | None = None, machine_profile: Dict[str, Any] | None = None) -> Dict[str, Any]:
        installer = self._load_installer()
        if installer is None or not hasattr(installer, "apply_micro_ai_install_dry_run"):
            return {"success": False, "status": "INSTALLER_UNAVAILABLE", "target": "arm"}
        return installer.apply_micro_ai_install_dry_run(target="arm", payload=payload or {}, machine_profile=machine_profile or {})

    def describe(self) -> Dict[str, Any]:
        modes = self.list_modes()
        return {
            "status": "ready",
            "platform": "arm",
            "manifest_path": str(self.manifest_path),
            "mode_count": len(modes),
            "modes": modes,
            "note": "ARM mode API provides repeatable filesystem-ready workspaces for board experiments.",
        }


if __name__ == "__main__":
    api = ARMBoardAPI()
    print(json.dumps(api.describe(), indent=2))

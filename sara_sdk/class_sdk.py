"""SDK Class: main SaraSdkGen1 wrapper and artifact writers."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sara_sdk.identity_sdk import SDK_PILLAR_NAME, SDK_VERSION, sdk_status
from sara_sdk.dispatch_sdk import dispatch_sdk_protocol, dispatch_amipi_backend


class SaraSdkGen1:
    """Minimal wrapper for future Gen1 SDK expansion."""

    def __init__(self) -> None:
        self.pillar = SDK_PILLAR_NAME
        self.version = SDK_VERSION

    def status(self) -> Dict[str, Any]:
        return sdk_status()

    def dispatch(self, protocol: str, action: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return dispatch_sdk_protocol(protocol, action, payload)

    def dispatch_amipi(self, backend_ami: str, action: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return dispatch_amipi_backend(backend_ami, action, payload)


def _write_sdk_artifacts(status: str, reached: bool, reason: str) -> None:
    """Write/update the three pillar artifact JSON files for SDK."""
    _here = os.path.dirname(os.path.abspath(__file__))
    _local = {
        "pillar": "sara_sdk",
        "file": "Sara_sdk.gen1.py",
        "status": status,
        "reached": reached,
        "reason": reason,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    _distant = {
        "pillar": "sara_sdk",
        "file": "Sara_sdk.gen1.py",
        "status": status,
        "reached": reached,
        "note": reason,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    _master = {"pillar": "sara_sdk", "final_status": status, "local": _local, "distant": _distant}
    for fname, obj in [("result.meta.json", _local), ("distant_end.json", _distant), ("master_result.json", _master)]:
        try:
            with open(os.path.join(_here, fname), "w", encoding="utf-8") as f:
                json.dump(obj, f, ensure_ascii=False, indent=2)
        except Exception:
            pass


def _load_micro_ai_installer_sdk():
    import importlib.util
    installer_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "common", "micro_ai_installer.py")
    if not os.path.exists(installer_path):
        return None
    spec = importlib.util.spec_from_file_location("sara_sdk_micro_ai_installer", installer_path)
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

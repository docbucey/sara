"""CORE Legacy: backward-compatible wrappers from Gen0."""
import os
import json
import importlib.util
from types import ModuleType
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timezone


# These constants are referenced by the legacy functions; imported from the
# monolith's module-level scope at runtime. When used standalone, callers
# should set NBS_BASE_DIR, SYSTEM_CORE_PROJECT_NAME, and INTERNAL_FILE_VERSION
# before calling these functions, or import them from the main module.
try:
    from .sara_coregen1 import (
        NBS_BASE_DIR,
        SYSTEM_CORE_PROJECT_NAME,
        INTERNAL_FILE_VERSION,
        _sanitize_name,
        _iso_now,
    )
except ImportError:
    NBS_BASE_DIR = os.path.join(os.getcwd(), "nbs_projects")
    SYSTEM_CORE_PROJECT_NAME = "system_core"
    INTERNAL_FILE_VERSION = "1.0"

    def _iso_now() -> str:
        return datetime.now(timezone.utc).isoformat()

    import re
    def _sanitize_name(value: Any) -> str:
        return re.sub(r"[^a-zA-Z0-9_\-]", "_", str(value)).strip("_")


############################################################
# Legacy Gen0 Compatibility Helpers (from Sara_core.py)
# These do NOT override or change Gen1 logic. Use only for
# compatibility or extension purposes. Safe to remove if not needed.
############################################################

def _load_core_module_legacy() -> ModuleType:
    """
    Dynamic loader for Gen1 core (legacy compatibility).
    Not used by Gen1 logic, but available for runtime extension.
    """
    _THIS_DIR = os.path.dirname(os.path.abspath(__file__))
    _CORE_PATH = os.path.join(
        _THIS_DIR,
        "sara_coregn1.py",
    )
    spec = importlib.util.spec_from_file_location("sara_coregn1_runtime", _CORE_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load Core module spec at {_CORE_PATH}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

# Gen0-style create_nbs_file (legacy, do not use for new code)
def create_nbs_file_legacy(
    project_name: str,
    relative_path: str,
    content: Any,
    meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    proj = _sanitize_name(project_name or SYSTEM_CORE_PROJECT_NAME)
    abs_dir = os.path.join(NBS_BASE_DIR, proj)
    abs_path = os.path.join(abs_dir, relative_path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)

    tags = []
    source = "core"
    nbs_type = "generic"
    if isinstance(meta, dict):
        tags = list(meta.get("tags", []))
        source = str(meta.get("source", "core"))
        nbs_type = str(meta.get("nbs_type", "generic"))

    obj = {
        "nbs_meta": {
            "nbs_id": f"{int(datetime.now(timezone.utc).timestamp())}_{proj}_nbs",
            "nbs_type": nbs_type,
            "nbs_gen": "gen0",
            "nbs_ver": INTERNAL_FILE_VERSION,
            "created_at": _iso_now(),
            "source": source,
            "project_name": proj,
            "tags": tags,
            "nexus_resonance_radius": 0.0,
            "nexus_stability": "stable",
        },
        "content": content or {},
        "file_version": INTERNAL_FILE_VERSION,
        "last_modified": _iso_now(),
    }

    with open(abs_path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

    return {
        "success": True,
        "data": obj,
        "reference": {
            "file_path": abs_path,
            "project": proj,
            "created_at": _iso_now(),
        },
    }

# Gen0-style validate_resonance (legacy, do not use for new code)
def validate_resonance_legacy(data: Dict[str, Any], max_radius: float = 1.0) -> Tuple[bool, str]:
    resonance_radius = float(data.get("_nexus_resonance_radius_puppy", 0.0))
    if resonance_radius <= max_radius:
        return True, "stable"
    return False, "dissonant"

# Gen0-style Proto-Lingua helpers (already present in Gen1, but exposed for compatibility)
def _classify_value_suffix_legacy(value: Any) -> str:
    if isinstance(value, dict):
        return "_breed"
    if isinstance(value, list):
        return "_dog_array"
    return "_puppy"

def _to_proto_lingua_legacy(data: Any, preferred_breed: Optional[str] = None) -> Any:
    if isinstance(data, dict):
        out: Dict[str, Any] = {}
        if preferred_breed:
            out["__file_breed"] = preferred_breed
        for k, v in data.items():
            new_key = f"{k}{_classify_value_suffix_legacy(v)}"
            if isinstance(v, dict):
                out[new_key] = _to_proto_lingua_legacy(v)
            elif isinstance(v, list):
                out[new_key] = [_to_proto_lingua_legacy(i) if isinstance(i, dict) else i for i in v]
            else:
                out[new_key] = v
        out.setdefault("_nexus_resonance_radius_puppy", 0.0)
        out.setdefault("_nexus_stability_puppy", "stable")
        return out
    if isinstance(data, list):
        return [_to_proto_lingua_legacy(i) if isinstance(i, dict) else i for i in data]
    return data

# End of Gen0 legacy helpers

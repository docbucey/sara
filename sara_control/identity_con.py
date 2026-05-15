"""
SARA Control — Identity resolution, persona loading, narrative profile management.
Extracted from sara_controlgen1.py.
"""
import os
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

try:
    from sara_control.loader_con import _load_core_module
    _core = _load_core_module()
    if _core is None:
        raise ImportError("Core module file not found")
    create_nbs_file = _core.create_nbs_file
    NBS_BASE_DIR = _core.NBS_BASE_DIR
    SYSTEM_CORE_PROJECT_NAME = _core.SYSTEM_CORE_PROJECT_NAME
except Exception:
    _core = None
    def create_nbs_file(project_name, relative_path, content, meta=None):
        return {"success": False, "error": "Core not loaded"}
    NBS_BASE_DIR = os.path.join(os.path.expanduser("~"), "sara_nbs")
    SYSTEM_CORE_PROJECT_NAME = "sara_core_project"


def _iso_now_con() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_persona_con(con_project: str = SYSTEM_CORE_PROJECT_NAME) -> Dict[str, Any]:
    """
    Load Control persona (protocol-droid female style), English US.
    Returns persona dict; if missing, creates a minimal default JSON on disk.
    """
    con_persona_dir = os.path.join(NBS_BASE_DIR, con_project, "control", "persona")
    os.makedirs(con_persona_dir, exist_ok=True)
    con_persona_path = os.path.join(con_persona_dir, "persona_protocol_droid_gen0.json")

    if not os.path.exists(con_persona_path):
        con_persona_default = {
            "identity": {"name": "SARA", "persona": "protocol_droid_female", "language": "en-US"},
            "tone": {"polite": True, "precise": True, "formal": True},
            "priorities": ["human_owner", "sara_assistant", "environment", "tools"],
            "policies": {
                "ask_before_destructive": True,
                "log_session_events": True,
                "nbs_array_first": True,
            },
            "created_at": _iso_now_con(),
        }
        with open(con_persona_path, "w", encoding="utf-8") as f:
            json.dump(con_persona_default, f, ensure_ascii=False, indent=2)

    with open(con_persona_path, "r", encoding="utf-8") as f:
        con_persona = json.load(f)
    return con_persona


def identity_resolve_con(con_project: str = SYSTEM_CORE_PROJECT_NAME) -> Dict[str, Any]:
    """
    Resolve common identity sheet paths for user/SARA/machine.
    """
    con_identity_dir = os.path.join(NBS_BASE_DIR, con_project, "identity")
    return {
        "user": os.path.join(con_identity_dir, "user", "doc_bucey_profile_gen0_1.0_nbs.json"),
        "sara": os.path.join(con_identity_dir, "sara", "sara_profile_gen0_1.0_nbs.json"),
        "machine": os.path.join(con_identity_dir, "machine", "pc_host_profile_gen0_1.0_nbs.json"),
    }


def ensure_narrative_profile_con(con_project: str = SYSTEM_CORE_PROJECT_NAME) -> Dict[str, Any]:
    """
    Ensure a project-level narrative profile exists and reflects current persona & identity links.
    Creates `narrative_profile_gen0_1.0_nbs.json` under project/narrative if missing.
    """
    con_rel = os.path.join("narrative", "narrative_profile_gen0_1.0_nbs.json")
    con_abs = os.path.join(NBS_BASE_DIR, con_project, con_rel)
    if os.path.exists(con_abs):
        return {"success": True, "reference": {"file_path": con_abs}, "created": False}

    con_persona = load_persona_con(con_project)
    ids = identity_resolve_con(con_project)
    links = []
    for role, path in ids.items():
        if os.path.exists(path):
            links.append({"role": role, "path": path})

    con_content = {
        "narrative_profile": {
            "project": con_project,
            "created_at": _iso_now_con(),
            "sessions_total": 0,
            "last_session_path": None,
            "persona_snapshot": con_persona,
            "identity_links": links,
        }
    }

    con_write = create_nbs_file(
        project_name=con_project,
        relative_path=con_rel,
        content=con_content,
        meta={
            "nbs_type": "narrative_profile",
            "tags": ["narrative", "profile"],
            "source": "control",
            "project_name": con_project,
        },
    )
    if isinstance(con_write, dict):
        ref = con_write.get("reference", {}).get("file_path")
    else:
        ref = con_abs
    return {"success": True, "reference": {"file_path": ref}, "created": True}


def sync_narrative_profile_con(con_project: str, con_narrative_path: str) -> Dict[str, Any]:
    """
    Update the narrative profile with the latest persona/identities and session reference.
    Safe to call even if profile is missing (it will be created on next session start).
    """
    con_rel = os.path.join("narrative", "narrative_profile_gen0_1.0_nbs.json")
    con_abs = os.path.join(NBS_BASE_DIR, con_project, con_rel)
    if not os.path.exists(con_abs):
        return {"success": False, "error": "narrative_profile missing", "path": con_abs}

    try:
        with open(con_abs, "r", encoding="utf-8") as f:
            obj = json.load(f)
    except Exception as e:
        return {"success": False, "error": f"read failure: {e}"}

    content = obj.setdefault("content", {})
    prof = content.setdefault("narrative_profile", {})

    prof["last_session_path"] = con_narrative_path
    prof["sessions_total"] = int(prof.get("sessions_total") or 0) + 1
    prof["updated_at"] = _iso_now_con()

    prof["persona_snapshot"] = load_persona_con(con_project)
    ids = identity_resolve_con(con_project)
    links = []
    for role, path in ids.items():
        if os.path.exists(path):
            links.append({"role": role, "path": path})
    prof["identity_links"] = links

    obj["last_modified"] = _iso_now_con()
    try:
        with open(con_abs, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
        return {"success": True, "reference": {"file_path": con_abs}}
    except Exception as e:
        return {"success": False, "error": f"write failure: {e}"}


def update_core_profile_with_ai_config(profile_type: str, profile_data: dict, immutable_fields: list):
    """
    Bridge function to update a core profile with ai_backend and training_config fields.
    Calls core's create_characterbase_nbs_profile and ensures config is stored.
    """
    try:
        core = _core
        if core is None:
            raise ImportError("Core not loaded")
    except (ImportError, NameError):
        return {"success": False, "error": "Core module not found"}
    data = dict(profile_data)
    if "ai_backend" in profile_data:
        data["ai_backend"] = profile_data["ai_backend"]
    if "training_config" in profile_data:
        data["training_config"] = profile_data["training_config"]
    return core.create_characterbase_nbs_profile(profile_type, data, immutable_fields)

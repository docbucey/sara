"""
SARA Control — Session lifecycle: start, append, end, checkpoint, heartbeat, array normalize.
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
    _to_proto_lingua = _core._to_proto_lingua
    validate_resonance = _core.validate_resonance
except Exception:
    _core = None
    def create_nbs_file(project_name, relative_path, content, meta=None):
        return {"success": False, "error": "Core not loaded"}
    NBS_BASE_DIR = os.path.join(os.path.expanduser("~"), "sara_nbs")
    SYSTEM_CORE_PROJECT_NAME = "sara_core_project"
    def _to_proto_lingua(obj, **kwargs): return obj
    def validate_resonance(obj): return True, "OK"


def _iso_now_con() -> str:
    return datetime.now(timezone.utc).isoformat()


def array_normalize_con(con_obj: Any) -> Any:
    """
    Normalize objects to be array-first friendly for NBS content.
    - None -> []
    - Scalars -> [scalar]
    - Dict -> [dict]
    - List -> list (unchanged)
    """
    if con_obj is None:
        return []
    if isinstance(con_obj, list):
        return con_obj
    if isinstance(con_obj, (str, int, float, bool)):
        return [con_obj]
    if isinstance(con_obj, dict):
        return [con_obj]
    return [str(con_obj)]


def start_session_con(con_project: str = SYSTEM_CORE_PROJECT_NAME,
                      con_session_note: Optional[str] = None) -> Dict[str, Any]:
    """
    Open a session narrative record linking user/SARA/machine + persona snapshot.
    Writes via Core's create_nbs_file using narrative_timeline type.
    Ensures Nexus metadata and Proto-Lingua compliance.
    """
    from sara_control.identity_con import load_persona_con, ensure_narrative_profile_con, sync_narrative_profile_con

    con_persona = load_persona_con(con_project)

    con_identity_dir = os.path.join(NBS_BASE_DIR, con_project, "identity")
    con_user_path = os.path.join(con_identity_dir, "user", "doc_bucey_profile_gen0_1.0_nbs.json")
    con_sara_path = os.path.join(con_identity_dir, "sara", "sara_profile_gen0_1.0_nbs.json")
    con_machine_path = os.path.join(con_identity_dir, "machine", "pc_host_profile_gen0_1.0_nbs.json")

    con_actors: List[Dict[str, Any]] = []
    if os.path.exists(con_user_path):
        con_actors.append({"role": "owner", "path": con_user_path, "tags": ["human", "owner"]})
    if os.path.exists(con_sara_path):
        con_actors.append({"role": "assistant", "path": con_sara_path, "tags": ["sara", "assistant"]})
    if os.path.exists(con_machine_path):
        con_actors.append({"role": "environment", "path": con_machine_path, "tags": ["machine", "host"]})

    con_content = {
        "narrative_type": "project_session",
        "timestamp": _iso_now_con(),
        "project_name": con_project,
        "persona": con_persona,
        "active_identities": con_actors,
        "events": [
            {
                "when": _iso_now_con(),
                "event_type": "session_start",
                "summary": con_session_note or "Session started",
                "participants": [a.get("role") for a in con_actors],
            }
        ],
        "_nexus_resonance_radius_puppy": 0.0,
        "_nexus_stability_puppy": "stable",
    }

    con_content = _to_proto_lingua(con_content, preferred_breed="narrative_timeline")

    con_rel = os.path.join("narrative", f"narrative_session_{int(datetime.now(timezone.utc).timestamp())}_gen0_1.0_nbs.json")
    con_write = create_nbs_file(
        project_name=con_project,
        relative_path=con_rel,
        content=con_content,
        meta={
            "nbs_type": "narrative_timeline",
            "tags": ["narrative", "session"],
            "source": "control",
            "project_name": con_project,
        },
    )
    try:
        prof = ensure_narrative_profile_con(con_project)
        if prof.get("success"):
            sync_narrative_profile_con(
                con_project=con_project,
                con_narrative_path=con_write.get("reference", {}).get("file_path", "")
            )
    except Exception:
        pass
    return con_write


def append_event_con(con_project: str, con_narrative_path: str, con_event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Append a structured event into an existing narrative file's events array.
    Validates resonance and ensures Proto-Lingua compliance.
    """
    if not os.path.exists(con_narrative_path):
        return {"success": False, "error": f"Narrative not found: {con_narrative_path}"}
    with open(con_narrative_path, "r", encoding="utf-8") as f:
        con_obj = json.load(f)
    if not isinstance(con_obj, dict) or "content" not in con_obj:
        return {"success": False, "error": "Invalid narrative wrapper"}
    con_content = con_obj.get("content", {})
    con_events = con_content.setdefault("events", [])
    if not isinstance(con_events, list):
        return {"success": False, "error": "content.events is not an array"}
    con_event = dict(con_event)
    con_event.setdefault("when", _iso_now_con())

    valid, status = validate_resonance(con_event)
    if not valid:
        return {"success": False, "error": f"Event exceeds resonance radius: {status}"}

    con_event = _to_proto_lingua(con_event)

    con_events.append(con_event)
    con_obj["last_modified"] = _iso_now_con()
    with open(con_narrative_path, "w", encoding="utf-8") as f:
        json.dump(con_obj, f, ensure_ascii=False, indent=2)
    return {"success": True, "path": con_narrative_path}


def end_session_con(con_project: str, con_narrative_path: str, con_summary: Optional[str] = None,
                    con_todos: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Append a session_end event with optional summary and todo list.
    Includes Nexus metadata.
    """
    con_event = {
        "event_type": "session_end",
        "summary": con_summary or "Session ended",
        "todos": array_normalize_con(con_todos or []),
        "_nexus_resonance_radius_puppy": 0.0,
        "_nexus_stability_puppy": "stable",
    }
    return append_event_con(con_project, con_narrative_path, con_event)


def checkpoint_con(con_project: str, con_narrative_path: str, con_chunk: Dict[str, Any]) -> Dict[str, Any]:
    """
    Micro-learning checkpoint: append a small, digestible progress chunk.
    con_chunk should include keys like: focus, context, next_steps (arrays preferred)
    """
    con_event = {
        "event_type": "checkpoint",
        "chunk": {
            "focus": array_normalize_con(con_chunk.get("focus")) if isinstance(con_chunk, dict) else [],
            "context": array_normalize_con(con_chunk.get("context")) if isinstance(con_chunk, dict) else [],
            "next_steps": array_normalize_con(con_chunk.get("next_steps")) if isinstance(con_chunk, dict) else [],
        },
    }
    return append_event_con(con_project, con_narrative_path, con_event)


def heartbeat_con(con_project: str, con_narrative_path: str) -> Dict[str, Any]:
    """
    Append a simple heartbeat event, useful for resume/trending.
    """
    con_event = {"event_type": "heartbeat"}
    return append_event_con(con_project, con_narrative_path, con_event)

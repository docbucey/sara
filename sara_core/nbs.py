"""CORE NBS: Narrative Bible System file creation and management."""
import os
import json
import hashlib
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from .proto_lingua import _to_proto_lingua, validate_resonance

import re


# -------------------------
# Constants
# -------------------------

NBS_BASE_DIR: str = os.path.join(os.getcwd(), "nbs_projects")
SYSTEM_CORE_PROJECT_NAME: str = "system_core"
INTERNAL_FILE_VERSION: str = "1.0"


# -------------------------
# Helpers
# -------------------------

def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sanitize_name(value: Any) -> str:
    return re.sub(r"[^a-zA-Z0-9_\-]", "_", str(value)).strip("_")


def _build_core_work_state(
    stage: str = "created",
    status: str = "ready",
    owner_pillar: str = "CORE",
    additional: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build a stable work-state record for CORE-owned wrappers, profiles, and envelopes."""
    state = {
        "status": str(status or "ready"),
        "stage": str(stage or "created"),
        "owner_pillar": str(owner_pillar or "CORE"),
        "last_transition_at": _iso_now(),
        "deterministic": True,
    }
    if isinstance(additional, dict):
        state.update({k: v for k, v in additional.items() if v is not None})
    return state


# -------------------------
# Canonical primitives (Gen0)
# -------------------------

def create_nbs_reference(project_name: str, file_path: str, additional_tags: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Canonical NBS reference generator (Gen0).

    Returns a stable, unique-ish reference record used by other core APIs.
    This must not be replaced by a placeholder that returns constant IDs.
    """
    ts = int(datetime.now(timezone.utc).timestamp())
    proj_clean = _sanitize_name(project_name or SYSTEM_CORE_PROJECT_NAME).lower()
    nbs_id = f"{ts}_{proj_clean}_nbs"

    return {
        "nbs_id": nbs_id,
        "file_path": file_path,
        "created_at": _iso_now(),
        "project": project_name or SYSTEM_CORE_PROJECT_NAME,
        "tags": list(additional_tags or []),
        "reference_type": "nbs_standard",
    }


def in_out_nbs_file(
    operation: str,
    file_path: str,
    data: Any = None,
    meta_tags: Optional[Dict[str, Any]] = None,
    file_format: str = "json",
) -> Dict[str, Any]:
    """
    Perform file I/O for NBS files, with Nexus metadata integration.

    Args:
        operation (str): "read" or "write".
        file_path (str): The path to the file.
        data (Any): The data to write (for "write" operations).
        meta_tags (Optional[Dict[str, Any]]): Metadata tags for the file.
        file_format (str): The file format (default: "json").

    Returns:
        Dict[str, Any]: The result of the operation.
    """
    operation = operation.lower()
    if file_format != "json":
        return {"success": False, "error": f"Unsupported format: {file_format}"}

    if operation == "read":
        if not os.path.exists(file_path):
            return {"success": False, "error": f"File not found: {file_path}"}
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                obj = json.load(f)
            # Validate the NBS wrapper
            if not isinstance(obj, dict) or "nbs_meta" not in obj or "content" not in obj:
                return {"success": False, "error": "Invalid NBS wrapper: missing nbs_meta/content"}
            return {"success": True, "data": obj}
        except Exception as e:
            return {"success": False, "error": f"Read error: {e}"}

    if operation == "write":
        # Build the NBS metadata
        nbs_meta = {
            "nbs_id": None,  # Will be filled after reference creation
            "nbs_type": meta_tags.get("nbs_type") if meta_tags else None,
            "nbs_gen": meta_tags.get("nbs_gen", "gen0"),
            "nbs_ver": meta_tags.get("nbs_ver", INTERNAL_FILE_VERSION),
            "created_at": _iso_now(),
            "source": meta_tags.get("source", "core"),
            "project_name": meta_tags.get("project_name"),
            "tags": meta_tags.get("tags", []),
            # Add Nexus metadata
            "nexus_resonance_radius": 0.0,  # Default to perfect resonance
            "nexus_stability": "stable",
        }

        # Ensure the parent directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Create a reference ID
        ref = create_nbs_reference(
            project_name=nbs_meta["project_name"],
            file_path=file_path,
            additional_tags=nbs_meta["tags"],
        )
        nbs_meta["nbs_id"] = ref["nbs_id"]

        # -----------------
        # Canonical content + work-state slab
        # -----------------
        content_data = dict(data) if isinstance(data, dict) else (data or {})
        if isinstance(content_data, dict):
            content_data.setdefault(
                "_work_state",
                _build_core_work_state(
                    stage="nbs_write",
                    status="ready",
                    additional={"nbs_type": nbs_meta.get("nbs_type") or "generic"},
                ),
            )

        file_breed = meta_tags.get("file_breed") or meta_tags.get("nbs_type", "generic_gen0")
        proto_lingua_enabled = bool(meta_tags.get("proto_lingua", True))

        if proto_lingua_enabled:
            try:
                kennel_content = _to_proto_lingua(content_data, preferred_breed=file_breed)
            except Exception:
                kennel_content = {"_error_puppy": "proto_lingua_transform_failed"}
        else:
            kennel_content = content_data

        # Build the NBS wrapper
        obj = {
            "nbs_meta": nbs_meta,
            "content": content_data,
            "file_version": INTERNAL_FILE_VERSION,
            "last_modified": _iso_now(),
            "nbs_envelope": {
                "file_breed": file_breed,
                "source_pillar": "CORE",
                "provenance_chain": {
                    "creator": "sara_core_gen1",
                    "origin_country": "US_local_machine",
                    "security_clearance": "admin_owner",
                },
                "work_state": _build_core_work_state(
                    stage="wrapped",
                    status="ready",
                    additional={"file_breed": file_breed},
                ),
                "timestamp_iso": _iso_now(),
            },
            "kennel_content": kennel_content,
        }

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(obj, f, ensure_ascii=False, indent=2)
            return {"success": True, "data": obj, "reference": ref}
        except Exception as e:
            return {"success": False, "error": f"Write error: {e}"}

    return {"success": False, "error": f"Unsupported operation: {operation}"}


def create_nbs_file(
    project_name: str,
    relative_path: str,
    content: Any,
    meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Convenience wrapper for creating a valid Gen0 NBS file under the project
    space, ensuring the directory exists and the wrapper is correct.
    """
    proj = _sanitize_name(project_name or SYSTEM_CORE_PROJECT_NAME)
    abs_dir = os.path.join(NBS_BASE_DIR, proj)
    abs_path = os.path.join(abs_dir, relative_path)

    meta = dict(meta or {})
    meta.setdefault("project_name", proj)
    return in_out_nbs_file(
        operation="write",
        file_path=abs_path,
        data=content,
        meta_tags=meta,
        file_format="json",
    )


# -------------------------
# Sheet APIs (Gen0 minimal)
# -------------------------

def create_characterbase_nbs_profile(
    profile_type: str,
    profile_data: Dict[str, Any],
    immutable_fields: List[str],
) -> Dict[str, Any]:
    """
    Create a CharacterBase NBS profile for user, SARA, or client records with
    immutable core fields, stored using the Gen0 wrapper (2/A).

    profile_type: 'user' | 'sara' | 'client'
    - 'user'  -> nbs_type = 'character_sheet'
    - 'sara'  -> nbs_type = 'profile_sheet'
    - 'client' -> nbs_type = 'client_sheet'
    """
    if profile_type not in ("user", "sara", "client"):
        return {"success": False, "error": "profile_type must be 'user', 'sara', or 'client'"}

    missing = [f for f in immutable_fields if f not in profile_data]
    if missing:
        return {"success": False, "error": f"Missing required immutable fields: {missing}"}

    # Enrich content
    content = dict(profile_data)
    profile_name = _sanitize_name(content.get("name", profile_type)).lower() or profile_type
    content["_immutable_fields"] = list(immutable_fields)
    content["_created_at"] = _iso_now()
    content["_profile_type"] = profile_type
    content.setdefault("profile_id", f"{profile_type}_{profile_name}")
    content.setdefault("profile_version", "gen0.1")
    content.setdefault("profile_scope", "local_first")
    content.setdefault(
        "_work_state",
        _build_core_work_state(
            stage="profile_created",
            status="ready",
            additional={"profile_type": profile_type, "profile_id": f"{profile_type}_{profile_name}"},
        ),
    )

    if profile_type == "client":
        client_status = str(content.get("client_status", "inactive")).strip().lower()
        billing_status = str(content.get("billing_status", "not_paid")).strip().lower()

        if client_status not in ("active", "inactive"):
            return {"success": False, "error": "client_status must be 'active' or 'inactive'"}
        if billing_status not in ("paid", "not_paid"):
            return {"success": False, "error": "billing_status must be 'paid' or 'not_paid'"}

        content["client_status"] = client_status
        content["billing_status"] = billing_status
        content["bill_paid"] = billing_status == "paid"

    nbs_type_map = {
        "user": "character_sheet",
        "sara": "profile_sheet",
        "client": "client_sheet",
    }
    nbs_type = nbs_type_map[profile_type]
    canonical_rel_path = os.path.join("identity", profile_type, f"{profile_name}_profile_gen0_1.0_nbs.json")
    compat_rel_path = os.path.join("sheets", profile_type, f"{profile_name}_profile.nbs.json")

    result = create_nbs_file(
        project_name=SYSTEM_CORE_PROJECT_NAME,
        relative_path=canonical_rel_path,
        content=content,
        meta={
            "nbs_type": nbs_type,
            "project_name": SYSTEM_CORE_PROJECT_NAME,
            "tags": [profile_type, "profile", "characterbase", "identity"],
            "source": "core",
            "file_breed": nbs_type,
            "proto_lingua": True,
        },
    )

    compat_result = create_nbs_file(
        project_name=SYSTEM_CORE_PROJECT_NAME,
        relative_path=compat_rel_path,
        content=dict(content),
        meta={
            "nbs_type": nbs_type,
            "project_name": SYSTEM_CORE_PROJECT_NAME,
            "tags": [profile_type, "profile", "characterbase", "compat"],
            "source": "core",
            "file_breed": nbs_type,
            "proto_lingua": True,
        },
    )

    if isinstance(result, dict):
        result["compatibility_reference"] = compat_result.get("reference") if isinstance(compat_result, dict) else None
        result["canonical_relative_path"] = canonical_rel_path
        result["compatibility_relative_path"] = compat_rel_path
    return result


def create_nbs_project_profile(
    project_name: str,
    project_data: Dict[str, Any],
    editable_fields: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Create a project sheet under the project's namespace using the Gen0 wrapper.
    """
    proj = _sanitize_name(project_name)
    content = dict(project_data)
    content.setdefault("project_name", proj)
    content.setdefault("_created_at", _iso_now())
    content.setdefault("_editable_fields", list(editable_fields or []))
    content.setdefault(
        "_work_state",
        _build_core_work_state(
            stage="project_sheet_created",
            status="ready",
            additional={"project_name": proj},
        ),
    )
    content.setdefault(
        "_workflow_slots",
        {
            "wfh": {"status": "planned"},
            "vnce": {"status": "planned"},
            "abbucey": {"status": "planned"},
        },
    )
    content.setdefault(
        "deliverable_state",
        {"status": "idle", "pending_count": 0, "last_closeout_at": None},
    )

    rel_path = os.path.join("sheets", f"{proj}_project_sheet.nbs.json")
    return create_nbs_file(
        project_name=proj,
        relative_path=rel_path,
        content=content,
        meta={
            "nbs_type": "project_sheet",
            "project_name": proj,
            "tags": ["project", "sheet"],
            "source": "core",
            "file_breed": "project_sheet",
            "proto_lingua": True,
        },
    )


def update_nbs_project_profile(
    current_project_name: str,
    updates: Dict[str, Any],
    new_project_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Update an existing project sheet. Supports optional rename of the project
    (moves directory and rewrites the file under the new name).
    """
    curr = _sanitize_name(current_project_name)
    curr_dir = os.path.join(NBS_BASE_DIR, curr)
    curr_rel = os.path.join("sheets", f"{curr}_project_sheet.nbs.json")
    curr_path = os.path.join(curr_dir, curr_rel)

    read_res = in_out_nbs_file("read", curr_path)
    if not read_res.get("success"):
        return read_res

    obj = read_res["data"]
    content = obj.get("content", {})

    # Apply updates with respect to _editable_fields if present
    editable = set(content.get("_editable_fields", []))
    if editable:
        for k, v in updates.items():
            if k in editable or k.startswith("_"):
                content[k] = v
    else:
        content.update(updates)

    # Handle rename if requested
    target_proj = _sanitize_name(new_project_name) if new_project_name else curr
    if target_proj != curr:
        target_dir = os.path.join(NBS_BASE_DIR, target_proj)
        os.makedirs(target_dir, exist_ok=True)
        # Move entire project directory (simple approach)
        try:
            if os.path.abspath(curr_dir) != os.path.abspath(target_dir):
                # If target exists, we keep it and just move files over; otherwise rename
                if not os.path.exists(target_dir):
                    os.rename(curr_dir, target_dir)
                else:
                    # Ensure sheets subdir exists
                    os.makedirs(os.path.join(target_dir, "sheets"), exist_ok=True)
                    # Move the project sheet file only; other assets remain user's choice
                    if os.path.exists(curr_path):
                        os.replace(curr_path, os.path.join(target_dir, "sheets", f"{target_proj}_project_sheet.nbs.json"))
                # Update paths
                curr_dir = target_dir
        except Exception as e:
            return {"success": False, "error": f"Rename error: {e}"}

    # Write back updated content to the proper location
    rel_path = os.path.join("sheets", f"{target_proj}_project_sheet.nbs.json")
    write_res = create_nbs_file(
        project_name=target_proj,
        relative_path=rel_path,
        content=content,
        meta={
            "nbs_type": "project_sheet",
            "project_name": target_proj,
            "tags": ["project", "sheet"],
            "source": "core",
        },
    )
    return write_res


def append_event(
    project_name: str,
    narrative_path: str,
    event: Dict[str, Any],
) -> Dict[str, Any]:
    proj = _sanitize_name(project_name)
    abs_dir = os.path.join(NBS_BASE_DIR, proj)
    abs_path = os.path.join(abs_dir, narrative_path)

    os.makedirs(os.path.dirname(abs_path), exist_ok=True)

    existing_id = None
    if os.path.exists(abs_path):
        read_res = in_out_nbs_file("read", abs_path)
        if not read_res.get("success"):
            return read_res
        
        obj = read_res["data"]
        content = obj.get("content", {})
        kennel = obj.get("kennel_content", {})
        # This line is the "Tuning Fork" - it finds the timeline in either format
        timeline = content.get("timeline") or kennel.get("timeline_dog_array", [])
        
        # This line "Latches" the identity so it doesn't reset every time
        existing_id = obj.get("nbs_meta", {}).get("nbs_id")
    else:
        timeline = []

    timeline.append(event)

    return in_out_nbs_file(
        operation="write",
        file_path=abs_path,
        data={"timeline": timeline},
        meta_tags={
            "nbs_type": "narrative_timeline",
            "project_name": proj,
            "tags": ["timeline", "events"],
            "source": "core",
            "nbs_id": existing_id 
        },
    )

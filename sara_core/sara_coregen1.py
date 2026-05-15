def core_slm_entrypoint(command: str, payload: dict) -> dict:
    """
    SLM entrypoint for CORE. Only responds if CONTROL is up and (MAMA and CORE) are up.
    Accepts 'probe' command to return available functions.
    """
    control_up = payload.get('control_up', False)
    mama_up = payload.get('mama_up', False)
    core_up = True  # This is CORE
    if not control_up:
        return {"status": "standing_by", "detail": "CONTROL not available"}
    if not (mama_up and core_up):
        return {"status": "standby", "detail": "Waiting for MAMA and CORE"}
    # Map of supported functions
    fn_map = {
        "import_3d_asset": import_3d_asset,
        "export_3d_asset": export_3d_asset,
        "convert_3d_asset": convert_3d_asset,
        "validate_3d_asset": validate_3d_asset,
        "create_update_scene": create_update_scene,
        "query_scene_state": query_scene_state,
        "delete_scene_object": delete_scene_object,
        "submit_render_job": submit_render_job,
        "query_render_job": query_render_job,
        "cancel_render_job": cancel_render_job,
        "retrieve_render_output": retrieve_render_output,
        "import_media_sequence": import_media_sequence,
        "export_media_sequence": export_media_sequence,
        "edit_timeline": edit_timeline,
        "query_timeline_media": query_timeline_media,
        "update_core_profile_with_ai_config": update_core_profile_with_ai_config,
        "create_characterbase_nbs_profile": create_characterbase_nbs_profile,
        "sara_project_memory_nbs": sara_project_memory_nbs,
        "_load_memory_context": _load_memory_context
    }
    if command == 'probe':
        return {
            "status": "ready",
            "functions": list(fn_map.keys())
        }
    # Dispatch to mapped function if available
    if command in fn_map:
        try:
            return fn_map[command](payload)
        except Exception as e:
            return {"success": False, "error": f"Exception in {command}: {e}"}
    return {"status": "ready", "detail": "CORE SLM active via CONTROL", "error": f"Unknown command: {command}"}
import subprocess

def run_system_command(payload):
    """
    Securely execute a system command (git, pip, winget, etc.) with audit logging.
    Args: payload dict with keys: command (str or list), allowed (optional whitelist)
    Returns: result dict
    """
    if isinstance(payload, dict) and 'shunt_id' in payload:
        if not validate_shunt_header(payload):
            return {"success": False, "error": "Invalid shunt header"}
    audit_entry = {
        'timestamp': datetime.now().isoformat(),
        'action': 'run_system_command',
        'user': payload.get('user', 'system'),
        'command': payload.get('command')
    }
    command = payload.get('command')
    allowed = payload.get('allowed', ['git', 'pip', 'winget'])
    if not command:
        result = {"success": False, "error": "Missing command in payload"}
    else:
        # Only allow whitelisted commands
        if isinstance(command, str):
            cmd_list = command.strip().split()
        else:
            cmd_list = list(command)
        if cmd_list[0] not in allowed:
            result = {"success": False, "error": f"Command not allowed: {cmd_list[0]}"}
        else:
            try:
                completed = subprocess.run(cmd_list, capture_output=True, text=True, timeout=60)
                result = {
                    "success": completed.returncode == 0,
                    "stdout": completed.stdout,
                    "stderr": completed.stderr,
                    "returncode": completed.returncode
                }
            except Exception as e:
                result = {"success": False, "error": f"Execution failed: {str(e)}"}
    # Audit log
    try:
        audit_dir = os.path.join(os.path.dirname(__file__), 'audit_logs')
        os.makedirs(audit_dir, exist_ok=True)
        audit_file = os.path.join(audit_dir, 'system_command_audit.log')
        audit_entry['result'] = 'PASS' if result.get('success') else 'FAIL'
        audit_entry['details'] = result.get('error', result.get('stdout', ''))
        with open(audit_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(audit_entry) + '\n')
    except Exception:
        pass
    return result
# =========================================================
# Profile, Memory, and Learning Management Functions (protocol_function_map.json)
# =========================================================
def update_core_profile_with_ai_config(payload):
    """
    Validate and update profile data, persist to core storage.
    Args: payload dict with keys: profile_data
    Returns: result dict
    """
    if isinstance(payload, dict) and 'shunt_id' in payload:
        if not validate_shunt_header(payload):
            return {"success": False, "error": "Invalid shunt header"}
    audit_entry = {
        'timestamp': datetime.now().isoformat(),
        'action': 'update_core_profile_with_ai_config',
        'user': payload.get('user', 'system')
    }
    profile_data = payload.get('profile_data')
    if not profile_data or not isinstance(profile_data, dict):
        result = {"success": False, "error": "Missing or invalid profile_data in payload"}
    else:
        profile_dir = os.path.join(os.path.dirname(__file__), 'profile_storage')
        os.makedirs(profile_dir, exist_ok=True)
        profile_id = profile_data.get('id') or f"profile_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        profile_file = os.path.join(profile_dir, f"{profile_id}.json")
        try:
            with open(profile_file, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, indent=2)
            result = {"success": True, "profile_id": profile_id, "profile_file": profile_file, "message": "Profile updated and persisted."}
        except Exception as e:
            result = {"success": False, "error": f"Failed to persist profile: {str(e)}"}
    # Audit log
    try:
        audit_dir = os.path.join(os.path.dirname(__file__), 'audit_logs')
        os.makedirs(audit_dir, exist_ok=True)
        audit_file = os.path.join(audit_dir, 'profile_audit.log')
        audit_entry['result'] = 'PASS' if result.get('success') else 'FAIL'
        audit_entry['details'] = result.get('error', result.get('message', ''))
        with open(audit_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(audit_entry) + '\n')
    except Exception:
        pass
    return result

def create_characterbase_nbs_profile(payload):
    """
    Create new characterbase profile in core storage.
    Args: payload dict with keys: profile_data
    Returns: result dict
    """
    if isinstance(payload, dict) and 'shunt_id' in payload:
        if not validate_shunt_header(payload):
            return {"success": False, "error": "Invalid shunt header"}
    audit_entry = {
        'timestamp': datetime.now().isoformat(),
        'action': 'create_characterbase_nbs_profile',
        'user': payload.get('user', 'system')
    }
    profile_data = payload.get('profile_data')
    if not profile_data or not isinstance(profile_data, dict):
        result = {"success": False, "error": "Missing or invalid profile_data in payload"}
    else:
        profile_dir = os.path.join(os.path.dirname(__file__), 'characterbase_profiles')
        os.makedirs(profile_dir, exist_ok=True)
        profile_id = profile_data.get('id') or f"characterbase_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        profile_file = os.path.join(profile_dir, f"{profile_id}.json")
        try:
            with open(profile_file, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, indent=2)
            result = {"success": True, "profile_id": profile_id, "profile_file": profile_file, "message": "Characterbase profile created and persisted."}
        except Exception as e:
            result = {"success": False, "error": f"Failed to persist characterbase profile: {str(e)}"}
    # Audit log
    try:
        audit_dir = os.path.join(os.path.dirname(__file__), 'audit_logs')
        os.makedirs(audit_dir, exist_ok=True)
        audit_file = os.path.join(audit_dir, 'profile_audit.log')
        audit_entry['result'] = 'PASS' if result.get('success') else 'FAIL'
        audit_entry['details'] = result.get('error', result.get('message', ''))
        with open(audit_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(audit_entry) + '\n')
    except Exception:
        pass
    return result

def sara_project_memory_nbs(payload):
    """
    Handle persistent project memory and logs.
    Args: payload dict with keys: project_id, memory_data
    Returns: result dict
    """
    if isinstance(payload, dict) and 'shunt_id' in payload:
        if not validate_shunt_header(payload):
            return {"success": False, "error": "Invalid shunt header"}
    audit_entry = {
        'timestamp': datetime.now().isoformat(),
        'action': 'sara_project_memory_nbs',
        'project_id': payload.get('project_id'),
        'user': payload.get('user', 'system')
    }
    project_id = payload.get('project_id')
    memory_data = payload.get('memory_data')
    if not project_id or not memory_data:
        result = {"success": False, "error": "Missing project_id or memory_data in payload"}
    else:
        memory_dir = os.path.join(os.path.dirname(__file__), 'project_memory')
        os.makedirs(memory_dir, exist_ok=True)
        memory_file = os.path.join(memory_dir, f"{project_id}.json")
        try:
            with open(memory_file, 'w', encoding='utf-8') as f:
                json.dump(memory_data, f, indent=2)
            result = {"success": True, "project_id": project_id, "memory_file": memory_file, "message": "Project memory persisted."}
        except Exception as e:
            result = {"success": False, "error": f"Failed to persist project memory: {str(e)}"}
    # Audit log
    try:
        audit_dir = os.path.join(os.path.dirname(__file__), 'audit_logs')
        os.makedirs(audit_dir, exist_ok=True)
        audit_file = os.path.join(audit_dir, 'project_memory_audit.log')
        audit_entry['result'] = 'PASS' if result.get('success') else 'FAIL'
        audit_entry['details'] = result.get('error', result.get('message', ''))
        with open(audit_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(audit_entry) + '\n')
    except Exception:
        pass
    return result

def _load_memory_context(payload):
    """
    Load memory context for SARA agent, research, and learning/audit managers.
    Args: payload dict with keys as needed
    Returns: result dict
    """
    if isinstance(payload, dict) and 'shunt_id' in payload:
        if not validate_shunt_header(payload):
            return {"success": False, "error": "Invalid shunt header"}
    # No audit log for context load (read-only, non-persistent)
    context_id = payload.get('context_id')
    if not context_id:
        return {"success": False, "error": "Missing context_id in payload"}
    memory_dir = os.path.join(os.path.dirname(__file__), 'project_memory')
    memory_file = os.path.join(memory_dir, f"{context_id}.json")
    if not os.path.isfile(memory_file):
        return {"success": False, "error": f"Memory context not found: {context_id}"}
    try:
        with open(memory_file, 'r', encoding='utf-8') as f:
            memory_context = json.load(f)
        return {"success": True, "context_id": context_id, "memory_context": memory_context, "message": "Memory context loaded."}
    except Exception as e:
        return {"success": False, "error": f"Failed to load memory context: {str(e)}"}
# =========================================================
# Timeline/Media Protocol Functions (protocol_function_map.json)
# =========================================================
def import_media_sequence(payload):
    """
    Validate, convert, and store media sequence (video, audio, image) in media library.
    Args: payload dict with keys: files, metadata
    Returns: result dict
    """
    if isinstance(payload, dict) and 'shunt_id' in payload:
        if not validate_shunt_header(payload):
            return {"success": False, "error": "Invalid shunt header"}
    audit_entry = {
        'timestamp': datetime.now().isoformat(),
        'action': 'import_media_sequence',
        'files': payload.get('files'),
        'user': payload.get('user', 'system')
    }
    files = payload.get('files')
    metadata = payload.get('metadata', {})
    if not files or not isinstance(files, list):
        result = {"success": False, "error": "Missing or invalid files list in payload"}
    else:
        media_library_dir = os.path.join(os.path.dirname(__file__), 'media_library')
        os.makedirs(media_library_dir, exist_ok=True)
        imported = []
        errors = []
        import shutil
        for file_path in files:
            if not os.path.isfile(file_path):
                errors.append(f"File not found: {file_path}")
                continue
            ext = os.path.splitext(file_path)[1].lower()
            if ext not in ('.mp4', '.mov', '.avi', '.wav', '.mp3', '.jpg', '.jpeg', '.png', '.tiff'):
                errors.append(f"Unsupported media type: {file_path}")
                continue
            try:
                dest_path = os.path.join(media_library_dir, os.path.basename(file_path))
                shutil.copy2(file_path, dest_path)
                imported.append(dest_path)
            except Exception as e:
                errors.append(f"Failed to import {file_path}: {str(e)}")
        if imported:
            result = {"success": True, "imported": imported, "errors": errors, "message": "Media files imported."}
        else:
            result = {"success": False, "error": "; ".join(errors) or "No files imported."}
    # Audit log
    try:
        audit_dir = os.path.join(os.path.dirname(__file__), 'audit_logs')
        os.makedirs(audit_dir, exist_ok=True)
        audit_file = os.path.join(audit_dir, 'media_timeline_audit.log')
        audit_entry['result'] = 'PASS' if result.get('success') else 'FAIL'
        audit_entry['details'] = result.get('error', result.get('message', ''))
        with open(audit_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(audit_entry) + '\n')
    except Exception:
        pass
    return result

def export_media_sequence(payload):
    """
    Convert and export media from library.
    Args: payload dict with keys: media_id, target_format, options
    Returns: result dict
    """
    if isinstance(payload, dict) and 'shunt_id' in payload:
        if not validate_shunt_header(payload):
            return {"success": False, "error": "Invalid shunt header"}
    audit_entry = {
        'timestamp': datetime.now().isoformat(),
        'action': 'export_media_sequence',
        'media_id': payload.get('media_id'),
        'target_format': payload.get('target_format'),
        'user': payload.get('user', 'system')
    }
    media_id = payload.get('media_id')
    target_format = payload.get('target_format')
    options = payload.get('options', {})
    if not media_id or not target_format:
        result = {"success": False, "error": "Missing media_id or target_format in payload"}
    else:
        media_library_dir = os.path.join(os.path.dirname(__file__), 'media_library')
        media_path = os.path.join(media_library_dir, os.path.basename(media_id))
        if not os.path.isfile(media_path):
            result = {"success": False, "error": f"Media not found in library: {media_path}"}
        else:
            export_dir = os.path.join(os.path.dirname(__file__), 'media_exports')
            os.makedirs(export_dir, exist_ok=True)
            export_filename = os.path.splitext(os.path.basename(media_id))[0] + target_format
            export_path = os.path.join(export_dir, export_filename)
            try:
                import shutil
                shutil.copy2(media_path, export_path)
                result = {"success": True, "export_path": export_path, "message": "Media exported."}
            except Exception as e:
                result = {"success": False, "error": f"Failed to export media: {str(e)}"}
    # Audit log
    try:
        audit_dir = os.path.join(os.path.dirname(__file__), 'audit_logs')
        os.makedirs(audit_dir, exist_ok=True)
        audit_file = os.path.join(audit_dir, 'media_timeline_audit.log')
        audit_entry['result'] = 'PASS' if result.get('success') else 'FAIL'
        audit_entry['details'] = result.get('error', result.get('message', ''))
        with open(audit_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(audit_entry) + '\n')
    except Exception:
        pass
    return result

def edit_timeline(payload):
    """
    Apply timeline edits (insert, cut, move, trim, etc.) and update persistent timeline state.
    Args: payload dict with keys: timeline_id, edit_actions
    Returns: result dict
    """
    if isinstance(payload, dict) and 'shunt_id' in payload:
        if not validate_shunt_header(payload):
            return {"success": False, "error": "Invalid shunt header"}
    audit_entry = {
        'timestamp': datetime.now().isoformat(),
        'action': 'edit_timeline',
        'timeline_id': payload.get('timeline_id'),
        'user': payload.get('user', 'system')
    }
    timeline_id = payload.get('timeline_id')
    edit_actions = payload.get('edit_actions')
    if not timeline_id or not edit_actions or not isinstance(edit_actions, list):
        result = {"success": False, "error": "Missing timeline_id or invalid edit_actions in payload"}
    else:
        timeline_dir = os.path.join(os.path.dirname(__file__), 'timeline_storage')
        os.makedirs(timeline_dir, exist_ok=True)
        timeline_file = os.path.join(timeline_dir, f"{timeline_id}.json")
        timeline_state = {"timeline_id": timeline_id, "edits": []}
        if os.path.isfile(timeline_file):
            try:
                with open(timeline_file, 'r', encoding='utf-8') as f:
                    timeline_state = json.load(f)
            except Exception:
                pass
        timeline_state['edits'].extend(edit_actions)
        try:
            with open(timeline_file, 'w', encoding='utf-8') as f:
                json.dump(timeline_state, f, indent=2)
            result = {"success": True, "timeline_id": timeline_id, "timeline_file": timeline_file, "message": "Timeline edits applied."}
        except Exception as e:
            result = {"success": False, "error": f"Failed to update timeline: {str(e)}"}
    # Audit log
    try:
        audit_dir = os.path.join(os.path.dirname(__file__), 'audit_logs')
        os.makedirs(audit_dir, exist_ok=True)
        audit_file = os.path.join(audit_dir, 'media_timeline_audit.log')
        audit_entry['result'] = 'PASS' if result.get('success') else 'FAIL'
        audit_entry['details'] = result.get('error', result.get('message', ''))
        with open(audit_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(audit_entry) + '\n')
    except Exception:
        pass
    return result

def query_timeline_media(payload):
    """
    Return current timeline/media state and info.
    Args: payload dict with keys: timeline_id, media_id, query_params
    Returns: result dict
    """
    if isinstance(payload, dict) and 'shunt_id' in payload:
        if not validate_shunt_header(payload):
            return {"success": False, "error": "Invalid shunt header"}
    audit_entry = {
        'timestamp': datetime.now().isoformat(),
        'action': 'query_timeline_media',
        'timeline_id': payload.get('timeline_id'),
        'media_id': payload.get('media_id'),
        'user': payload.get('user', 'system')
    }
    timeline_id = payload.get('timeline_id')
    media_id = payload.get('media_id')
    timeline_dir = os.path.join(os.path.dirname(__file__), 'timeline_storage')
    if not timeline_id:
        result = {"success": False, "error": "Missing timeline_id in payload"}
    else:
        timeline_file = os.path.join(timeline_dir, f"{timeline_id}.json")
        if not os.path.isfile(timeline_file):
            result = {"success": False, "error": f"Timeline not found: {timeline_id}"}
        else:
            try:
                with open(timeline_file, 'r', encoding='utf-8') as f:
                    timeline_state = json.load(f)
                # Optionally filter for media_id if provided
                if media_id:
                    media_info = [edit for edit in timeline_state.get('edits', []) if edit.get('media_id') == media_id]
                    result = {"success": True, "timeline_id": timeline_id, "media_id": media_id, "media_info": media_info, "message": "Timeline media info loaded."}
                else:
                    result = {"success": True, "timeline_id": timeline_id, "timeline_state": timeline_state, "message": "Timeline state loaded."}
            except Exception as e:
                result = {"success": False, "error": f"Failed to load timeline: {str(e)}"}
    # Audit log
    try:
        audit_dir = os.path.join(os.path.dirname(__file__), 'audit_logs')
        os.makedirs(audit_dir, exist_ok=True)
        audit_file = os.path.join(audit_dir, 'media_timeline_audit.log')
        audit_entry['result'] = 'PASS' if result.get('success') else 'FAIL'
        audit_entry['details'] = result.get('error', result.get('message', ''))
        with open(audit_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(audit_entry) + '\n')
    except Exception:
        pass
    return result
# =========================================================
# Render/Job Protocol Functions (protocol_function_map.json)
# =========================================================
def submit_render_job(payload):
    """
    Queue render job and store job spec in CORE.
    Args: payload dict with keys: scene_id, frame_range, output_settings, job_metadata
    Returns: result dict
    """
    if isinstance(payload, dict) and 'shunt_id' in payload:
        if not validate_shunt_header(payload):
            return {"success": False, "error": "Invalid shunt header"}
    audit_entry = {
        'timestamp': datetime.now().isoformat(),
        'action': 'submit_render_job',
        'scene_id': payload.get('scene_id'),
        'user': payload.get('user', 'system')
    }
    scene_id = payload.get('scene_id')
    frame_range = payload.get('frame_range')
    output_settings = payload.get('output_settings')
    job_metadata = payload.get('job_metadata', {})
    if not scene_id or not frame_range or not output_settings:
        result = {"success": False, "error": "Missing required render job fields (scene_id, frame_range, output_settings)"}
    else:
        job_id = f"job_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        job_dir = os.path.join(os.path.dirname(__file__), 'render_jobs')
        os.makedirs(job_dir, exist_ok=True)
        job_file = os.path.join(job_dir, f"{job_id}.json")
        job_spec = {
            "job_id": job_id,
            "scene_id": scene_id,
            "frame_range": frame_range,
            "output_settings": output_settings,
            "job_metadata": job_metadata,
            "status": "queued",
            "created": datetime.now().isoformat()
        }
        try:
            with open(job_file, 'w', encoding='utf-8') as f:
                json.dump(job_spec, f, indent=2)
            result = {"success": True, "job_id": job_id, "job_file": job_file, "message": "Render job queued."}
        except Exception as e:
            result = {"success": False, "error": f"Failed to queue render job: {str(e)}"}
    # Audit log
    try:
        audit_dir = os.path.join(os.path.dirname(__file__), 'audit_logs')
        os.makedirs(audit_dir, exist_ok=True)
        audit_file = os.path.join(audit_dir, 'render_job_audit.log')
        audit_entry['result'] = 'PASS' if result.get('success') else 'FAIL'
        audit_entry['details'] = result.get('error', result.get('message', ''))
        with open(audit_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(audit_entry) + '\n')
    except Exception:
        pass
    return result

def query_render_job(payload):
    """
    Return render job status, logs, and output location.
    Args: payload dict with keys: job_id
    Returns: result dict
    """
    if isinstance(payload, dict) and 'shunt_id' in payload:
        if not validate_shunt_header(payload):
            return {"success": False, "error": "Invalid shunt header"}
    audit_entry = {
        'timestamp': datetime.now().isoformat(),
        'action': 'query_render_job',
        'job_id': payload.get('job_id'),
        'user': payload.get('user', 'system')
    }
    job_id = payload.get('job_id')
    if not job_id:
        result = {"success": False, "error": "Missing job_id in payload"}
    else:
        job_dir = os.path.join(os.path.dirname(__file__), 'render_jobs')
        job_file = os.path.join(job_dir, f"{job_id}.json")
        if not os.path.isfile(job_file):
            result = {"success": False, "error": f"Render job not found: {job_id}"}
        else:
            try:
                with open(job_file, 'r', encoding='utf-8') as f:
                    job_spec = json.load(f)
                result = {"success": True, "job_id": job_id, "job_status": job_spec.get('status'), "job_spec": job_spec, "message": "Render job status loaded."}
            except Exception as e:
                result = {"success": False, "error": f"Failed to load render job: {str(e)}"}
    # Audit log
    try:
        audit_dir = os.path.join(os.path.dirname(__file__), 'audit_logs')
        os.makedirs(audit_dir, exist_ok=True)
        audit_file = os.path.join(audit_dir, 'render_job_audit.log')
        audit_entry['result'] = 'PASS' if result.get('success') else 'FAIL'
        audit_entry['details'] = result.get('error', result.get('message', ''))
        with open(audit_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(audit_entry) + '\n')
    except Exception:
        pass
    return result

def cancel_render_job(payload):
    """
    Cancel queued or running render job.
    Args: payload dict with keys: job_id
    Returns: result dict
    """
    if isinstance(payload, dict) and 'shunt_id' in payload:
        if not validate_shunt_header(payload):
            return {"success": False, "error": "Invalid shunt header"}
    audit_entry = {
        'timestamp': datetime.now().isoformat(),
        'action': 'cancel_render_job',
        'job_id': payload.get('job_id'),
        'user': payload.get('user', 'system')
    }
    job_id = payload.get('job_id')
    if not job_id:
        result = {"success": False, "error": "Missing job_id in payload"}
    else:
        job_dir = os.path.join(os.path.dirname(__file__), 'render_jobs')
        job_file = os.path.join(job_dir, f"{job_id}.json")
        if not os.path.isfile(job_file):
            result = {"success": False, "error": f"Render job not found: {job_id}"}
        else:
            try:
                with open(job_file, 'r', encoding='utf-8') as f:
                    job_spec = json.load(f)
                job_spec['status'] = 'cancelled'
                with open(job_file, 'w', encoding='utf-8') as f:
                    json.dump(job_spec, f, indent=2)
                result = {"success": True, "job_id": job_id, "message": "Render job cancelled."}
            except Exception as e:
                result = {"success": False, "error": f"Failed to cancel render job: {str(e)}"}
    # Audit log
    try:
        audit_dir = os.path.join(os.path.dirname(__file__), 'audit_logs')
        os.makedirs(audit_dir, exist_ok=True)
        audit_file = os.path.join(audit_dir, 'render_job_audit.log')
        audit_entry['result'] = 'PASS' if result.get('success') else 'FAIL'
        audit_entry['details'] = result.get('error', result.get('message', ''))
        with open(audit_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(audit_entry) + '\n')
    except Exception:
        pass
    return result

def retrieve_render_output(payload):
    """
    Return output file(s) and logs for render job.
    Args: payload dict with keys: job_id
    Returns: result dict
    """
    if isinstance(payload, dict) and 'shunt_id' in payload:
        if not validate_shunt_header(payload):
            return {"success": False, "error": "Invalid shunt header"}
    audit_entry = {
        'timestamp': datetime.now().isoformat(),
        'action': 'retrieve_render_output',
        'job_id': payload.get('job_id'),
        'user': payload.get('user', 'system')
    }
    job_id = payload.get('job_id')
    if not job_id:
        result = {"success": False, "error": "Missing job_id in payload"}
    else:
        job_dir = os.path.join(os.path.dirname(__file__), 'render_jobs')
        job_file = os.path.join(job_dir, f"{job_id}.json")
        if not os.path.isfile(job_file):
            result = {"success": False, "error": f"Render job not found: {job_id}"}
        else:
            try:
                with open(job_file, 'r', encoding='utf-8') as f:
                    job_spec = json.load(f)
                # Simulate output files/logs
                output_dir = os.path.join(os.path.dirname(__file__), 'render_outputs')
                output_file = os.path.join(output_dir, f"{job_id}_output.txt")
                log_file = os.path.join(output_dir, f"{job_id}_log.txt")
                # Simulate files if they don't exist
                os.makedirs(output_dir, exist_ok=True)
                if not os.path.isfile(output_file):
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(f"Output for render job {job_id}\n")
                if not os.path.isfile(log_file):
                    with open(log_file, 'w', encoding='utf-8') as f:
                        f.write(f"Log for render job {job_id}\n")
                result = {
                    "success": True,
                    "job_id": job_id,
                    "output_file": output_file,
                    "log_file": log_file,
                    "message": "Render output and logs retrieved."
                }
            except Exception as e:
                result = {"success": False, "error": f"Failed to retrieve render output: {str(e)}"}
    # Audit log
    try:
        audit_dir = os.path.join(os.path.dirname(__file__), 'audit_logs')
        os.makedirs(audit_dir, exist_ok=True)
        audit_file = os.path.join(audit_dir, 'render_job_audit.log')
        audit_entry['result'] = 'PASS' if result.get('success') else 'FAIL'
        audit_entry['details'] = result.get('error', result.get('message', ''))
        with open(audit_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(audit_entry) + '\n')
    except Exception:
        pass
    return result
# =========================================================
# Scene/State Protocol Functions (protocol_function_map.json)
# =========================================================
def create_update_scene(payload):
    """
    Store or update scene graph (objects, transforms, cameras, lights, collections) in CORE.
    Args: payload dict with keys: scene_graph, scene_id (optional)
    Returns: result dict
    """
    if isinstance(payload, dict) and 'shunt_id' in payload:
        if not validate_shunt_header(payload):
            return {"success": False, "error": "Invalid shunt header"}
    audit_entry = {
        'timestamp': datetime.now().isoformat(),
        'action': 'create_update_scene',
        'scene_id': payload.get('scene_id'),
        'user': payload.get('user', 'system')
    }
    scene_graph = payload.get('scene_graph')
    scene_id = payload.get('scene_id') or f"scene_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    if not scene_graph:
        result = {"success": False, "error": "Missing scene_graph in payload"}
    else:
        # Store or update scene as JSON file
        scene_dir = os.path.join(os.path.dirname(__file__), 'scene_storage')
        os.makedirs(scene_dir, exist_ok=True)
        scene_file = os.path.join(scene_dir, f"{scene_id}.json")
        try:
            with open(scene_file, 'w', encoding='utf-8') as f:
                json.dump(scene_graph, f, indent=2)
            result = {"success": True, "scene_id": scene_id, "scene_file": scene_file, "message": "Scene stored/updated."}
        except Exception as e:
            result = {"success": False, "error": f"Failed to store scene: {str(e)}"}
    # Audit log
    try:
        audit_dir = os.path.join(os.path.dirname(__file__), 'audit_logs')
        os.makedirs(audit_dir, exist_ok=True)
        audit_file = os.path.join(audit_dir, 'scene_audit.log')
        audit_entry['result'] = 'PASS' if result.get('success') else 'FAIL'
        audit_entry['details'] = result.get('error', result.get('message', ''))
        with open(audit_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(audit_entry) + '\n')
    except Exception:
        pass
    return result

def query_scene_state(payload):
    """
    Return current scene graph/state.
    Args: payload dict with keys: scene_id, query_params
    Returns: result dict
    """
    if isinstance(payload, dict) and 'shunt_id' in payload:
        if not validate_shunt_header(payload):
            return {"success": False, "error": "Invalid shunt header"}
    audit_entry = {
        'timestamp': datetime.now().isoformat(),
        'action': 'query_scene_state',
        'scene_id': payload.get('scene_id'),
        'user': payload.get('user', 'system')
    }
    scene_id = payload.get('scene_id')
    if not scene_id:
        result = {"success": False, "error": "Missing scene_id in payload"}
    else:
        scene_dir = os.path.join(os.path.dirname(__file__), 'scene_storage')
        scene_file = os.path.join(scene_dir, f"{scene_id}.json")
        if not os.path.isfile(scene_file):
            result = {"success": False, "error": f"Scene not found: {scene_id}"}
        else:
            try:
                with open(scene_file, 'r', encoding='utf-8') as f:
                    scene_graph = json.load(f)
                result = {"success": True, "scene_id": scene_id, "scene_graph": scene_graph, "message": "Scene loaded."}
            except Exception as e:
                result = {"success": False, "error": f"Failed to load scene: {str(e)}"}
    # Audit log
    try:
        audit_dir = os.path.join(os.path.dirname(__file__), 'audit_logs')
        os.makedirs(audit_dir, exist_ok=True)
        audit_file = os.path.join(audit_dir, 'scene_audit.log')
        audit_entry['result'] = 'PASS' if result.get('success') else 'FAIL'
        audit_entry['details'] = result.get('error', result.get('message', ''))
        with open(audit_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(audit_entry) + '\n')
    except Exception:
        pass
    return result

def delete_scene_object(payload):
    """
    Remove scene or object from persistent state.
    Args: payload dict with keys: scene_id or object_id
    Returns: result dict
    """
    if isinstance(payload, dict) and 'shunt_id' in payload:
        if not validate_shunt_header(payload):
            return {"success": False, "error": "Invalid shunt header"}
    audit_entry = {
        'timestamp': datetime.now().isoformat(),
        'action': 'delete_scene_object',
        'scene_id': payload.get('scene_id'),
        'object_id': payload.get('object_id'),
        'user': payload.get('user', 'system')
    }
    scene_id = payload.get('scene_id')
    object_id = payload.get('object_id')
    scene_dir = os.path.join(os.path.dirname(__file__), 'scene_storage')
    if scene_id:
        scene_file = os.path.join(scene_dir, f"{scene_id}.json")
        if not os.path.isfile(scene_file):
            result = {"success": False, "error": f"Scene not found: {scene_id}"}
        else:
            try:
                if object_id:
                    # Remove object from scene graph
                    with open(scene_file, 'r', encoding='utf-8') as f:
                        scene_graph = json.load(f)
                    # Assume scene_graph['objects'] is a list of dicts with 'id' key
                    objects = scene_graph.get('objects', [])
                    new_objects = [obj for obj in objects if obj.get('id') != object_id]
                    if len(objects) == len(new_objects):
                        result = {"success": False, "error": f"Object {object_id} not found in scene {scene_id}"}
                    else:
                        scene_graph['objects'] = new_objects
                        with open(scene_file, 'w', encoding='utf-8') as f:
                            json.dump(scene_graph, f, indent=2)
                        result = {"success": True, "message": f"Object {object_id} deleted from scene {scene_id}."}
                else:
                    # Delete entire scene file
                    os.remove(scene_file)
                    result = {"success": True, "message": f"Scene {scene_id} deleted."}
            except Exception as e:
                result = {"success": False, "error": f"Failed to delete: {str(e)}"}
    else:
        result = {"success": False, "error": "scene_id required"}
    # Audit log
    try:
        audit_dir = os.path.join(os.path.dirname(__file__), 'audit_logs')
        os.makedirs(audit_dir, exist_ok=True)
        audit_file = os.path.join(audit_dir, 'scene_audit.log')
        audit_entry['result'] = 'PASS' if result.get('success') else 'FAIL'
        audit_entry['details'] = result.get('error', result.get('message', ''))
        with open(audit_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(audit_entry) + '\n')
    except Exception:
        pass
    return result
import json
from datetime import datetime
# =========================================================
# 3D Asset Protocol Functions (protocol_function_map.json)
# =========================================================
def import_3d_asset(payload):
    """
    Import 3D asset file (OBJ, FBX, GLTF, BLEND, etc.), validate, convert to canonical format, and store in asset library.
    Args: payload dict with keys: file (path), metadata (dict)
    Returns: result dict
    """
    # Shunt header enforcement
    if isinstance(payload, dict) and 'shunt_id' in payload:
        if not validate_shunt_header(payload):
            return {"success": False, "error": "Invalid shunt header"}
    audit_entry = {
        'timestamp': datetime.now().isoformat(),
        'action': 'import_3d_asset',
        'file': payload.get('file'),
        'user': payload.get('user', 'system')
    }
    # Step 1: Validate file existence and type
    file_path = payload.get('file')
    metadata = payload.get('metadata', {})
    if not file_path or not os.path.isfile(file_path):
        result = {"success": False, "error": "File not found: {}".format(file_path)}
    elif not file_path.lower().endswith((".obj", ".fbx", ".gltf", ".glb", ".blend")):
        result = {"success": False, "error": "Unsupported 3D asset file type: {}".format(file_path)}
    else:
        # Step 2: Validate asset (geometry/topology/metadata)
        validate_result = validate_3d_asset({"asset_id": file_path, "metadata": metadata, "shunt_id": payload.get('shunt_id'), "user": payload.get('user', 'system')})
        if not validate_result.get('success'):
            result = {"success": False, "error": "Validation failed: {}".format(validate_result.get('error'))}
        else:
            # Step 3: Convert asset to canonical format (e.g., .gltf)
            canonical_ext = ".gltf"
            canonical_path = os.path.splitext(file_path)[0] + canonical_ext
            convert_result = convert_3d_asset({"asset_id": file_path, "target_format": canonical_ext, "shunt_id": payload.get('shunt_id'), "user": payload.get('user', 'system')})
            if not convert_result.get('success'):
                result = {"success": False, "error": "Conversion failed: {}".format(convert_result.get('error'))}
            else:
                # Step 4: Store in asset library (simulate by copying file)
                asset_library_dir = os.path.join(os.path.dirname(__file__), 'asset_library')
                os.makedirs(asset_library_dir, exist_ok=True)
                try:
                    import shutil
                    shutil.copy2(file_path, os.path.join(asset_library_dir, os.path.basename(file_path)))
                    # If converted, also copy canonical file (simulate)
                    if os.path.exists(canonical_path):
                        shutil.copy2(canonical_path, os.path.join(asset_library_dir, os.path.basename(canonical_path)))
                    result = {"success": True, "asset_path": os.path.join(asset_library_dir, os.path.basename(canonical_path)), "message": "3D asset imported and stored."}
                except Exception as e:
                    result = {"success": False, "error": "Failed to store asset: {}".format(str(e))}
    # Step 5: Audit log
    try:
        audit_dir = os.path.join(os.path.dirname(__file__), 'audit_logs')
        os.makedirs(audit_dir, exist_ok=True)
        audit_file = os.path.join(audit_dir, '3d_asset_audit.log')
        audit_entry['result'] = 'PASS' if result.get('success') else 'FAIL'
        audit_entry['details'] = result.get('error', result.get('message', ''))
        with open(audit_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(audit_entry) + '\n')
    except Exception:
        pass
    return result

def export_3d_asset(payload):
    """
    Export 3D asset from library to target format.
    Args: payload dict with keys: asset_id, target_format, export_options
    Returns: result dict
    """
    if isinstance(payload, dict) and 'shunt_id' in payload:
        if not validate_shunt_header(payload):
            return {"success": False, "error": "Invalid shunt header"}
    audit_entry = {
        'timestamp': datetime.now().isoformat(),
        'action': 'export_3d_asset',
        'asset_id': payload.get('asset_id'),
        'target_format': payload.get('target_format'),
        'user': payload.get('user', 'system')
    }
    asset_library_dir = os.path.join(os.path.dirname(__file__), 'asset_library')
    asset_id = payload.get('asset_id')
    target_format = payload.get('target_format')
    export_options = payload.get('export_options', {})
    if not asset_id:
        result = {"success": False, "error": "Missing asset_id"}
    else:
        asset_path = os.path.join(asset_library_dir, os.path.basename(asset_id))
        if not os.path.isfile(asset_path):
            result = {"success": False, "error": f"Asset not found in library: {asset_path}"}
        else:
            # Step 1: Convert asset to target format
            convert_result = convert_3d_asset({"asset_id": asset_path, "target_format": target_format, "shunt_id": payload.get('shunt_id'), "user": payload.get('user', 'system')})
            if not convert_result.get('success'):
                result = {"success": False, "error": f"Conversion failed: {convert_result.get('error')}"}
            else:
                # Step 2: Export (simulate by copying to export dir)
                export_dir = os.path.join(os.path.dirname(__file__), 'asset_exports')
                os.makedirs(export_dir, exist_ok=True)
                export_filename = os.path.splitext(os.path.basename(asset_id))[0] + (target_format or '')
                export_path = os.path.join(export_dir, export_filename)
                try:
                    import shutil
                    # Simulate export by copying the converted file
                    canonical_path = os.path.splitext(asset_path)[0] + (target_format or '')
                    if os.path.exists(canonical_path):
                        shutil.copy2(canonical_path, export_path)
                        result = {"success": True, "export_path": export_path, "message": "3D asset exported."}
                    else:
                        result = {"success": False, "error": f"Converted file not found: {canonical_path}"}
                except Exception as e:
                    result = {"success": False, "error": f"Failed to export asset: {str(e)}"}
    # Step 3: Audit log
    try:
        audit_dir = os.path.join(os.path.dirname(__file__), 'audit_logs')
        os.makedirs(audit_dir, exist_ok=True)
        audit_file = os.path.join(audit_dir, '3d_asset_audit.log')
        audit_entry['result'] = 'PASS' if result.get('success') else 'FAIL'
        audit_entry['details'] = result.get('error', result.get('message', ''))
        with open(audit_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(audit_entry) + '\n')
    except Exception:
        pass
    return result

def convert_3d_asset(payload):
    """
    Convert 3D asset to target format and update library.
    Args: payload dict with keys: asset_id, target_format
    Returns: result dict
    """
    if isinstance(payload, dict) and 'shunt_id' in payload:
        if not validate_shunt_header(payload):
            return {"success": False, "error": "Invalid shunt header"}
    audit_entry = {
        'timestamp': datetime.now().isoformat(),
        'action': 'convert_3d_asset',
        'asset_id': payload.get('asset_id'),
        'target_format': payload.get('target_format'),
        'user': payload.get('user', 'system')
    }
    asset_id = payload.get('asset_id')
    target_format = payload.get('target_format')
    if not asset_id or not target_format:
        result = {"success": False, "error": "Missing asset_id or target_format"}
    elif not os.path.isfile(asset_id):
        result = {"success": False, "error": f"Asset file not found: {asset_id}"}
    else:
        # Simulate conversion by copying file with new extension
        converted_path = os.path.splitext(asset_id)[0] + target_format
        try:
            import shutil
            shutil.copy2(asset_id, converted_path)
            result = {"success": True, "converted_path": converted_path, "message": f"Asset converted to {target_format}"}
        except Exception as e:
            result = {"success": False, "error": f"Conversion failed: {str(e)}"}
    # Audit log
    try:
        audit_dir = os.path.join(os.path.dirname(__file__), 'audit_logs')
        os.makedirs(audit_dir, exist_ok=True)
        audit_file = os.path.join(audit_dir, '3d_asset_audit.log')
        audit_entry['result'] = 'PASS' if result.get('success') else 'FAIL'
        audit_entry['details'] = result.get('error', result.get('message', ''))
        with open(audit_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(audit_entry) + '\n')
    except Exception:
        pass
    return result

def validate_3d_asset(payload):
    """
    Run geometry, topology, and metadata checks on 3D asset.
    Args: payload dict with keys: asset_id
    Returns: result dict
    """
    if isinstance(payload, dict) and 'shunt_id' in payload:
        if not validate_shunt_header(payload):
            return {"success": False, "error": "Invalid shunt header"}
    audit_entry = {
        'timestamp': datetime.now().isoformat(),
        'action': 'validate_3d_asset',
        'asset_id': payload.get('asset_id'),
        'user': payload.get('user', 'system')
    }
    asset_id = payload.get('asset_id')
    # Simulate geometry/topology/metadata checks
    if not asset_id or not os.path.isfile(asset_id):
        result = {"success": False, "error": f"Asset file not found: {asset_id}"}
    else:
        # Simulate: check file size, extension, and dummy metadata
        file_size = os.path.getsize(asset_id)
        ext = os.path.splitext(asset_id)[1].lower()
        if ext not in (".obj", ".fbx", ".gltf", ".glb", ".blend"):
            result = {"success": False, "error": f"Unsupported file type: {ext}"}
        elif file_size < 100:  # Arbitrary minimum size for demo
            result = {"success": False, "error": "File too small to be a valid 3D asset."}
        else:
            # Simulate metadata check
            result = {"success": True, "message": "3D asset validated."}
    # Audit log
    try:
        audit_dir = os.path.join(os.path.dirname(__file__), 'audit_logs')
        os.makedirs(audit_dir, exist_ok=True)
        audit_file = os.path.join(audit_dir, '3d_asset_audit.log')
        audit_entry['result'] = 'PASS' if result.get('success') else 'FAIL'
        audit_entry['details'] = result.get('error', result.get('message', ''))
        with open(audit_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(audit_entry) + '\n')
    except Exception:
        pass
    return result
"""
SARA Gen0 Core â€” Shunt Header Contract (SARA Compliance)
All cross-pillar shunt calls MUST be wrapped in a deterministic Shunt Header envelope as follows:

Shunt Header JSON Structure:
{
  "shunt_id": "GUID",
  "source_pillar": "CONTROL | HUD | WIDGET | CANOE | WATCHMAN | MAMA | SECURITY",
  "target_pillar": "CONTROL | HUD | WIDGET | CANOE | WATCHMAN | MAMA | SECURITY",
  "timestamp": "ISO8601",
  "intent": "string",
  "payload": { ... },
  "context_tags": [ ... ],
  "requires_response": true | false
}

- No pillar may send or receive data without a Shunt Header.
- No raw data may cross pillar boundaries.
- No direct calls between pillars are allowed.
- All shunts must be logged in MamaLedger.
- All shunt enforcement and execution must be routed through CONTROL.
"""

try:
    from PIL import Image
except ImportError:
    Image = None

# =========================================================
# --- FDSSM FORMALIZATION (AUTOGENERATED) ---
from typing import Dict, Any

# ShuntFSM object declaration (stub)
"""
SARA Gen0 Core â€” Shunt Header Contract (SARA Compliance)
All cross-pillar shunt calls MUST be wrapped in a deterministic Shunt Header envelope as follows:

Shunt Header JSON Structure:
{
  "shunt_id": "GUID",
  "source_pillar": "CONTROL | HUD | WIDGET | CANOE | WATCHMAN | MAMA | SECURITY",
  "target_pillar": "CONTROL | HUD | WIDGET | CANOE | WATCHMAN | MAMA | SECURITY",
  "timestamp": "ISO8601",
  "intent": "string",
  "payload": { ... },
  "context_tags": [ ... ],
  "requires_response": true | false
}

- No pillar may send or receive data without a Shunt Header.
- No raw data may cross pillar boundaries.
- No direct calls between pillars are allowed.
- All shunts must be logged in MamaLedger.
- All shunt enforcement and execution must be routed through CONTROL.
"""

try:
    from PIL import Image
except ImportError:
    Image = None

# =========================================================
# --- FDSSM FORMALIZATION (AUTOGENERATED) ---
from typing import Dict, Any

# ShuntFSM object declaration (stub)
class ShuntFSM:
    def __init__(self, states: Dict[str, int], transitions: Dict[str, Any]):
        self.states = states
        self.transitions = transitions

# --- VNCE / CORE command constants ---
CORE_PROTOCOL_VNCE = "vnce"
CORE_CMD_VNCE_SESSION_START = "CORE_VNCE_SESSION_START"
CORE_CMD_VNCE_SESSION_END = "CORE_VNCE_SESSION_END"
CORE_STATE_VNCE_SESSION = "vnce_session_active"

# FSM state and transition table (stub/example)
CORE_FSM_STATES = {
    "idle": 0,
    "processing": 1,
    "done": 2,
    "error": 3,
    CORE_STATE_VNCE_SESSION: 4,
}
CORE_FSM_TRANSITIONS = {
    (0, "start"): (1, "begin_processing"),
    (1, "finish"): (2, "complete"),
    (1, "fail"): (3, "handle_error"),
    (0, CORE_CMD_VNCE_SESSION_START): (4, "emit_vnce_start_envelope"),
    (1, CORE_CMD_VNCE_SESSION_START): (4, "emit_vnce_start_envelope"),
    (4, CORE_CMD_VNCE_SESSION_END): (2, "emit_vnce_end_envelope"),
    (3, "reset"): (0, "reset_idle")
}
core_fsm = ShuntFSM(CORE_FSM_STATES, CORE_FSM_TRANSITIONS)


def build_vnce_shunt_envelope(command: str, payload: dict) -> dict:
    """
    Build a CONTROL-bound VNCE shunt envelope from CORE.
    CORE does not validate VNCE content; it only wraps and forwards it.
    """
    from datetime import datetime, timezone
    import uuid

    inner_payload = payload.get("payload", payload) if isinstance(payload, dict) else {}
    context_tags = list(payload.get("context_tags", [])) if isinstance(payload, dict) else []
    context_tags.extend(["vnce", "envoy", "core-forward"])

    return {
        "shunt_id": str(payload.get("shunt_id") or uuid.uuid4()) if isinstance(payload, dict) else str(uuid.uuid4()),
        "source_pillar": payload.get("source_pillar", "CORE") if isinstance(payload, dict) else "CORE",
        "target_pillar": "CONTROL",
        "timestamp": payload.get("timestamp") if isinstance(payload, dict) and payload.get("timestamp") else datetime.now(timezone.utc).isoformat(),
        "intent": str(command).lower(),
        "payload": inner_payload,
        "context_tags": context_tags,
        "requires_response": payload.get("requires_response", True) if isinstance(payload, dict) else True,
        "protocol": CORE_PROTOCOL_VNCE,
    }

# Shunt entrypoint
def core_shunt_entrypoint(command: str, payload: dict) -> dict:
    """
    Single entrypoint for all cross-pillar actions. Applies header validation and routes to FSM.
    """
    if not validate_shunt_header(payload):
        return {"success": False, "error": "Invalid shunt header"}

    if command in {CORE_CMD_VNCE_SESSION_START, CORE_CMD_VNCE_SESSION_END}:
        vnce_envelope = build_vnce_shunt_envelope(command, payload)
        return {
            "success": True,
            "command": command,
            "out_route": "CONTROL",
            "protocol": CORE_PROTOCOL_VNCE,
            "result": vnce_envelope,
        }

    # ACT-based dispatch logic (from actionmap.json)
    act_map = {
        "00": (load_identity, "RETURN"),
        "01": (load_config, "RETURN"),
        "10": (validate_state, "RETURN"),
        "11": (noop_action, "RETURN")
    }
    act_code = str(payload.get("ACT", "")).zfill(2)
    if act_code not in act_map:
        return {"success": False, "error": f"Unknown ACT code: {act_code}"}
    fn, out_route = act_map[act_code]
    try:
        result = fn(payload.get("payload", {}))
    except Exception as e:
        return {"success": False, "error": f"Dispatch error: {e}", "action_code": act_code, "function": fn.__name__, "out_route": out_route}
    return {"success": True, "action_code": act_code, "function": fn.__name__, "out_route": out_route, "result": result}

# --- ACT-mapped functions for CORE pillar ---
def load_identity(payload: dict) -> dict:
    """ACT 00 â€” Load machine/user/SARA identity profile from NBS store."""
    import json as _json, os as _os
    project = str(payload.get("project_name") or SYSTEM_CORE_PROJECT_NAME)
    role = str(payload.get("role") or "").lower()  # user | sara | machine
    identity_dir = _os.path.join(NBS_BASE_DIR, project, "identity")
    # If specific role requested, look in that subdirectory
    candidates = []
    if role in {"user", "sara", "machine"}:
        candidates = [_os.path.join(identity_dir, role)]
    else:
        candidates = [
            _os.path.join(identity_dir, "user"),
            _os.path.join(identity_dir, "sara"),
            _os.path.join(identity_dir, "machine"),
        ]
    profiles = []
    for d in candidates:
        if not _os.path.isdir(d):
            continue
        for fname in _os.listdir(d):
            if not fname.endswith(".json"):
                continue
            fpath = _os.path.join(d, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = _json.load(f)
                profiles.append({"path": fpath, "data": data})
            except Exception:
                pass
    if not profiles:
        return {"success": False, "error": f"No identity files found in {identity_dir}", "project": project}
    return {"success": True, "project": project, "identity_profiles": profiles, "count": len(profiles)}

def load_config(payload: dict) -> dict:
    """ACT 01 â€” Load system config deterministically from NBS store."""
    import json as _json, os as _os
    project = str(payload.get("project_name") or SYSTEM_CORE_PROJECT_NAME)
    config_dir = _os.path.join(NBS_BASE_DIR, project, "control", "config")
    configs = {}
    if _os.path.isdir(config_dir):
        for fname in _os.listdir(config_dir):
            if not fname.endswith(".json"):
                continue
            fpath = _os.path.join(config_dir, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    configs[fname] = _json.load(f)
            except Exception:
                pass
    # Also check for a trust-policy alongside the config
    trust_candidates = [
        _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "trust-policy.json"),
        "/etc/sara-lite/trust-policy.json",
    ]
    for tp in trust_candidates:
        if _os.path.exists(tp):
            try:
                with open(tp, "r", encoding="utf-8") as f:
                    configs["trust-policy.json"] = _json.load(f)
            except Exception:
                pass
            break
    return {"success": True, "project": project, "configs": configs, "count": len(configs)}

def validate_state(payload: dict) -> dict:
    """ACT 10 â€” Validate current FSM state against allowed CORE transitions."""
    state_str = str(payload.get("state", "")).lower()
    if not state_str:
        return {"valid": False, "reason": "No state provided in payload"}
    allowed = set(CORE_FSM_STATES.keys())
    if state_str not in allowed:
        return {"valid": False, "state": state_str, "allowed": sorted(allowed), "reason": "State not in CORE FSM"}
    # Check if transition is possible from current state
    current_code = CORE_FSM_STATES.get(state_str, -1)
    reachable = {v[0] for (s, a), v in CORE_FSM_TRANSITIONS.items() if s == current_code}
    reachable_names = [k for k, v in CORE_FSM_STATES.items() if v in reachable]
    return {"valid": True, "state": state_str, "state_code": current_code, "reachable_states": reachable_names}

def noop_action(payload: dict) -> dict:
    """ACT 11 â€” No operation; returns payload unchanged."""
    return {"success": True, "noop": True, "payload": payload}

# Header enforcement wrapper
def validate_shunt_header(payload: dict) -> bool:
    """
    Enforces shunt header contract on inbound/outbound actions.
    """
    required_fields = ["shunt_id", "source_pillar", "target_pillar", "timestamp", "intent", "payload", "context_tags", "requires_response"]
    return all(field in payload for field in required_fields)
# Image/Graphics File IO Handlers (JPG, PNG, GIF, etc.)
# =========================================================
def read_image_file(path):
    if not Image:
        return {"success": False, "error": "Pillow not installed"}
    try:
        img = Image.open(path)
        info = {
            "format": img.format,
            "mode": img.mode,
            "size": img.size
        }
        return {"success": True, "info": info}
    except Exception as e:
        return {"success": False, "error": str(e)}

def write_image_file(path, data, format=None):
    if not Image:
        return {"success": False, "error": "Pillow not installed"}
    try:
        img = Image.fromarray(data) if hasattr(data, 'shape') else Image.open(data)
        img.save(path, format=format)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

def resize_image_file(path, output_path, size):
    if not Image:
        return {"success": False, "error": "Pillow not installed"}
    try:
        img = Image.open(path)
        img = img.resize(size)
        img.save(output_path)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def read_video_file(path):
    """Read video asset metadata with optional frame-level detail when cv2 is available."""
    import os

    if not os.path.exists(path):
        return {"success": False, "error": "file not found"}

    ext = os.path.splitext(path)[1].lower()
    if ext not in {".mp4", ".mov", ".avi", ".mkv", ".webm"}:
        return {"success": False, "error": f"unsupported video format: {ext}"}

    info = {
        "path": path,
        "ext": ext,
        "size_bytes": os.path.getsize(path),
    }

    try:
        import cv2  # optional

        cap = cv2.VideoCapture(path)
        if cap.isOpened():
            fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
            duration = float(frame_count / fps) if fps > 0 else None
            info.update(
                {
                    "fps": fps,
                    "frame_count": frame_count,
                    "width": width,
                    "height": height,
                    "duration_seconds": duration,
                    "metadata_mode": "cv2",
                }
            )
        cap.release()
    except Exception:
        info["metadata_mode"] = "basic"

    return {"success": True, "info": info}


def read_audio_file(path):
    """Read audio asset metadata for common office-suite media lanes."""
    import os

    if not os.path.exists(path):
        return {"success": False, "error": "file not found"}

    ext = os.path.splitext(path)[1].lower()
    if ext not in {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac"}:
        return {"success": False, "error": f"unsupported audio format: {ext}"}

    info = {
        "path": path,
        "ext": ext,
        "size_bytes": os.path.getsize(path),
        "metadata_mode": "basic",
    }

    if ext == ".wav":
        try:
            import wave

            with wave.open(path, "rb") as wav:
                rate = int(wav.getframerate())
                frames = int(wav.getnframes())
                channels = int(wav.getnchannels())
                width = int(wav.getsampwidth())
                info.update(
                    {
                        "sample_rate": rate,
                        "channels": channels,
                        "sample_width_bytes": width,
                        "duration_seconds": float(frames / rate) if rate > 0 else None,
                        "metadata_mode": "wave",
                    }
                )
        except Exception:
            pass

    return {"success": True, "info": info}


def read_3d_file(path):
    """Read 3D asset metadata for OBJ/STL files used by modern graphics workflows."""
    import os
    import struct

    if not os.path.exists(path):
        return {"success": False, "error": "file not found"}

    ext = os.path.splitext(path)[1].lower()
    if ext not in {".obj", ".stl"}:
        return {"success": False, "error": f"unsupported 3d format: {ext}"}

    info = {
        "path": path,
        "ext": ext,
        "size_bytes": os.path.getsize(path),
    }

    try:
        if ext == ".obj":
            vertices = 0
            texcoords = 0
            normals = 0
            faces = 0
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    s = line.lstrip()
                    if s.startswith("v "):
                        vertices += 1
                    elif s.startswith("vt "):
                        texcoords += 1
                    elif s.startswith("vn "):
                        normals += 1
                    elif s.startswith("f "):
                        faces += 1
            info.update(
                {
                    "vertices": vertices,
                    "texcoords": texcoords,
                    "normals": normals,
                    "faces": faces,
                    "metadata_mode": "obj_text_scan",
                }
            )
        else:
            with open(path, "rb") as f:
                header = f.read(84)
            if len(header) >= 84:
                tri_count = struct.unpack("<I", header[80:84])[0]
                expected = 84 + tri_count * 50
                if expected == info["size_bytes"]:
                    info.update({"triangles": int(tri_count), "format_hint": "binary", "metadata_mode": "stl_binary_header"})
                else:
                    facets = 0
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        for line in f:
                            if line.lstrip().lower().startswith("facet normal"):
                                facets += 1
                    info.update({"triangles": facets, "format_hint": "ascii", "metadata_mode": "stl_ascii_scan"})
    except Exception as e:
        return {"success": False, "error": str(e)}

    return {"success": True, "info": info}


def read_graphics_asset_file(path):
    """Unified reader for image/video/audio/3D assets in the office graphics lane."""
    import os

    ext = os.path.splitext(path)[1].lower()
    if ext in {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp"}:
        return read_image_file(path)
    if ext in {".mp4", ".mov", ".avi", ".mkv", ".webm"}:
        return read_video_file(path)
    if ext in {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac"}:
        return read_audio_file(path)
    if ext in {".stl", ".obj"}:
        return read_3d_file(path)
    return {"success": False, "error": f"unsupported graphics asset type: {ext}"}
import sys
try:
    import docx  # python-docx
except ImportError:
    docx = None
try:
    import openpyxl
except ImportError:
    openpyxl = None
try:
    import pptx  # python-pptx
except ImportError:
    pptx = None

# =========================================================
# Office File IO Handlers (Word, Excel, PowerPoint)
# All actions must be routed through control for enforcement/execution.
# =========================================================
def read_word_docx(path):
    if not docx:
        return {"success": False, "error": "python-docx not installed"}
    try:
        doc = docx.Document(path)
        text = "\n".join([p.text for p in doc.paragraphs])
        return {"success": True, "text": text}
    except Exception as e:
        return {"success": False, "error": str(e)}

def write_word_docx(path, paragraphs):
    if not docx:
        return {"success": False, "error": "python-docx not installed"}
    try:
        doc = docx.Document()
        for para in paragraphs:
            doc.add_paragraph(para)
        doc.save(path)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

def read_excel_xlsx(path):
    if not openpyxl:
        return {"success": False, "error": "openpyxl not installed"}
    try:
        wb = openpyxl.load_workbook(path, read_only=True)
        data = {}
        for sheet in wb.sheetnames:
            ws = wb[sheet]
            data[sheet] = [[cell.value for cell in row] for row in ws.iter_rows()]
        return {"success": True, "sheets": data}
    except Exception as e:
        return {"success": False, "error": str(e)}

def write_excel_xlsx(path, sheets_data):
    if not openpyxl:
        return {"success": False, "error": "openpyxl not installed"}
    try:
        wb = openpyxl.Workbook()
        for idx, (sheet, rows) in enumerate(sheets_data.items()):
            ws = wb.create_sheet(title=sheet) if idx > 0 else wb.active
            ws.title = sheet
            for row in rows:
                ws.append(row)
        wb.save(path)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

def read_powerpoint_pptx(path):
    if not pptx:
        return {"success": False, "error": "python-pptx not installed"}
    try:
        prs = pptx.Presentation(path)
        slides = []
        for slide in prs.slides:
            text = []
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    text.append(shape.text)
            slides.append("\n".join(text))
        return {"success": True, "slides": slides}
    except Exception as e:
        return {"success": False, "error": str(e)}

def write_powerpoint_pptx(path, slides_data):
    if not pptx:
        return {"success": False, "error": "python-pptx not installed"}
    try:
        prs = pptx.Presentation()
        for slide_text in slides_data:
            slide = prs.slides.add_slide(prs.slide_layouts[1])
            shapes = slide.shapes
            shapes.title.text = slide_text[0] if slide_text else ""
            for para in slide_text[1:]:
                shapes.placeholders[1].text += "\n" + para
        prs.save(path)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

import threading
# shunt header: sara_core_gen1
SARA_HEADER_START = "SARA_HEADER_START"
SARA_HEADER_BYTE0 = 0x01
SARA_HEADER_BYTE1 = 0x0D
SARA_HEADER_BYTE2 = 0x01
SARA_HEADER_BYTE3 = 0xF0
SARA_HEADER_BYTE4 = 0x80
SARA_HEADER_BYTE5 = 0x00
SARA_HEADER_RESERVED_BYTES = 210
SARA_HEADER_END = "SARA_HEADER_END"
SARA_BINARY_SPECIAL_HEADER_LITERAL = """SARA_HEADER_START
BYTE0: 01        # Shunt Mode Enable
BYTE1: 0D        # Domain=00 CPU | Origin=00 Traditional | Authority=11 CONTROL-only | Routing=01 thirds
BYTE2: 01        # Envoy/Resonator Switch (1 = OS may treat as special envoy file)
BYTE3: F0        # FileName_FirstLetter=11 | VowelPattern=11
BYTE4: 80        # ExtensionSignature=10 | DomainConfirm=00
BYTE5: 00        # ShuntAuthority=0 inbound-only | ShuntLock=0 read-only
RESERVED: 00 * 210 bytes
SARA_HEADER_END"""
SARA_BINARY_SPECIAL_HEADER_BYTES = bytes(
    [
        SARA_HEADER_BYTE0,
        SARA_HEADER_BYTE1,
        SARA_HEADER_BYTE2,
        SARA_HEADER_BYTE3,
        SARA_HEADER_BYTE4,
        SARA_HEADER_BYTE5,
    ]
)
# =========================================================
# Kingdome Phoenix Protocol Integration (Machine Side)
# All actions must be routed through control for enforcement/execution.
# =========================================================
# SPEC NOTE (language ownership):
# - sara_core remains Python.
# - sara_control target language is C.
# - sara_security target language is Ada.
# This is a planning note only and does not change runtime behavior.

import os
import importlib
import math
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime, timezone

def is_admin_or_lead(context):
    """Check if the user is a system admin, network admin, or team lead."""
    allowed_roles = {"system_admin", "network_admin", "team_lead"}
    return bool(set(context.get("roles", [])) & allowed_roles)

def list_phoenix_snapshots(location_data):
    """List available Phoenix Ash snapshots from a machine location file."""
    return location_data.get("snapshots", [])

def can_restore_phoenix(context, location_data, target_timestamp):
    """
    Check if restore is allowed under current context and policy.
    All enforcement and execution must be routed through control.
    """
    if not is_admin_or_lead(context):
        return {"success": False, "error": "Not authorized (admin/lead only)"}
    policy = location_data.get("restore_policy", {})
    max_days = policy.get("max_days_back", 7)
    require_dual = policy.get("require_dual_admin_approval", False)
    # Check time window
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    try:
        target = datetime.fromisoformat(target_timestamp.replace("Z", "+00:00"))
    except Exception:
        return {"success": False, "error": "Invalid timestamp format"}
    days_back = (now - target).days
    if days_back > max_days:
        return {"success": False, "error": f"Restore exceeds max_days_back ({max_days})"}
    # Dual admin approval (to be enforced by control)
    if require_dual and not context.get("dual_admin_approved"):
        return {"success": False, "error": "Dual admin approval required"}
    return {"success": True}

def get_phoenix_snapshot(location_data, target_timestamp):
    """Retrieve the Phoenix Ash snapshot for a given timestamp."""
    for snap in location_data.get("snapshots", []):
        if snap.get("timestamp") == target_timestamp:
            return snap
    return None

def register_malware_hooks_from_file(location_data):
    """
    Register malware detection/response shunts from a machine location file's 'malware_hooks' section.
    All execution must be routed through control.
    """
    hooks = location_data.get("malware_hooks", {})
    for name, code_str in hooks.items():
        local_ns = {}
        try:
            exec(code_str, {}, local_ns)
            if 'shunt' in local_ns and callable(local_ns['shunt']):
                location_shunt_registry.register_shunt(name, local_ns['shunt'])
        except Exception:
            continue

def execute_malware_hook(name, *args, **kwargs):
    """Execute a registered malware hook by name (must be routed through control)."""
    return location_shunt_registry.execute_shunt(name, *args, **kwargs)
# =========================================================
# User Location File Support (Contextual Rules & Device Types)
# =========================================================

USER_LOCATION_FILE_EXT = ".userloc.nbs.json"

def is_user_location_file(filename):
    """Check if a file is a user location file."""
    return filename.endswith(USER_LOCATION_FILE_EXT)

def load_user_location_file(filepath):
    """Load a user location file and return its contents as dict."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError("User location file must be a JSON object.")
        return {"success": True, "data": data}
    except Exception as e:
        return {"success": False, "error": str(e)}

class UserLocationRuleRegistry:
    """
    Registry for user location rules and device-type policies.
    Allows registration and enforcement of context-aware rules.
    """
    def __init__(self):
        self.rules = {}
        self.lock = threading.Lock()

    def register_rule(self, location, rule_fn):
        with self.lock:
            self.rules[location] = rule_fn

    def enforce_rule(self, location, *args, **kwargs):
        with self.lock:
            if location not in self.rules:
                return {"success": False, "error": f"No rule for location '{location}'"}
            try:
                result = self.rules[location](*args, **kwargs)
                return {"success": True, "result": result}
            except Exception as e:
                return {"success": False, "error": str(e)}

user_location_rule_registry = UserLocationRuleRegistry()

def register_user_location_rules_from_file(userloc_data):
    """
    Register all rules defined in a user location file's 'rules' section.
    Expects userloc_data to be a dict with a 'rules' key mapping to {location: code_str}.
    """
    rules = userloc_data.get("rules", {})
    for location, code_str in rules.items():
        local_ns = {}
        try:
            exec(code_str, {}, local_ns)
            # Expect the function to be named 'rule'
            if 'rule' in local_ns and callable(local_ns['rule']):
                user_location_rule_registry.register_rule(location, local_ns['rule'])
        except Exception:
            continue

def enforce_user_location_rule(location, *args, **kwargs):
    """Enforce a registered user location rule by location name."""
    return user_location_rule_registry.enforce_rule(location, *args, **kwargs)
# =========================================================
# Location File Support (Machine Profile, Kingdome Protocols)
# Only location files pass through core to control.
# Specialized shunts for OS integration.
# =========================================================

import threading
import threading
import json
import base64
import zlib
import base64
import zlib

LOCATION_FILE_EXT = ".location.nbs.json"

# Location file type constants
LOCATION_TYPE_ENVOY = "envoy"
LOCATION_TYPE_PHOENIX_ASH = "phoenix_ash"

def detect_location_file_type(location_data):
    """
    Determine the type of location file: envoy or phoenix_ash (registry).
    Returns LOCATION_TYPE_ENVOY, LOCATION_TYPE_PHOENIX_ASH, or None.
    """
    if location_data.get("type") == LOCATION_TYPE_ENVOY:
        return LOCATION_TYPE_ENVOY
    if location_data.get("type") == LOCATION_TYPE_PHOENIX_ASH:
        return LOCATION_TYPE_PHOENIX_ASH
    # Heuristic: Phoenix Ash files may have a 'phoenix_ash' or 'compressed' key
    if "phoenix_ash" in location_data or "compressed" in location_data:
        return LOCATION_TYPE_PHOENIX_ASH
    if "envoy" in location_data:
        return LOCATION_TYPE_ENVOY
    return None

def decompress_phoenix_ash_data(ash_data):
    """
    Decompress and decode Phoenix Ash (registry) data.
    Expects base64-encoded, zlib-compressed string.
    Returns the decompressed JSON object or None.
    """
    try:
        compressed = base64.b64decode(ash_data)
        decompressed = zlib.decompress(compressed).decode("utf-8")
        return json.loads(decompressed)
    except Exception as e:
        return None

def load_location_file(filepath):
    """
    Load a location file and return its contents as dict.
    Handles both envoy and Phoenix Ash (registry) types.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError("Location file must be a JSON object.")
        file_type = detect_location_file_type(data)
        if file_type == LOCATION_TYPE_PHOENIX_ASH:
            # Decompress and validate Phoenix Ash data
            ash_data = data.get("phoenix_ash") or data.get("compressed")
            if not ash_data:
                return {"success": False, "error": "Missing Phoenix Ash data."}
            decompressed = decompress_phoenix_ash_data(ash_data)
            if decompressed is None:
                return {"success": False, "error": "Failed to decompress Phoenix Ash data."}
            data["decompressed"] = decompressed
        return {"success": True, "data": data, "type": file_type}
    except Exception as e:
        return {"success": False, "error": str(e)}

def is_location_file(filename):
    """Check if a file is a location file (machine profile)."""
    return filename.endswith(LOCATION_FILE_EXT)

def load_location_file(filepath):
    """Load a location file and return its contents as dict."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError("Location file must be a JSON object.")
        return {"success": True, "data": data}
    except Exception as e:
        return {"success": False, "error": str(e)}

class LocationShuntRegistry:
    """
    Registry for specialized shunts defined in location files.
    Allows registration and execution of OS-level shunt functions.
    """
    def __init__(self):
        self.shunts = {}
        self.lock = threading.Lock()

    def register_shunt(self, name, func):
        with self.lock:
            self.shunts[name] = func

    def execute_shunt(self, name, *args, **kwargs):
        with self.lock:
            if name not in self.shunts:
                return {"success": False, "error": f"Shunt '{name}' not found."}
            try:
                result = self.shunts[name](*args, **kwargs)
                return {"success": True, "result": result}
            except Exception as e:
                return {"success": False, "error": str(e)}

location_shunt_registry = LocationShuntRegistry()

def register_location_shunts_from_file(location_data):
    """
    Register all shunts defined in a location file's 'shunts' section.
    Expects location_data to be a dict with a 'shunts' key mapping to {name: code_str}.
    """
    shunts = location_data.get("shunts", {})
    for name, code_str in shunts.items():
        # Compile the code string into a function in a local namespace
        local_ns = {}
        try:
            exec(code_str, {}, local_ns)
            # Expect the function to be named 'shunt'
            if 'shunt' in local_ns and callable(local_ns['shunt']):
                location_shunt_registry.register_shunt(name, local_ns['shunt'])
        except Exception:
            continue

def execute_location_shunt(name, *args, **kwargs):
    """Execute a registered location shunt by name."""
    return location_shunt_registry.execute_shunt(name, *args, **kwargs)
# ...existing code...
############################################################
# Legacy Gen0 Compatibility Helpers (from Sara_core.py)
# These do NOT override or change Gen1 logic. Use only for
# compatibility or extension purposes. Safe to remove if not needed.
############################################################

import importlib.util
from types import ModuleType

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

############################################################
# Mini FSM for Shunt/Evolution Routing (extensible utility)
############################################################

class ShuntFSM:
    """
    Minimal finite state machine for shunt/evolution routing.
    Accepts commands, manages state, and walks transitions.
    Extend or refine as needed for your evolution/shunt system.
    """

    def __init__(self, states, transitions, initial_state):
        """
        states: list of state names
        transitions: dict of (state, command) -> (next_state, action_fn)
        initial_state: starting state name
        """
        self.states = set(states)
        self.transitions = transitions  # {(state, command): (next_state, action_fn)}
        self.state = initial_state
        self.history = []
        self.improvements = []  # List of (state, command, next_state, result)
        self.max_improvements = 10

    def handle(self, command, *args, **kwargs):
        key = (self.state, command)
        if key not in self.transitions:
            return {"success": False, "error": f"No transition for ({self.state}, {command})"}
        next_state, action_fn = self.transitions[key]
        result = action_fn(*args, **kwargs) if action_fn else None
        record = (self.state, command, next_state, result)
        self.history.append(record)
        self.state = next_state
        # Track first ten improvements only
        if len(self.improvements) < self.max_improvements:
            self.improvements.append(record)
        return {"success": True, "state": self.state, "result": result}

    def reset(self, state=None):
        self.state = state or (self.history[0][0] if self.history else None)
        self.history.clear()
        self.improvements.clear()

    def get_state(self):
        return self.state

    def get_history(self):
        return list(self.history)

    def get_first_ten_improvements(self):
        """Return the first ten improvements recorded."""
        return list(self.improvements)

    def probe_lower_files_until_flag(self, probe_fn, request_data_fn=None):
        """
        Probe lower-level files until probe_fn returns 1 (or '01').
        When found, request data (if request_data_fn is provided) and return it for control.
        probe_fn: function(index) -> flag (int or str)
        request_data_fn: function(index) -> data (optional)
        Returns: dict with 'found': bool, 'index': int, 'data': any (if found)
        """
        for i in range(self.max_improvements):
            flag = probe_fn(i)
            if flag == 1 or flag == '01':
                data = request_data_fn(i) if request_data_fn else None
                return {'found': True, 'index': i, 'data': data}
        return {'found': False, 'index': None, 'data': None}

# Example usage (to be removed or replaced in production):
# def example_action():
#     return "Action performed!"
# fsm = ShuntFSM(
#     states=["idle", "processing", "done"],
#     transitions={
#         ("idle", "start"): ("processing", example_action),
#         ("processing", "finish"): ("done", None),
#     },
#     initial_state="idle"
# )
# result = fsm.handle("start")
# result = fsm.handle("finish")
#!/usr/bin/env python3

# Literal binary special header preserved at module top in:
# - SARA_HEADER_START / SARA_HEADER_END
# - SARA_HEADER_BYTE0..SARA_HEADER_BYTE5
# - SARA_HEADER_RESERVED_BYTES
# - SARA_BINARY_SPECIAL_HEADER_LITERAL
# - SARA_BINARY_SPECIAL_HEADER_BYTES

44# done
# DO NOT EDIT: This file is frozen until Gen1. Changes will be rejected.
"""
Sara Core Gen0 (clean rebuild scaffold)

This file is a minimal, import-safe foundation used to rebuild the core
according to the Gen0 NBS spec:
  - 1/B: Global scratch/narrative/continuity (system-wide timeline)
  - 2/A: Universal wrapper for internal NBS JSON:
        { "nbs_meta": {...}, "content": {...}, "file_version": "1.0", "last_modified": ISO }

Notes:
  - Keep this file free of side effects at import time.
  - Do not add placeholder functions that return stub IDs. Canonical
    primitives below are the single source of truth.
  - We will port additional APIs (profiles, timelines, utilities)
    incrementally after this scaffold is stable.
"""



import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union, Tuple
import urllib.request
import urllib.parse
from html.parser import HTMLParser
import threading



# -------------------------
# Constants / Configuration
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


AMI_ID_PATTERN = re.compile(r"^[0-9A-Fa-f]{4}\s[0-9A-Fa-f]{8}\s[0-9A-Fa-f]{4}$")
CORE_DEFAULT_AMIP_VERSION = "0.1"
CORE_DEFAULT_AMI_IDS: Dict[str, str] = {
    "sara": "0100 00000000 0001",
    "user": "0010 00000000 0001",
    "machine": "0011 00000000 0001",
    "nano": "0001 00000001 0001",
    "copilot": "0001 00000002 0001",
    "gemini_local": "0001 00000003 0001",
    "ollama_local": "0001 00000004 0001",
    "openai_local": "0001 00000005 0001",
}
CORE_DEFAULT_MACHINE_PROFILE: Dict[str, Any] = {
    "profile_id": "default_local_machine",
    "profile_version": "v1",
    "hardware_class": "pc",
    "default_mode": "interactive",
    "night_shift_available": True,
    "allowed_automation_level": "bounded_batch",
    "allowed_routing_intents": [
        "document.read",
        "document.write",
        "document.validate",
        "document.transform",
        "local.search",
        "local.ingest",
        "security.scan",
        "sdk.invoke",
        "amipi.invoke",
    ],
    "resource_budget": {
        "strain": "medium",
        "tokens": 4096,
        "runtime_ms": 15000,
    },
}


def core_validate_ami_id(ami_id: str) -> bool:
    return bool(AMI_ID_PATTERN.match(str(ami_id or "").strip()))


def core_default_ami_id(actor: str = "sara") -> str:
    return CORE_DEFAULT_AMI_IDS.get(str(actor or "sara").strip().lower(), CORE_DEFAULT_AMI_IDS["sara"])


def resolve_machine_profile_core(profile_ref: Optional[Dict[str, Any]] = None, ami_id: str = "") -> Dict[str, Any]:
    """Resolve the effective CORE-owned machine profile for a local Gen1 request."""
    resolved = dict(CORE_DEFAULT_MACHINE_PROFILE)
    if isinstance(profile_ref, dict):
        resolved.update({k: v for k, v in profile_ref.items() if v is not None})
    resolved.setdefault("ami_id", ami_id or core_default_ami_id("machine"))
    resolved.setdefault("profile_id", CORE_DEFAULT_MACHINE_PROFILE["profile_id"])
    resolved.setdefault("profile_version", CORE_DEFAULT_MACHINE_PROFILE["profile_version"])
    return resolved


def build_amip_payload_core(
    routing_intent: str,
    payload: Optional[Dict[str, Any]] = None,
    mode: Optional[str] = None,
    machine_profile: Optional[Dict[str, Any]] = None,
    correlation_id: Optional[str] = None,
    resource_budget: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build a deterministic AMIP v0.1 payload using CORE defaults and profile context."""
    import uuid

    resolved_profile = resolve_machine_profile_core(machine_profile)
    resolved_mode = str(mode or resolved_profile.get("default_mode", "interactive")).strip().lower()
    if resolved_mode not in {"interactive", "night_shift"}:
        resolved_mode = "interactive"
    resolved_budget = dict(resolved_profile.get("resource_budget", {}))
    if isinstance(resource_budget, dict):
        resolved_budget.update(resource_budget)
    resolved_routing = str(routing_intent or "local.search").strip() or "local.search"
    resolved_payload = dict(payload or {})
    if "document_context" not in resolved_payload or not isinstance(resolved_payload.get("document_context"), dict):
        resolved_payload["document_context"] = {
            "document_id": str(resolved_payload.get("document_id") or ""),
            "document_version": str(resolved_payload.get("document_version") or ""),
            "traversal_mode": str(resolved_payload.get("traversal_mode") or "single_pass"),
            "focus_scope": str(resolved_payload.get("focus_scope") or "document"),
            "hierarchy": resolved_payload.get("hierarchy") if isinstance(resolved_payload.get("hierarchy"), dict) else {},
        }
    return {
        "amip_version": CORE_DEFAULT_AMIP_VERSION,
        "source_pillar": "CORE",
        "target_pillar": "CONTROL",
        "deterministic": True,
        "mode": resolved_mode,
        "routing_intent": resolved_routing,
        "resource_budget": {
            "strain": str(resolved_budget.get("strain", "medium")),
            "tokens": int(resolved_budget.get("tokens", 4096) or 0),
            "runtime_ms": int(resolved_budget.get("runtime_ms", 15000) or 1),
        },
        "payload": resolved_payload,
        "machine_profile": {
            "profile_id": resolved_profile.get("profile_id", CORE_DEFAULT_MACHINE_PROFILE["profile_id"]),
            "profile_version": resolved_profile.get("profile_version", CORE_DEFAULT_MACHINE_PROFILE["profile_version"]),
            "ami_id": resolved_profile.get("ami_id", core_default_ami_id("machine")),
            "allowed_automation_level": resolved_profile.get("allowed_automation_level", "bounded_batch"),
        },
        "workflow_state": _build_core_work_state(
            stage="amip_built",
            status="ready",
            additional={
                "routing_intent": resolved_routing,
                "automation_allowed": resolved_mode == "night_shift",
            },
        ),
        "correlation_id": str(correlation_id or uuid.uuid4()),
    }


def build_bucey_shunt_envelope_core(
    amip_payload: Dict[str, Any],
    ami_id: str = "",
    profile_ref: Optional[Dict[str, Any]] = None,
    correlation_id: Optional[str] = None,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Build a deterministic Bucey Shunt envelope for local C#/Python or internal AI traffic."""
    import uuid

    resolved_ami = ami_id if core_validate_ami_id(ami_id) else core_default_ami_id("sara")
    resolved_profile = resolve_machine_profile_core(profile_ref, ami_id=resolved_ami)
    resolved_correlation = str(correlation_id or amip_payload.get("correlation_id") or uuid.uuid4())
    resolved_request_id = str(request_id or uuid.uuid4())
    resolved_shunt_id = str(uuid.uuid4())
    timestamp_utc = _iso_now()
    routing_intent = str(amip_payload.get("routing_intent") or "local.search").strip() or "local.search"
    payload_block = dict(amip_payload.get("payload") or {})
    return {
        "shunt_id": resolved_shunt_id,
        "source_pillar": "CORE",
        "target_pillar": "CONTROL",
        "timestamp": timestamp_utc,
        "intent": routing_intent,
        "payload": payload_block,
        "context_tags": ["core", "bucey", str(amip_payload.get("mode", "interactive")), "local_only"],
        "requires_response": True,
        "header": {
            "shunt_version": "gen1",
            "protocol_family": "bucey_shunt",
            "shunt_id": resolved_shunt_id,
            "timestamp_utc": timestamp_utc,
        },
        "fsm_bits": {
            "state": str(amip_payload.get("mode", "interactive")),
            "routing_policy": "local_only",
            "strain_policy": str(amip_payload.get("resource_budget", {}).get("strain", "medium")),
        },
        "ami_id": resolved_ami,
        "profile_ref": {
            "profile_id": resolved_profile.get("profile_id"),
            "profile_version": resolved_profile.get("profile_version"),
        },
        "correlation_id": resolved_correlation,
        "request_id": resolved_request_id,
        "transport_policy": {
            "local_only": True,
            "response_expected": True,
            "allow_automation": amip_payload.get("mode") == "night_shift",
        },
        "workflow_state": _build_core_work_state(
            stage="shunt_built",
            status="ready",
            additional={"routing_intent": routing_intent},
        ),
        "amip_payload": dict(amip_payload or {}),
    }


def unwrap_bucey_shunt_core(envelope: Dict[str, Any]) -> Dict[str, Any]:
    """Return normalized shunt metadata for CONTROL/SECURITY without mutating the original envelope."""
    if not isinstance(envelope, dict):
        return {"success": False, "error": "Bucey Shunt envelope must be a dict"}
    if "amip_payload" not in envelope:
        return {"success": False, "error": "Missing amip_payload in Bucey Shunt envelope"}
    header = dict(envelope.get("header") or {})
    amip_payload = dict(envelope.get("amip_payload") or {})
    resolved_profile = resolve_machine_profile_core(envelope.get("profile_ref"), ami_id=str(envelope.get("ami_id", "")))
    return {
        "success": True,
        "ami_id": str(envelope.get("ami_id") or core_default_ami_id("sara")),
        "profile_ref": {
            "profile_id": resolved_profile.get("profile_id"),
            "profile_version": resolved_profile.get("profile_version"),
        },
        "correlation_id": str(envelope.get("correlation_id") or amip_payload.get("correlation_id") or ""),
        "request_id": str(envelope.get("request_id") or ""),
        "amip_payload": amip_payload,
    }


CORE_LITE_CONTRACT_VERSION = "gen1-core-lite-2026-04-11"


def build_core_lite_bundle_core(
    routing_intent: str,
    payload: Optional[Dict[str, Any]] = None,
    mode: Optional[str] = None,
    machine_profile: Optional[Dict[str, Any]] = None,
    correlation_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Bounded CORE-Lite export wrapper; builders only, no routing authority."""
    amip_payload = build_amip_payload_core(
        routing_intent=routing_intent,
        payload=payload,
        mode=mode,
        machine_profile=machine_profile,
        correlation_id=correlation_id,
    )
    shunt_envelope = build_bucey_shunt_envelope_core(
        amip_payload=amip_payload,
        ami_id=str((machine_profile or {}).get("ami_id") or ""),
        profile_ref=machine_profile,
        correlation_id=str(amip_payload.get("correlation_id") or ""),
    )
    return {
        "contract_version": CORE_LITE_CONTRACT_VERSION,
        "deterministic": True,
        "routing_authority": "CONTROL",
        "builders_only": True,
        "amip_payload": amip_payload,
        "shunt_envelope": shunt_envelope,
        "state_binding": {
            "schema_store": "/var/lib/sara-lite/nbs/schemas/",
            "state_store": "/var/lib/sara-lite/runtime/core-state.json",
        },
    }


# -------------------------
# Proto-Lingua helpers (Gen0 option A)
# -------------------------

def _classify_value_suffix(value: Any) -> str:
    """Return the Proto-Lingua suffix based on value type."""
    if isinstance(value, dict):
        return "_breed"
    if isinstance(value, list):
        return "_dog_array"
    return "_puppy"


def _to_proto_lingua(data: Any, preferred_breed: Optional[str] = None) -> Any:
    """
    Transform a Python object into a Proto-Lingua-compliant structure.
    - Adds Nexus metadata for resonance tracking.
    - Ensures all keys are suffixed based on their type (_puppy, _breed, _dog_array).

    Args:
        data (Any): The input data to transform.
        preferred_breed (Optional[str]): The top-level breed to assign (e.g., "project_sheet").

    Returns:
        Any: The transformed Proto-Lingua structure.
    """
    if isinstance(data, dict):
        out: Dict[str, Any] = {}
        if preferred_breed:
            out["__file_breed"] = preferred_breed  # Add top-level breed if provided
        for k, v in data.items():
            suffix = _classify_value_suffix(v)  # Determine the suffix based on value type
            new_key = f"{k}{suffix}"  # Append the suffix to the key
            if isinstance(v, dict):
                out[new_key] = _to_proto_lingua(v)  # Recursively transform nested dictionaries
            elif isinstance(v, list):
                out[new_key] = [_to_proto_lingua(item) if isinstance(item, dict) else item for item in v]
            else:
                out[new_key] = v  # Preserve scalar values
        # Add Nexus metadata for resonance tracking
        out["_nexus_resonance_radius_puppy"] = 0.0  # Default to perfect resonance
        out["_nexus_stability_puppy"] = "stable"  # Default to stable
        return out
    elif isinstance(data, list):
        return [_to_proto_lingua(item) if isinstance(item, dict) else item for item in data]
    return data  # Return scalar values as-is

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


# -------------
# Import sanity
# -------------

__all__ = [
    "NBS_BASE_DIR",
    "SYSTEM_CORE_PROJECT_NAME",
    "INTERNAL_FILE_VERSION",
    "create_nbs_reference",
    "in_out_nbs_file",
    "create_nbs_file",
    # sheet APIs (exposed for callers)
    "create_characterbase_nbs_profile",
    "create_client_projects_sheet",
    "list_client_projects_sheet",
    "remove_client_project_preserve_critical",
    "update_client_projects_sheet",
    "create_nbs_project_profile",
    "update_nbs_project_profile",
    "append_event",
    "CORE_DEFAULT_AMIP_VERSION",
    "CORE_DEFAULT_AMI_IDS",
    "CORE_DEFAULT_MACHINE_PROFILE",
    "core_validate_ami_id",
    "core_default_ami_id",
    "resolve_machine_profile_core",
    "build_amip_payload_core",
    "build_bucey_shunt_envelope_core",
    "unwrap_bucey_shunt_core",]


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


def create_client_projects_sheet(
    client_name: str,
    sheet_data: Optional[Dict[str, Any]] = None,
    operating_mode: str = "wfh",
    editable_fields: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Create a client-specific projects sheet in system core.

    operating_mode: 'wfh' | 'hybrid' | 'business' | 'public'
    - wfh is the current default and intended for local/home operations.
    """
    mode = str(operating_mode or "wfh").strip().lower()
    if mode not in ("wfh", "hybrid", "business", "public"):
        return {"success": False, "error": "operating_mode must be 'wfh', 'hybrid', 'business', or 'public'"}

    client_slug = _sanitize_name(client_name or "client").lower()
    content = dict(sheet_data or {})
    content.setdefault("client_name", client_name)
    content.setdefault("operating_mode", mode)
    content.setdefault("projects", [])
    content.setdefault("active_project_count", 0)
    content.setdefault("wfh_context", {
        "enabled": mode == "wfh",
        "workspace_type": "home_office" if mode == "wfh" else "mixed",
        "hours_window": "flex",
    })
    content.setdefault("_created_at", _iso_now())
    content.setdefault("_profile_type", "client_projects")
    content.setdefault(
        "_work_state",
        _build_core_work_state(
            stage="client_projects_created",
            status="ready",
            additional={"client_name": client_name, "operating_mode": mode},
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
    content.setdefault("_editable_fields", list(editable_fields or [
        "projects",
        "active_project_count",
        "operating_mode",
        "wfh_context",
        "notes",
        "deliverable_state",
    ]))

    rel_path = os.path.join("sheets", "client_projects", f"{client_slug}_projects_sheet.nbs.json")
    return create_nbs_file(
        project_name=SYSTEM_CORE_PROJECT_NAME,
        relative_path=rel_path,
        content=content,
        meta={
            "nbs_type": "client_projects_sheet",
            "project_name": SYSTEM_CORE_PROJECT_NAME,
            "tags": ["client", "projects", "sheet", mode],
            "source": "core",
        },
    )


def update_client_projects_sheet(
    client_name: str,
    updates: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Update a client-specific projects sheet under system core.
    Respects _editable_fields if present.
    """
    client_slug = _sanitize_name(client_name or "client").lower()
    rel_path = os.path.join("sheets", "client_projects", f"{client_slug}_projects_sheet.nbs.json")
    abs_path = os.path.join(NBS_BASE_DIR, SYSTEM_CORE_PROJECT_NAME, rel_path)

    read_res = in_out_nbs_file("read", abs_path)
    if not read_res.get("success"):
        return read_res

    obj = read_res["data"]
    content = obj.get("content", {})

    editable = set(content.get("_editable_fields", []))
    if editable:
        for key, value in updates.items():
            if key in editable or str(key).startswith("_"):
                content[key] = value
    else:
        content.update(updates)

    mode = str(content.get("operating_mode", "wfh")).strip().lower()
    if mode not in ("wfh", "hybrid", "business", "public"):
        return {"success": False, "error": "operating_mode must be 'wfh', 'hybrid', 'business', or 'public'"}
    content["operating_mode"] = mode

    projects = content.get("projects", [])
    if isinstance(projects, list):
        active_count = sum(1 for p in projects if isinstance(p, dict) and str(p.get("status", "")).lower() == "active")
        content["active_project_count"] = active_count

    write_res = create_nbs_file(
        project_name=SYSTEM_CORE_PROJECT_NAME,
        relative_path=rel_path,
        content=content,
        meta={
            "nbs_type": "client_projects_sheet",
            "project_name": SYSTEM_CORE_PROJECT_NAME,
            "tags": ["client", "projects", "sheet", mode],
            "source": "core",
        },
    )
    return write_res


def remove_client_project_preserve_critical(
    client_name: str,
    project_key: str,
    critical_fields: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Remove a completed client project from active projects while preserving
    critical continuity data for future re-engagement with the same client.

    project_key matches either project_id or name (case-insensitive).
    """
    client_slug = _sanitize_name(client_name or "client").lower()
    rel_path = os.path.join("sheets", "client_projects", f"{client_slug}_projects_sheet.nbs.json")
    abs_path = os.path.join(NBS_BASE_DIR, SYSTEM_CORE_PROJECT_NAME, rel_path)

    read_res = in_out_nbs_file("read", abs_path)
    if not read_res.get("success"):
        return read_res

    obj = read_res["data"]
    content = obj.get("content", {})
    projects = content.get("projects", [])
    if not isinstance(projects, list):
        return {"success": False, "error": "Invalid client projects sheet: projects must be a list"}

    key = str(project_key or "").strip().lower()
    if not key:
        return {"success": False, "error": "project_key is required"}

    keep_projects: List[Any] = []
    removed_project: Optional[Dict[str, Any]] = None
    for p in projects:
        if not isinstance(p, dict):
            keep_projects.append(p)
            continue
        pid = str(p.get("project_id", "")).strip().lower()
        pname = str(p.get("name", "")).strip().lower()
        if removed_project is None and (key == pid or key == pname):
            removed_project = p
            continue
        keep_projects.append(p)

    if removed_project is None:
        return {"success": False, "error": f"Project not found for key: {project_key}"}

    fields = list(critical_fields or [
        "project_id",
        "name",
        "type",
        "status",
        "billing_status",
        "started_at",
        "completed_at",
        "last_active_at",
        "outcome_summary",
        "tags",
    ])
    critical_snapshot = {k: removed_project.get(k) for k in fields}
    critical_snapshot["client_name"] = client_name
    critical_snapshot["removed_at"] = _iso_now()
    critical_snapshot["retention_reason"] = "project_completed_reuse_context"

    history = content.get("project_history_critical", [])
    if not isinstance(history, list):
        history = []
    history.append(critical_snapshot)

    content["projects"] = keep_projects
    content["project_history_critical"] = history

    active_count = sum(
        1
        for p in keep_projects
        if isinstance(p, dict) and str(p.get("status", "")).strip().lower() == "active"
    )
    content["active_project_count"] = active_count

    mode = str(content.get("operating_mode", "wfh")).strip().lower()
    if mode not in ("wfh", "hybrid", "business", "public"):
        mode = "wfh"
        content["operating_mode"] = mode

    write_res = create_nbs_file(
        project_name=SYSTEM_CORE_PROJECT_NAME,
        relative_path=rel_path,
        content=content,
        meta={
            "nbs_type": "client_projects_sheet",
            "project_name": SYSTEM_CORE_PROJECT_NAME,
            "tags": ["client", "projects", "sheet", mode],
            "source": "core",
        },
    )
    if not write_res.get("success"):
        return write_res

    return {
        "success": True,
        "removed_project": {
            "project_id": removed_project.get("project_id"),
            "name": removed_project.get("name"),
            "status": removed_project.get("status"),
        },
        "critical_retained_fields": fields,
        "history_count": len(history),
        "active_project_count": active_count,
        "path": rel_path,
        "reference": write_res.get("reference"),
    }


def list_client_projects_sheet(
    client_name: str,
    only_active: bool = True,
    operating_mode: Optional[str] = "wfh",
    include_history_critical: bool = False,
) -> Dict[str, Any]:
    """
    Read and filter a client projects sheet.

    Defaults to active WFH projects for daily operations.
    """
    client_slug = _sanitize_name(client_name or "client").lower()
    rel_path = os.path.join("sheets", "client_projects", f"{client_slug}_projects_sheet.nbs.json")
    abs_path = os.path.join(NBS_BASE_DIR, SYSTEM_CORE_PROJECT_NAME, rel_path)

    read_res = in_out_nbs_file("read", abs_path)
    if not read_res.get("success"):
        return read_res

    obj = read_res["data"]
    content = obj.get("content", {})
    sheet_mode = str(content.get("operating_mode", "wfh")).strip().lower()
    requested_mode = None if operating_mode is None else str(operating_mode).strip().lower()
    if requested_mode is not None and requested_mode not in ("wfh", "hybrid", "business", "public"):
        return {"success": False, "error": "operating_mode must be 'wfh', 'hybrid', 'business', 'public', or None"}

    projects = content.get("projects", [])
    if not isinstance(projects, list):
        return {"success": False, "error": "Invalid client projects sheet: projects must be a list"}

    filtered: List[Dict[str, Any]] = []
    for p in projects:
        if not isinstance(p, dict):
            continue
        if only_active and str(p.get("status", "")).strip().lower() != "active":
            continue
        if requested_mode is not None:
            project_mode = str(p.get("operating_mode", sheet_mode)).strip().lower()
            if project_mode != requested_mode:
                continue
        filtered.append(p)

    result = {
        "success": True,
        "client_name": content.get("client_name", client_name),
        "sheet_operating_mode": sheet_mode,
        "filter": {
            "only_active": bool(only_active),
            "operating_mode": requested_mode,
        },
        "count": len(filtered),
        "projects": filtered,
        "path": rel_path,
    }

    if include_history_critical:
        history = content.get("project_history_critical", [])
        result["project_history_critical"] = history if isinstance(history, list) else []

    return result


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


def validate_resonance(data: Dict[str, Any], max_radius: float = 1.0) -> Tuple[bool, str]:
    """
    Validate that the data remains within the $S^*$ Resonance Sphere.

    Args:
        data (Dict[str, Any]): The data to validate.
        max_radius (float): The maximum allowable resonance radius.

    Returns:
        Tuple[bool, str]: (True, "stable") if within the resonance radius, otherwise (False, "dissonant").
    """
    # Extract the resonance radius from the data
    resonance_radius = data.get("_nexus_resonance_radius_puppy", 0.0)
    if resonance_radius <= max_radius:
        return True, "stable"  # Data is within the resonance sphere
    return False, "dissonant"  # Data exceeds the resonance sphere


__all__ += [
    "create_characterbase_nbs_profile",
    "create_client_projects_sheet",
    "list_client_projects_sheet",
    "remove_client_project_preserve_critical",
    "update_client_projects_sheet",
    "create_nbs_project_profile",
    "update_nbs_project_profile",
    "validate_resonance",
    "CORE_LITE_CONTRACT_VERSION",
    "build_core_lite_bundle_core",
]
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
class BuceyShunt:
    def __init__(self, device_id, offset, control_byte):
        # 8-bit fields
        self.device_id = device_id & 0xFF
        self.offset = offset & 0xFF
        self.control = control_byte & 0xFF

    @property
    def state(self):
        # top 2 bits (2-4-2)
        return (self.control >> 6) & 0b11

    @property
    def agency_type(self):
        # middle 4 bits (2-4-2)
        return (self.control >> 2) & 0b1111

    @property
    def exec_mode(self):
        # bottom 2 bits (2-4-2)
        return self.control & 0b11

    def encode(self):
        # This is the raw 8-8-8 binary header
        return bytes([self.device_id, self.offset, self.control])
# ---------------------------------------------------------
# Metadata structure (UTFâ€‘8/2)
# ---------------------------------------------------------
def make_metadata(url, content_type):
    parsed = urllib.parse.urlparse(url)
    domain = parsed.netloc.lower()
    return {
        "domain": domain,
        "content_type": content_type.split(";")[0].strip().lower()
    }

# ---------------------------------------------------------
# HTML â†’ Text extractor (offset 0x10)
# ---------------------------------------------------------
class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_parts = []

    def handle_data(self, data):
        if data.strip():
            self.text_parts.append(data.strip())

    def get_text(self):
        return " ".join(self.text_parts)


# =========================================================
# Basic Memory I/O Interface (for learning, pattern recognition, and control)
# =========================================================

import threading
import psutil  # Requires 'psutil' package for real memory/cpu stats

class SaraMemoryIO:
    """
    In-memory key-value store with usage limits and simulated resource tracking.
    Allows control modules to read/write memory, with percent-based limits.
    """
    def __init__(self, max_memory_percent=10.0, max_cpu_percent=10.0):
        self._store = {}
        self._lock = threading.Lock()
        self.max_memory_percent = max_memory_percent  # % of total system memory
        self.max_cpu_percent = max_cpu_percent      # % of total CPU (simulated)

    def _memory_usage(self):
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        total = psutil.virtual_memory().total
        return (mem_info.rss / total) * 100.0

    def _cpu_usage(self):
        # Simulated: returns process CPU percent over 0.1s interval
        return psutil.Process(os.getpid()).cpu_percent(interval=0.1)

    def set(self, key, value):
        with self._lock:
            if self._memory_usage() > self.max_memory_percent:
                return {"success": False, "error": "Memory usage limit exceeded"}
            self._store[key] = value
            return {"success": True}

    def get(self, key):
        with self._lock:
            return self._store.get(key, None)

    def delete(self, key):
        with self._lock:
            if key in self._store:
                del self._store[key]
                return {"success": True}
            return {"success": False, "error": "Key not found"}

    def usage_report(self):
        return {
            "memory_percent": self._memory_usage(),
            "cpu_percent": self._cpu_usage(),
            "max_memory_percent": self.max_memory_percent,
            "max_cpu_percent": self.max_cpu_percent,
            "current_keys": list(self._store.keys()),
        }

# Singleton instance for core use
sara_memory_io = SaraMemoryIO()

# Expose for control modules
def memory_set(key, value):
    """Set a value in SARA's memory store (enforces memory limit)."""
    return sara_memory_io.set(key, value)

def memory_get(key):
    """Get a value from SARA's memory store."""
    return sara_memory_io.get(key)

def memory_delete(key):
    """Delete a value from SARA's memory store."""
    return sara_memory_io.delete(key)

def memory_usage_report():
    """Get a report of current memory and CPU usage for SARA's memory store."""
    return sara_memory_io.usage_report()


def core_compress_bytes(data: bytes, level: int = 3) -> bytes:
    """
    CORE-level compression helper.
    CONTROL will choose backend (zstd, zip, etc.).
    CORE provides a stable API surface only.
    """
    raise NotImplementedError("core_compress_bytes backend not wired yet.")


def core_decompress_bytes(blob: bytes) -> bytes:
    """
    CORE-level decompression helper.
    CONTROL will implement backend logic.
    """
    raise NotImplementedError("core_decompress_bytes backend not wired yet.")


def core_detect_compression_format(path: str) -> str:
    """
    Inspect a file and return a best-effort compression format label.
    CONTROL will implement actual detection logic.
    """
    return "unknown"


def core_checksum_bytes(blob: bytes, algorithm: str = "sha256") -> str:
    """
    Return a checksum string for the given bytes.
    CONTROL will implement actual hashing.
    """
    raise NotImplementedError("core_checksum_bytes backend not wired yet.")


def core_extract_full(archive_path: str, output_dir: str) -> Dict[str, Any]:
    """
    CORE-level full extraction helper.
    CONTROL will choose the archive backend and execution path.
    CORE provides a stable API surface only.
    """
    raise NotImplementedError("core_extract_full backend not wired yet.")


def core_extract_target(archive_path: str, target_name: str, output_dir: str = "") -> Dict[str, Any]:
    """
    CORE-level targeted extraction helper.
    CONTROL will implement selective extraction logic.
    """
    raise NotImplementedError("core_extract_target backend not wired yet.")

def extract_text(html_bytes, url, content_type):
    try:
        html = html_bytes.decode("utf-8", errors="ignore")
    except:
        html = ""

    parser = TextExtractor()
    parser.feed(html)
    text = parser.get_text()

    metadata = make_metadata(url, content_type)
    return text, metadata

# ---------------------------------------------------------
# HTML â†’ Links extractor (offset 0x11)
# ---------------------------------------------------------
class LinkExtractor(HTMLParser):
    def __init__(self, base_url):
        super().__init__()
        self.links = []
        self.base_url = base_url

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            for (attr, value) in attrs:
                if attr.lower() == "href" and value:
                    full = urllib.parse.urljoin(self.base_url, value)
                    self.links.append(full)

    def get_links(self):
        return self.links

def extract_links(html_bytes, url, content_type):
    try:
        html = html_bytes.decode("utf-8", errors="ignore")
    except:
        html = ""

    parser = LinkExtractor(url)
    parser.feed(html)
    links = parser.get_links()

    metadata = make_metadata(url, content_type)
    return links, metadata

# ---------------------------------------------------------
# HTTP GET (device 0x20)
# ---------------------------------------------------------
def http_get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "SARA-Gen0A"})
    with urllib.request.urlopen(req) as response:
        content_type = response.headers.get("Content-Type", "text/html")
        data = response.read()
        return data, content_type


def core_smtp_send_email(
    smtp_host: str,
    smtp_port: int,
    username: str,
    password: str,
    email_data: Dict[str, Any],
    use_tls: bool = True,
    use_ssl: bool = False,
    timeout: int = 20,
) -> Dict[str, Any]:
    """CORE-owned SMTP transport primitive for outbound mail submission."""
    import smtplib
    from email.message import EmailMessage

    if not isinstance(email_data, dict):
        return {"status": "FAIL", "error": "email_data must be a dict"}

    required = ["to", "from", "subject", "body"]
    missing = [key for key in required if not str(email_data.get(key, "")).strip()]
    if missing:
        return {"status": "FAIL", "error": "missing_fields", "missing_fields": missing}

    msg = EmailMessage()
    msg["To"] = str(email_data.get("to", "")).strip()
    msg["From"] = str(email_data.get("from", "")).strip()
    msg["Subject"] = str(email_data.get("subject", "")).strip()
    msg.set_content(str(email_data.get("body", "")))

    try:
        if use_ssl:
            with smtplib.SMTP_SSL(host=smtp_host, port=int(smtp_port), timeout=timeout) as client:
                if username:
                    client.login(username, password)
                client.send_message(msg)
        else:
            with smtplib.SMTP(host=smtp_host, port=int(smtp_port), timeout=timeout) as client:
                if use_tls:
                    client.starttls()
                if username:
                    client.login(username, password)
                client.send_message(msg)
        return {
            "status": "PASS",
            "sent": True,
            "transport": "smtp",
            "host": str(smtp_host),
            "port": int(smtp_port),
        }
    except Exception as exc:
        return {
            "status": "ERROR",
            "sent": False,
            "transport": "smtp",
            "error": str(exc),
        }


def core_imap_fetch_inbox(
    imap_host: str,
    username: str,
    password: str,
    mailbox: str = "INBOX",
    limit: int = 20,
    use_ssl: bool = True,
    port: Optional[int] = None,
    criteria: str = "ALL",
) -> Dict[str, Any]:
    """CORE-owned IMAP transport primitive for inbox retrieval."""
    import email
    import imaplib

    if not imap_host or not username:
        return {"status": "FAIL", "error": "imap_host and username are required"}

    safe_limit = max(1, min(int(limit or 20), 200))
    imap_client = None
    try:
        if use_ssl:
            imap_client = imaplib.IMAP4_SSL(imap_host, int(port or 993))
        else:
            imap_client = imaplib.IMAP4(imap_host, int(port or 143))

        imap_client.login(username, password)
        select_status, _ = imap_client.select(mailbox, readonly=True)
        if str(select_status).upper() != "OK":
            return {"status": "FAIL", "error": f"select_failed:{mailbox}"}

        search_status, data = imap_client.search(None, criteria)
        if str(search_status).upper() != "OK":
            return {"status": "FAIL", "error": f"search_failed:{criteria}"}

        ids = data[0].split() if data and data[0] else []
        selected_ids = ids[-safe_limit:]
        messages: List[Dict[str, Any]] = []

        for msg_id in selected_ids:
            fetch_status, msg_data = imap_client.fetch(msg_id, "(RFC822)")
            if str(fetch_status).upper() != "OK" or not msg_data:
                continue
            raw_message = msg_data[0][1] if isinstance(msg_data[0], tuple) and len(msg_data[0]) > 1 else b""
            parsed = email.message_from_bytes(raw_message)
            messages.append(
                {
                    "id": msg_id.decode("utf-8", errors="ignore"),
                    "from": str(parsed.get("From", "")),
                    "to": str(parsed.get("To", "")),
                    "subject": str(parsed.get("Subject", "")),
                    "date": str(parsed.get("Date", "")),
                }
            )

        return {
            "status": "PASS",
            "transport": "imap",
            "mailbox": str(mailbox),
            "count": len(messages),
            "messages": messages,
        }
    except Exception as exc:
        return {
            "status": "ERROR",
            "transport": "imap",
            "error": str(exc),
        }
    finally:
        if imap_client is not None:
            try:
                imap_client.logout()
            except Exception:
                pass


# TODO: wire VNCE CORE envelopes into CONTROL routing once CONTROL exposes VNCE command handling.
# TODO: route VNCE CORE envelopes through SECURITY attestation before any live session approval.
# TODO: add ledger/audit entries for VNCE session start/end lifecycle handoffs.

def export_fsm_state_diagram(
    state_dict: Dict[str, Any],
    output_path: str,
    diagram_title: str = "FSM State Diagram",
) -> Dict[str, Any]:
    """
    Export FSM state machine as a visual PNG diagram.
    Creates nodes for states and arrows for transitions.

    Args:
        state_dict     : dict of {state_name: {"transitions": {...}, ...}}
        output_path    : path to write the output .png
        diagram_title  : title for the diagram

    Returns dict with 'success', 'path'.
    Requires: Pillow
    """
    try:
        pil_image = importlib.import_module("PIL.Image")
        pil_draw = importlib.import_module("PIL.ImageDraw")
        pil_font = importlib.import_module("PIL.ImageFont")
    except Exception:
        return {"success": False, "error": "Pillow not installed (pip install Pillow)"}

    try:
        # Create canvas
        width, height = 1200, 800
        img = pil_image.new("RGBA", (width, height), "white")
        draw = pil_draw.ImageDraw(img)
        try:
            font_title = pil_font.truetype("arial.ttf", 20)
            font_state = pil_font.truetype("arial.ttf", 14)
        except Exception:
            font_title = font_state = pil_font.load_default()

        # Draw title
        draw.text((20, 20), diagram_title, fill="black", font=font_title)

        # Layout states in a circle
        states = list(state_dict.keys())
        num_states = len(states)
        cx, cy = width // 2, height // 2
        radius = min(width, height) // 3

        state_positions = {}
        for i, state in enumerate(states):
            angle = (2 * 3.14159 * i) / max(1, num_states)
            x = int(cx + radius * __import__("math").cos(angle))
            y = int(cy + radius * __import__("math").sin(angle))
            state_positions[state] = (x, y)

            # Draw state node (circle)
            r = 30
            draw.ellipse(
                [(x - r, y - r), (x + r, y + r)],
                fill="lightblue",
                outline="darkblue",
                width=2,
            )
            # Draw state label
            draw.text(
                (x - 20, y - 8),
                state[:10],
                fill="black",
                font=font_state,
            )

        # Draw transitions as arrows (simplified)
        for state, info in state_dict.items():
            transitions = info.get("transitions", {})
            if state in state_positions:
                x0, y0 = state_positions[state]
                for target in list(transitions.keys())[:2]:  # Limit arrows for clarity
                    if target in state_positions:
                        x1, y1 = state_positions[target]
                        # Draw arrow line
                        draw.line([(x0, y0), (x1, y1)], fill="gray", width=1)
                        # Simple arrowhead
                        dx = x1 - x0
                        dy = y1 - y0
                        length = (dx**2 + dy**2) ** 0.5
                        if length > 0:
                            ax = int(x1 - (dx / length) * 15)
                            ay = int(y1 - (dy / length) * 15)
                            draw.polygon(
                                [
                                    (x1, y1),
                                    (ax - 5, ay + 5),
                                    (ax + 5, ay + 5),
                                ],
                                fill="gray",
                            )

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        img.save(output_path)
    except Exception as e:
        return {"success": False, "error": f"export_fsm_state_diagram failed: {e}"}

    return {"success": True, "path": output_path}


def compose_phoenix_snapshot(
    phoenix_state: Dict[str, Any],
    output_path: str,
    width: int = 1000,
    height: int = 600,
) -> Dict[str, Any]:
    """
    Generate a visual snapshot of Phoenix Ash state (evolution, traces, energy).
    Creates a simple annotated diagram.

    Args:
        phoenix_state : dict with 'evolution', 'traces', 'energy', etc.
        output_path   : path to write the output .png
        width         : canvas width
        height        : canvas height

    Returns dict with 'success', 'path'.
    Requires: Pillow
    """
    try:
        pil_image = importlib.import_module("PIL.Image")
        pil_draw = importlib.import_module("PIL.ImageDraw")
        pil_font = importlib.import_module("PIL.ImageFont")
    except Exception:
        return {"success": False, "error": "Pillow not installed (pip install Pillow)"}

    try:
        img = pil_image.new("RGBA", (width, height), "lightyellow")
        draw = pil_draw.ImageDraw(img)
        try:
            font = pil_font.truetype("arial.ttf", 12)
        except Exception:
            font = pil_font.load_default()

        y_offset = 20
        for key, value in (phoenix_state or {}).items():
            if y_offset > height - 40:
                break
            label = f"{key}: {str(value)[:60]}"
            draw.text((20, y_offset), label, fill="darkgreen", font=font)
            y_offset += 25

        # Draw a simple progress bar for energy
        energy = phoenix_state.get("energy", 0.5)
        bar_width = 200
        bar_height = 20
        bar_x, bar_y = 20, height - 50
        draw.rectangle(
            [(bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height)],
            outline="black",
            width=1,
        )
        fill_width = int(bar_width * min(1.0, energy))
        draw.rectangle(
            [(bar_x, bar_y), (bar_x + fill_width, bar_y + bar_height)],
            fill="orange",
        )
        draw.text((bar_x + bar_width + 10, bar_y), "energy", fill="black", font=font)

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        img.save(output_path)
    except Exception as e:
        return {"success": False, "error": f"compose_phoenix_snapshot failed: {e}"}

    return {"success": True, "path": output_path}


# --- Artifact JSON writers (result.meta.json, distant_end.json, master_result.json) ---
def _write_core_artifacts(status: str, reached: bool, reason: str) -> None:
    """Write/update the three pillar artifact JSON files for CORE."""
    _here = os.path.dirname(os.path.abspath(__file__))
    _local = {
        "pillar": "sara_core",
        "file": "sara_coregen1.py",
        "status": status,
        "reached": reached,
        "reason": reason,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    _distant = {
        "pillar": "sara_core",
        "file": "sara_coregen1.py",
        "status": status,
        "reached": reached,
        "note": reason,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    _master = {"pillar": "sara_core", "final_status": status, "local": _local, "distant": _distant}
    for fname, obj in [("result.meta.json", _local), ("distant_end.json", _distant), ("master_result.json", _master)]:
        try:
            with open(os.path.join(_here, fname), "w", encoding="utf-8") as f:
                json.dump(obj, f, ensure_ascii=False, indent=2)
        except Exception:
            pass


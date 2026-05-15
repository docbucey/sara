"""CORE Media: timeline editing, render jobs, media sequence import/export."""
import os
import json
from typing import Any, Dict, List, Optional
from datetime import datetime


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


def validate_shunt_header(payload: dict) -> bool:
    """
    Enforces shunt header contract on inbound/outbound actions.
    """
    required_fields = ["shunt_id", "source_pillar", "target_pillar", "timestamp", "intent", "payload", "context_tags", "requires_response"]
    return all(field in payload for field in required_fields)

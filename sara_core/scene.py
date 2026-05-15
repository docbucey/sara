"""CORE Scene: 3D asset management, scene state, import/export/conversion."""
import os
import json
from typing import Any, Dict, List, Optional
from datetime import datetime


def validate_shunt_header(payload: dict) -> bool:
    """
    Enforces shunt header contract on inbound/outbound actions.
    """
    required_fields = ["shunt_id", "source_pillar", "target_pillar", "timestamp", "intent", "payload", "context_tags", "requires_response"]
    return all(field in payload for field in required_fields)


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

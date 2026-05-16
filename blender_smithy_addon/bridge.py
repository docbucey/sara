"""
bridge.py — Smithy ↔ SARA CONTROL Bridge (Blender)
Sends BuceyShunt envelopes to sara_control_http.py running on localhost.
Uses only Python stdlib (urllib) — no external dependencies.

SARA CONTROL must be running before use:
    python sara_control/sara_control_http.py
    Default: http://127.0.0.1:5050
"""

import json
import uuid
import threading
import urllib.request
import urllib.error
from datetime import datetime, timezone

SARA_HOST = "127.0.0.1"
SARA_PORT = 5050
SARA_SHUNT_URL  = f"http://{SARA_HOST}:{SARA_PORT}/shunt"
SARA_HEALTH_URL = f"http://{SARA_HOST}:{SARA_PORT}/health"
REQUEST_TIMEOUT = 8.0

# Thread-safe connection state
_sara_online = False
_sara_lock = threading.Lock()


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _make_id() -> str:
    return str(uuid.uuid4())


def _build_envelope(intent: str, payload: dict) -> dict:
    return {
        "shunt_id":         _make_id(),
        "source_pillar":    "SMITHY_BLENDER",
        "target_pillar":    "CONTROL",
        "timestamp":        _iso_now(),
        "intent":           intent,
        "payload":          payload,
        "context_tags":     ["smithy", "blender", intent],
        "requires_response": True,
    }


def _post(url: str, data: dict, timeout: float = REQUEST_TIMEOUT) -> dict:
    """Synchronous POST. Returns parsed JSON dict or raises."""
    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


# ---------------------------------------------------------------------------
# Public API — async (non-blocking, uses a daemon thread)
# ---------------------------------------------------------------------------

def dispatch(intent: str, payload: dict, callback=None) -> str:
    """
    Send a BuceyShunt envelope to SARA CONTROL asynchronously.

    intent:   plain action name, e.g. "implement_logic", "audit_file"
    payload:  dict of context data
    callback: optional callable(task_id, state, result) — called on the
              threading thread (use bpy.app.timers if you need to touch Blender data)

    Returns task_id immediately.
    """
    task_id = _make_id()
    envelope = _build_envelope(intent, payload)
    envelope["shunt_id"] = task_id  # use task_id as shunt_id for easy correlation

    def _run():
        global _sara_online
        try:
            result = _post(SARA_SHUNT_URL, envelope)
            with _sara_lock:
                _sara_online = True
            state = _map_state(result)
            print(f"[SaraBridge] task={task_id} state={state}")
            if callback:
                callback(task_id, state, result)
        except (urllib.error.URLError, OSError) as e:
            with _sara_lock:
                _sara_online = False
            print(f"[SaraBridge] SARA unreachable: {e}")
            if callback:
                callback(task_id, "error", {"success": False, "error": str(e)})
        except Exception as e:
            print(f"[SaraBridge] Unexpected error: {e}")
            if callback:
                callback(task_id, "error", {"success": False, "error": str(e)})

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return task_id


def dispatch_ai_request(file_path: str, task: str, briefing: dict = None, callback=None) -> str:
    """
    Convenience wrapper matching ai_connector usage.
    Bundles file path + task + optional briefing into a single payload.
    """
    payload = dict(briefing or {})
    payload["file"] = file_path
    payload["task"] = task
    return dispatch("implement_logic", payload, callback)


def check_health(callback=None) -> None:
    """
    Non-blocking health check against SARA CONTROL.
    callback: optional callable(online: bool, info: dict)
    """
    def _run():
        global _sara_online
        try:
            req = urllib.request.Request(SARA_HEALTH_URL, method="GET")
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                info = json.loads(resp.read().decode("utf-8"))
            online = info.get("status") == "ok"
        except Exception:
            online = False
            info = {}
        with _sara_lock:
            _sara_online = online
        if online:
            print("[SaraBridge] SARA CONTROL is online.")
        else:
            print("[SaraBridge] SARA CONTROL not reachable. Start sara_control_http.py.")
        if callback:
            callback(online, info)

    threading.Thread(target=_run, daemon=True).start()


def is_sara_online() -> bool:
    with _sara_lock:
        return _sara_online


# ---------------------------------------------------------------------------
# State mapping
# ---------------------------------------------------------------------------

def _map_state(parsed: dict) -> str:
    inner = parsed.get("result", parsed)
    status = str(inner.get("status", "")).lower()
    if status in ("allow", "deny", "constrain", "schema_fail"):
        return status
    if parsed.get("success") is True:
        return "allow"
    if parsed.get("success") is False:
        err = str(parsed.get("error", "")).lower()
        if "schema" in err or "invalid" in err:
            return "schema_fail"
        if "deny" in err or "reject" in err or "unauthorized" in err:
            return "deny"
        return "error"
    return "error"


# ---------------------------------------------------------------------------
# Legacy command handler (kept for backward compat with existing operators)
# ---------------------------------------------------------------------------

def smithy_handle_command(cmd: str):
    """
    Route simple string commands to SARA CONTROL.
    Kept so existing SMITHY_OT_run_command operators still work.
    """
    print(f"[SaraBridge] Received command: {cmd}")
    dispatch("blender_command", {"command": cmd})


# ---------------------------------------------------------------------------
# Asset pipeline — FBX/3D → render → PNG → SARA assets/png/
# ---------------------------------------------------------------------------

def resolve_sara_root() -> str:
    """Locate the SARA repo root. Reads SARA_ROOT env var or falls back to default."""
    import os
    return os.environ.get(
        "SARA_ROOT",
        os.path.join(os.path.expanduser("~"), "Documents", "coding projects", "SARA"),
    )


def png_output_path(asset_id: str) -> str:
    """Full path to the rendered PNG for a given asset ID (no extension needed)."""
    import os
    return os.path.join(resolve_sara_root(), "assets", "png", f"{asset_id}.png")


def update_asset_meta(asset_id: str, width: int = 1024, height: int = 768) -> None:
    """
    Mark an asset in assets_meta.json as blender_render and update its dimensions.
    Removes the procedural_bootstrap tag. Creates a new catalog entry if not found.
    """
    import os, json
    meta_path = os.path.join(resolve_sara_root(), "assets", "meta", "assets_meta.json")
    if not os.path.exists(meta_path):
        print(f"[SaraBridge] assets_meta.json not found at {meta_path}")
        return
    try:
        with open(meta_path, "r", encoding="utf-8") as f:
            doc = json.load(f)
        assets = doc.get("assets", [])
        found = False
        for entry in assets:
            if entry.get("id") == asset_id:
                tags = entry.get("style_tags", [])
                if "procedural_bootstrap" in tags:
                    tags.remove("procedural_bootstrap")
                if "blender_render" not in tags:
                    tags.append("blender_render")
                entry["style_tags"] = tags
                entry["pixel_width"] = width
                entry["pixel_height"] = height
                found = True
                break
        if not found:
            assets.append({
                "id": asset_id,
                "file": f"assets/png/{asset_id}.png",
                "pixel_width": width,
                "pixel_height": height,
                "aspect": "4:3",
                "style_tags": ["blender_render"],
                "logical_regions": {
                    "safe_rect": {"x0": 0.5, "y0": 0.5, "x1": 9.5, "y1": 9.0},
                    "slice_caps": {"left": 0.9, "right": 0.9, "top": 0.9, "bottom": 0.9},
                    "hit_boxes": [],
                },
                "keys_drawn_in_art": False,
                "paint_brief": f"Blender render: {asset_id}",
            })
            doc["assets"] = assets
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=2)
        print(f"[SaraBridge] Meta updated: {asset_id}")
    except Exception as e:
        print(f"[SaraBridge] meta update failed: {e}")


# ---------------------------------------------------------------------------
# XAML export — geometry → WPF DrawingBrush code (no PNG, no binary assets)
# ---------------------------------------------------------------------------

def xaml_output_path(asset_id: str) -> str:
    """Full path to the XAML file for a given asset ID."""
    import os
    return os.path.join(resolve_sara_root(), "assets", "xaml", f"{asset_id}.xaml")


def update_asset_meta_xaml(asset_id: str, xaml_key: str) -> None:
    """
    Record the XAML resource key in assets_meta.json.
    Adds 'blender_export' style tag. Removes 'procedural_bootstrap'.
    The C# app checks for this key first; falls back to PNG if absent.
    """
    import os, json
    meta_path = os.path.join(resolve_sara_root(), "assets", "meta", "assets_meta.json")
    if not os.path.exists(meta_path):
        return
    try:
        with open(meta_path, "r", encoding="utf-8") as f:
            doc = json.load(f)
        assets = doc.get("assets", [])
        found = False
        for entry in assets:
            if entry.get("id") == asset_id:
                tags = entry.get("style_tags", [])
                for remove in ("procedural_bootstrap",):
                    if remove in tags:
                        tags.remove(remove)
                if "blender_export" not in tags:
                    tags.append("blender_export")
                entry["style_tags"] = tags
                entry["procedural_xaml_ref"] = xaml_key
                found = True
                break
        if not found:
            assets.append({
                "id": asset_id,
                "file": f"assets/png/{asset_id}.png",
                "aspect": "4:3",
                "style_tags": ["blender_export"],
                "procedural_xaml_ref": xaml_key,
                "logical_regions": {
                    "safe_rect": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
                    "slice_caps": {"left": 0.0, "right": 0.0, "top": 0.0, "bottom": 0.0},
                    "hit_boxes": [],
                },
                "keys_drawn_in_art": False,
                "paint_brief": f"Blender XAML export: {asset_id}",
            })
            doc["assets"] = assets
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=2)
        print(f"[SaraBridge] XAML meta updated: {asset_id} → {xaml_key}")
    except Exception as e:
        print(f"[SaraBridge] XAML meta update failed: {e}")


def _rgba_to_wpf_hex(rgba) -> str:
    """Convert Blender float RGBA (0-1 each) to WPF #AARRGGBB or #RRGGBB hex."""
    r = int(max(0.0, min(1.0, rgba[0])) * 255)
    g = int(max(0.0, min(1.0, rgba[1])) * 255)
    b = int(max(0.0, min(1.0, rgba[2])) * 255)
    a = int(max(0.0, min(1.0, rgba[3])) * 255) if len(rgba) > 3 else 255
    if a < 255:
        return f"#{a:02X}{r:02X}{g:02X}{b:02X}"
    return f"#{r:02X}{g:02X}{b:02X}"


def format_drawing_brush(asset_id: str, elements: list) -> str:
    """
    Format a complete WPF ResourceDictionary XAML string from a list of element dicts.

    Each element dict:
      {
        "color": "#RRGGBB",   # WPF hex color
        "x": 0.0,             # normalized canvas position (0-1)
        "y": 0.0,
        "w": 1.0,
        "h": 1.0,
        "rx": 0.0,            # optional corner radius X (from sara_rx custom prop)
        "ry": 0.0,            # optional corner radius Y
        "label": "obj_name",  # optional — written as XML comment for readability
      }

    Output is a complete ResourceDictionary — merge directly into a WPF project:
      <ResourceDictionary.MergedDictionaries>
          <ResourceDictionary Source="assets/xaml/{asset_id}.xaml"/>
      </ResourceDictionary.MergedDictionaries>
    """
    drawings = []
    for el in elements:
        color = el.get("color", "#CCCCCC")
        x = round(el.get("x", 0.0), 5)
        y = round(el.get("y", 0.0), 5)
        w = round(max(el.get("w", 0.0), 0.001), 5)
        h = round(max(el.get("h", 0.0), 0.001), 5)
        rx = round(el.get("rx", 0.0), 5)
        ry = round(el.get("ry", rx), 5)
        label = el.get("label", "")
        comment = f"<!-- {label} -->\n      " if label else ""
        if rx > 0 or ry > 0:
            geom = (
                f'<RectangleGeometry Rect="{x},{y},{w},{h}" '
                f'RadiusX="{rx}" RadiusY="{ry}"/>'
            )
        else:
            geom = f'<RectangleGeometry Rect="{x},{y},{w},{h}"/>'
        drawings.append(
            f"      {comment}"
            f'<GeometryDrawing Brush="{color}">\n'
            f"        <GeometryDrawing.Geometry>\n"
            f"          {geom}\n"
            f"        </GeometryDrawing.Geometry>\n"
            f"      </GeometryDrawing>"
        )

    body = "\n".join(drawings)
    return (
        '<!-- SARA procedural asset — generated by Smithy Blender export. Do not hand-edit. -->\n'
        '<ResourceDictionary\n'
        '    xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"\n'
        '    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">\n\n'
        f'  <DrawingBrush x:Key="{asset_id}"\n'
        '                Stretch="Fill" TileMode="None"\n'
        '                ViewboxUnits="Absolute" Viewbox="0,0,1,1">\n'
        '    <DrawingBrush.Drawing>\n'
        '      <DrawingGroup>\n'
        f'{body}\n'
        '      </DrawingGroup>\n'
        '    </DrawingBrush.Drawing>\n'
        '  </DrawingBrush>\n\n'
        '</ResourceDictionary>\n'
    )


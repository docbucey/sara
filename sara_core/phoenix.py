"""CORE Phoenix: snapshot/restore, location files, malware hooks, location shunts."""
import os
import json
import zlib
import base64
import threading
import importlib
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone


# =========================================================
# Kingdome Phoenix Protocol Integration (Machine Side)
# All actions must be routed through control for enforcement/execution.
# =========================================================

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

"""
SARA Control — Module loaders for CORE, MAMA, SECURITY, SDK, and mechanic adapter.
Extracted from sara_controlgen1.py.

Mechanic adapter load is optional: external desktop client stack; not shipped with SARA.
"""
import os
import importlib
import importlib.util


def _load_core_module():
    _here = os.path.dirname(os.path.abspath(__file__))
    _path = os.path.join(_here, "..", "sara_core", "sara_coregen1.py")
    if not os.path.exists(_path):
        return None
    _spec = importlib.util.spec_from_file_location("sara_coregen1", _path)
    if _spec is None or _spec.loader is None:
        return None
    _mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    return _mod


def _load_mama_module():
    _here = os.path.dirname(os.path.abspath(__file__))
    _path = os.path.join(_here, "..", "sara_mama", "sara_mamagen1.py")
    if not os.path.exists(_path):
        return None
    _spec = importlib.util.spec_from_file_location("sara_mamagen1", _path)
    if _spec is None or _spec.loader is None:
        return None
    _mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    return _mod


def _load_gen1_security():
    _here = os.path.dirname(os.path.abspath(__file__))
    _candidates = [
        ("sara_securitygen1", os.path.join(_here, "..", "sara_security", "sara_securitygen1.py")),
        ("sara_securitygn1", os.path.join(_here, "..", "sara_security", "sara_securitygn1.py")),
    ]
    for _module_name, _path in _candidates:
        if not os.path.exists(_path):
            continue
        _spec = importlib.util.spec_from_file_location(_module_name, _path)
        if _spec is None or _spec.loader is None:
            continue
        _mod = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(_mod)
        return _mod
    raise FileNotFoundError("Could not locate Gen1 SECURITY module. Checked sara_securitygen1.py and sara_securitygn1.py")


def _load_sdk_gen1_module_con():
    sdk_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sara_sdk", "Sara_sdk.gen1.py")
    if not os.path.exists(sdk_path):
        return None
    sdk_spec = importlib.util.spec_from_file_location("sara_sdk_gen1_runtime", sdk_path)
    if sdk_spec is None or sdk_spec.loader is None:
        return None
    sdk_mod = importlib.util.module_from_spec(sdk_spec)
    sdk_spec.loader.exec_module(sdk_mod)
    return sdk_mod


def _load_mechanic_adapter_contract():
    # External desktop client (Project Mechanic); not shipped with SARA — NBS contract only.
    try:
        from sara_control.loader_con import _load_core_module
        _core = _load_core_module()
        if _core is None:
            raise ImportError("Core not loaded")
        NBS_BASE_DIR = _core.NBS_BASE_DIR
        SYSTEM_CORE_PROJECT_NAME = _core.SYSTEM_CORE_PROJECT_NAME
    except Exception:
        NBS_BASE_DIR = os.path.join(os.path.expanduser("~"), "sara_nbs")
        SYSTEM_CORE_PROJECT_NAME = "sara_core_project"

    _path = os.path.join(
        NBS_BASE_DIR,
        SYSTEM_CORE_PROJECT_NAME,
        "adapters",
        "mechanic_adapter_contract.py",
    )
    if not os.path.exists(_path):
        return None
    _spec = importlib.util.spec_from_file_location("mechanic_adapter_contract", _path)
    if _spec is None or _spec.loader is None:
        return None
    _mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    return _mod


# The try/except block that loads _core and imports from it
try:
    _core = _load_core_module()
    if _core is None:
        raise ImportError("Core module file not found")
    create_nbs_file = _core.create_nbs_file
    NBS_BASE_DIR = _core.NBS_BASE_DIR
    SYSTEM_CORE_PROJECT_NAME = _core.SYSTEM_CORE_PROJECT_NAME
    _to_proto_lingua = _core._to_proto_lingua
    validate_resonance = _core.validate_resonance
except Exception as _core_load_err:
    _core = None
    def create_nbs_file(project_name, relative_path, content, meta=None):
        return {"success": False, "error": "Core not loaded"}
    NBS_BASE_DIR = os.path.join(os.path.expanduser("~"), "sara_nbs")
    SYSTEM_CORE_PROJECT_NAME = "sara_core_project"
    def _to_proto_lingua(obj, **kwargs): return obj
    def validate_resonance(obj): return True, "OK"

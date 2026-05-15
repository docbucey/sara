# shunt header: sara_control_core_stub
# Purpose: harness prereq marker + import forwarder for sara_control pillar.
# The real Gen1 core lives at ../sara_core/sara_coregn1.py
import importlib.util, os as _os

_path = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "sara_core", "sara_coregn1.py")
_spec = importlib.util.spec_from_file_location("sara_coregn1", _path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

from importlib import import_module as _im
import sys as _sys
_sys.modules.setdefault("sara_coregn1", _mod)

# Re-export everything from real core
NBS_BASE_DIR = _mod.NBS_BASE_DIR
SYSTEM_CORE_PROJECT_NAME = _mod.SYSTEM_CORE_PROJECT_NAME
INTERNAL_FILE_VERSION = _mod.INTERNAL_FILE_VERSION
create_nbs_file = _mod.create_nbs_file
create_nbs_reference = _mod.create_nbs_reference
in_out_nbs_file = _mod.in_out_nbs_file
create_characterbase_nbs_profile = _mod.create_characterbase_nbs_profile
create_nbs_project_profile = _mod.create_nbs_project_profile
update_nbs_project_profile = _mod.update_nbs_project_profile
validate_resonance = _mod.validate_resonance
append_event = _mod.append_event
_to_proto_lingua = _mod._to_proto_lingua

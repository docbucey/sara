"""
Shared constants and type definitions for the SARA system.
"""

KNOWN_PILLARS = {"CONTROL", "CORE", "SECURITY", "MAMA", "SDK"}

# Pillar naming conventions (from architecture log):
# Functions: (snake)_suffix where suffix = pillar abbreviation
#   CORE: no suffix or _core
#   CONTROL: _con
#   SECURITY: _sec
#   MAMA: _mama
#   SDK: _sdk

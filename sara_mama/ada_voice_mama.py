"""MAMA — load ADA voice I-O profile from SettingsProtocol for UX adaptation."""

from typing import Any, Dict


def get_effective_ada_voice_io() -> Dict[str, Any]:
    try:
        from sara_core.ada_voice_profile import merge_with_defaults
    except ImportError:
        return {}

    try:
        from .settings_protocol import SettingsProtocol

        sp = SettingsProtocol()
        raw = sp.get("ada_voice_profile")
        if isinstance(raw, dict):
            return merge_with_defaults(raw)
        return merge_with_defaults({})
    except Exception:
        return merge_with_defaults({})


def apply_voice_io_to_ux(ux_profile: Dict[str, Any], voice_io: Dict[str, Any]) -> Dict[str, Any]:
    try:
        from sara_core.ada_voice_profile import merge_voice_into_ux_profile

        return merge_voice_into_ux_profile(ux_profile, voice_io)
    except Exception:
        return dict(ux_profile)

"""
CORE — ADA / blind-access voice I-O profile (spec-aligned defaults + presets).

Aligned with SPEC_SHEET_GEN0_CSHARP_EXTENDED.md Phase 1 matrix:
- voice + read-aloud available, never sole path (keyboard/pointer fallbacks)
- mic / trust-sensitive capture remains SECURITY-gated in product policy
- deterministic STT modes (PTT until send, etc.) for motor + blind workflows

Front-ends (C#, Godot, web) read merged profile from MAMA `adapt_amip_ux_mama`
and/or CONTROL `ada_voice_profile_get`.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Optional

# STT capture semantics (front-end implements; profile is contract only)
STT_MODES = (
    "ptt_hold_until_send",  # record while held; assemble; send via explicit Send (recommended)
    "ptt_short",            # legacy short capture
    "disabled",
)

DEFAULT_ADA_VOICE_PROFILE: Dict[str, Any] = {
    "schema_version": 1,
    "profile_label": "default",
    # Read path (TTS / screen-reader friendliness)
    "read_aloud_enabled": True,
    "read_aloud_ui_hints": True,
    "read_aloud_errors": True,
    "read_aloud_route_summaries": True,
    "tts_rate_wpm": 175,
    "tts_voice": "system_default",
    # Voice input
    "stt_enabled": True,
    "stt_mode": "ptt_hold_until_send",
    "voice_first": True,
    "active_listening_contract": "ptt_until_explicit_send",
    # Fallback order when a modality fails (UI should try next)
    "interaction_fallback_order": ["keyboard", "voice", "pointer"],
    # WCAG-oriented hints for generated chrome (Godot/C#/web)
    "screen_reader_semantic_enrichment": True,
    "live_region_verbosity": "medium",
    "do_not_encode_meaning_color_only": True,
    "reduce_motion_default": True,
    # SECURITY policy flags (honored by SECURITY + front-end; no bypass)
    "mic_requires_security_consent": True,
    "remote_input_requires_security_consent": True,
    # Plain-language recovery (paired with Phase 1 matrix)
    "plain_language_blocked_paths": True,
}

PRESET_BLIND_FULL_ACCESS: Dict[str, Any] = {
    "profile_label": "blind_full_access",
    "read_aloud_enabled": True,
    "read_aloud_ui_hints": True,
    "read_aloud_errors": True,
    "read_aloud_route_summaries": True,
    "tts_rate_wpm": 160,
    "stt_enabled": True,
    "stt_mode": "ptt_hold_until_send",
    "voice_first": True,
    "active_listening_contract": "ptt_until_explicit_send",
    "interaction_fallback_order": ["voice", "keyboard", "pointer"],
    "screen_reader_semantic_enrichment": True,
    "live_region_verbosity": "high",
    "do_not_encode_meaning_color_only": True,
    "reduce_motion_default": True,
    "mic_requires_security_consent": True,
    "remote_input_requires_security_consent": True,
    "plain_language_blocked_paths": True,
}

PRESETS: Dict[str, Dict[str, Any]] = {
    "default": {},
    "blind_full_access": PRESET_BLIND_FULL_ACCESS,
    "motor_first": {
        "profile_label": "motor_first",
        "voice_first": True,
        "stt_mode": "ptt_hold_until_send",
        "read_aloud_enabled": True,
        "interaction_fallback_order": ["voice", "keyboard", "pointer"],
        "live_region_verbosity": "high",
    },
}


def deep_merge(base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
    out = deepcopy(base)
    for k, v in (overlay or {}).items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = deepcopy(v) if isinstance(v, dict) else v
    return out


def merge_with_defaults(stored: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    merged = deepcopy(DEFAULT_ADA_VOICE_PROFILE)
    if isinstance(stored, dict):
        merged = deep_merge(merged, stored)
    if merged.get("stt_mode") not in STT_MODES:
        merged["stt_mode"] = "ptt_hold_until_send"
    fo = merged.get("interaction_fallback_order")
    if not isinstance(fo, list) or not fo:
        merged["interaction_fallback_order"] = list(DEFAULT_ADA_VOICE_PROFILE["interaction_fallback_order"])
    return merged


def apply_preset(preset_name: str, prior: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if preset_name == "factory_reset":
        return merge_with_defaults({})
    base = merge_with_defaults(prior)
    patch = PRESETS.get(preset_name)
    if not patch:
        return base
    return deep_merge(base, deepcopy(patch))


def merge_voice_into_ux_profile(ux_profile: Dict[str, Any], voice: Dict[str, Any]) -> Dict[str, Any]:
    """Augment MAMA ux_profile with voice contract; voice_first follows ADA profile if set."""
    out = dict(ux_profile)
    vf = voice.get("voice_first")
    if isinstance(vf, bool):
        out["voice_first"] = vf
    out["read_aloud_recommended"] = bool(voice.get("read_aloud_enabled", True))
    out["stt_recommended"] = bool(voice.get("stt_enabled", True))
    return out

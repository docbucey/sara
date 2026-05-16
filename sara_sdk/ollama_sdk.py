"""SDK Ollama: Ollama-specific policy helpers and defaults."""
from __future__ import annotations

import os
from typing import Dict

try:
    from sara_sdk.identity_sdk import SDK_INTERNAL_AMI_LANES
except ImportError:
    from .identity_sdk import SDK_INTERNAL_AMI_LANES


def _sdk_ollama_enabled() -> bool:
    raw = str(os.getenv("SARA_ALLOW_OLLAMA", "")).strip().lower()
    return raw in {"1", "true", "yes", "on", "enabled"}


def _sdk_ollama_policy_mode() -> str:
    raw = str(os.getenv("SARA_OLLAMA_POLICY", "")).strip().lower()
    if raw in {"full", "allow", "on", "enabled"}:
        return "full"
    if raw in {"backup", "fallback", "limited"}:
        return "backup"
    if _sdk_ollama_enabled():
        return "full"
    return "off"


def _sdk_default_ami() -> str:
    return SDK_INTERNAL_AMI_LANES.get("copilot", next(iter(SDK_INTERNAL_AMI_LANES.values()), ""))

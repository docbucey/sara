"""Common utility stubs for SARA SDK Gen1."""

from __future__ import annotations

from typing import Any, Dict


def placeholder_metadata(name: str) -> Dict[str, Any]:
    """Return simple stub metadata for future SDK components."""
    return {
        "status": "stub",
        "name": name,
        "note": "Utility behavior has not been implemented yet.",
    }

"""CORE Proto-Lingua: data normalization and resonance validation."""
from typing import Any, Dict, List, Optional, Tuple


def _classify_value_suffix(value: Any) -> str:
    """Return the Proto-Lingua suffix based on value type."""
    if isinstance(value, dict):
        return "_breed"
    if isinstance(value, list):
        return "_dog_array"
    return "_puppy"


def _to_proto_lingua(data: Any, preferred_breed: Optional[str] = None) -> Any:
    """
    Transform a Python object into a Proto-Lingua-compliant structure.
    - Adds Nexus metadata for resonance tracking.
    - Ensures all keys are suffixed based on their type (_puppy, _breed, _dog_array).

    Args:
        data (Any): The input data to transform.
        preferred_breed (Optional[str]): The top-level breed to assign (e.g., "project_sheet").

    Returns:
        Any: The transformed Proto-Lingua structure.
    """
    if isinstance(data, dict):
        out: Dict[str, Any] = {}
        if preferred_breed:
            out["__file_breed"] = preferred_breed  # Add top-level breed if provided
        for k, v in data.items():
            suffix = _classify_value_suffix(v)  # Determine the suffix based on value type
            new_key = f"{k}{suffix}"  # Append the suffix to the key
            if isinstance(v, dict):
                out[new_key] = _to_proto_lingua(v)  # Recursively transform nested dictionaries
            elif isinstance(v, list):
                out[new_key] = [_to_proto_lingua(item) if isinstance(item, dict) else item for item in v]
            else:
                out[new_key] = v  # Preserve scalar values
        # Add Nexus metadata for resonance tracking
        out["_nexus_resonance_radius_puppy"] = 0.0  # Default to perfect resonance
        out["_nexus_stability_puppy"] = "stable"  # Default to stable
        return out
    elif isinstance(data, list):
        return [_to_proto_lingua(item) if isinstance(item, dict) else item for item in data]
    return data  # Return scalar values as-is


def validate_resonance(data: Dict[str, Any], max_radius: float = 1.0) -> Tuple[bool, str]:
    """
    Validate that the data remains within the $S^*$ Resonance Sphere.

    Args:
        data (Dict[str, Any]): The data to validate.
        max_radius (float): The maximum allowable resonance radius.

    Returns:
        Tuple[bool, str]: (True, "stable") if within the resonance radius, otherwise (False, "dissonant").
    """
    # Extract the resonance radius from the data
    resonance_radius = data.get("_nexus_resonance_radius_puppy", 0.0)
    if resonance_radius <= max_radius:
        return True, "stable"  # Data is within the resonance sphere
    return False, "dissonant"  # Data exceeds the resonance sphere

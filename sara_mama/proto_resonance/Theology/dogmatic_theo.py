# Dogmatic Theology - Foundational Reasoning Module
# No imports. No external dependencies.
# Designed for SARA Gen1 resonance layer.

# Internal doctrinal principles.
# These are intentionally generic so the module can be used outside theology.
_PRINCIPLES = {
    "truth": "Truth is consistent and non-contradictory.",
    "order": "Order reflects underlying structure.",
    "purpose": "Purpose is inherent, not accidental.",
    "authority": "Established principles outweigh novel interpretations.",
    "coherence": "Interpretations must align with core axioms."
}

def _evaluate_alignment(text):
    """
    Very small deterministic alignment check.
    Looks for principle keywords and scores alignment.
    """
    if not text:
        return 0

    lowered = text.lower()
    score = 0

    for key in _PRINCIPLES:
        if key in lowered:
            score += 1

    # Normalize to a 0-1 range
    return score / len(_PRINCIPLES)


def run_approach(input_data):
    """
    Core Dogmatic Theology reasoning function.
    Applies fixed principles to the input and returns a structured evaluation.
    """
    # Convert input to string safely
    text = str(input_data)

    alignment = _evaluate_alignment(text)

    return {
        "approach": "dogmatic",
        "input": text,
        "alignment_score": alignment,
        "principles_considered": list(_PRINCIPLES.keys()),
        "interpretation": (
            "Input aligns with established principles."
            if alignment > 0.5 else
            "Input shows weak alignment with core principles."
        ),
        "notes": "Dogmatic reasoning applies fixed axioms and evaluates consistency."
    }
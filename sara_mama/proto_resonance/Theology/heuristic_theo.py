# Heuristic Theology - Foundational Reasoning Module
# Pure ASCII. No imports. Deterministic logic.
# Designed for SARA Gen1 resonance layer.

# Internal heuristic patterns.
# These are intentionally abstract so the module can be reused outside theology.
_PATTERNS = {
    "light": "Associated with clarity, insight, or understanding.",
    "path": "Associated with direction, journey, or process.",
    "seed": "Associated with growth, origin, or potential.",
    "water": "Associated with renewal, change, or adaptation.",
    "fire": "Associated with transformation, intensity, or testing."
}

def _analyze_tokens(text):
    """
    Breaks the input into simple tokens and checks for heuristic patterns.
    Returns a dictionary of matched patterns and a score.
    """
    lowered = text.lower()
    tokens = lowered.split()

    matches = []
    score = 0

    for key in _PATTERNS:
        if key in tokens:
            matches.append(key)
            score += 1

    # Normalize score to 0-1 range
    if len(_PATTERNS) > 0:
        score = score / len(_PATTERNS)

    return matches, score

def run_approach(input_data):
    """
    Core Heuristic Theology reasoning function.
    Explores meaning through pattern recognition and analogy.
    """
    text = str(input_data)

    matches, score = _analyze_tokens(text)

    interpretation = "Heuristic interpretation generated from detected patterns."
    if score == 0:
        interpretation = "No heuristic patterns detected. Interpretation is minimal."

    return {
        "approach": "heuristic",
        "input": text,
        "patterns_detected": matches,
        "pattern_score": score,
        "interpretation": interpretation,
        "notes": "Heuristic reasoning explores meaning through analogy and pattern matching."
    }
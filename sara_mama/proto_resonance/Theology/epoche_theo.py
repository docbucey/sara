# Epoche Theology - Foundational Reasoning Module
# Pure ASCII. No imports. Deterministic logic.
# Designed for SARA Gen1 resonance layer.

def _strip_assumptions(text):
    """
    Removes common qualifiers, assumptions, and interpretive language.
    Returns a simplified, neutral version of the input.
    """
    lowered = text.lower()

    # Words that imply interpretation or assumption.
    remove_words = [
        "maybe", "perhaps", "seems", "appears", "likely",
        "possibly", "probably", "i think", "i feel",
        "in my opinion", "assume", "guess", "suggests"
    ]

    cleaned = lowered
    for word in remove_words:
        cleaned = cleaned.replace(word, "")

    # Normalize spacing after removals.
    cleaned = " ".join(cleaned.split())
    return cleaned

def _observe(text):
    """
    Returns a neutral description of what is directly present in the text.
    No interpretation, no assumptions.
    """
    if text.strip() == "":
        return "No direct content present."

    # For Gen1, the observation is simply the cleaned text itself.
    return "Direct content observed: " + text

def run_approach(input_data):
    """
    Core Epoche Theology reasoning function.
    Suspends assumptions and returns a neutral observation.
    """
    text = str(input_data)

    cleaned = _strip_assumptions(text)
    observation = _observe(cleaned)

    return {
        "approach": "epoche",
        "input": text,
        "cleaned_input": cleaned,
        "observation": observation,
        "notes": "Epoche reasoning brackets assumptions and focuses on direct content only."
    }

# Phenomenological Philosophy - Skeleton
# Pure ASCII. No imports.

_INTERNAL = {
    "descriptive_keywords": ["experience", "perception", "feeling", "awareness"],
    "neutral_phrases": ["it appears that", "it seems", "one observes"]
}

def _helper(text):
    return text.lower()

def _extract_descriptions(text):
    descriptions = []
    for keyword in _INTERNAL["descriptive_keywords"]:
        if keyword in text:
            descriptions.append(keyword)
    return descriptions

def _remove_interpretive_language(text):
    for phrase in _INTERNAL["neutral_phrases"]:
        text = text.replace(phrase, "")
    return text.strip()

def run_approach(input_data):
    text = _helper(str(input_data))
    descriptions = _extract_descriptions(text)
    neutral_text = _remove_interpretive_language(text)
    
    return {
        "approach": "phenomenological",
        "input": text,
        "descriptions": descriptions,
        "neutral_text": neutral_text,
        "status": "complete"
    }4
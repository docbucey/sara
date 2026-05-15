# Semiotic Humanities - Expanded
# Pure ASCII. No imports.

_INTERNAL = {
    "signs": ["icon", "index", "symbol"],
    "codes": ["language", "gesture", "ritual"],
    "meaning_systems": ["cultural", "social", "contextual"]
}

def _helper(text):
    return text.lower()

def _detect_signs(text):
    detected_signs = []
    for sign in _INTERNAL["signs"]:
        if sign in text:
            detected_signs.append(sign)
    return detected_signs

def _detect_codes(text):
    detected_codes = []
    for code in _INTERNAL["codes"]:
        if code in text:
            detected_codes.append(code)
    return detected_codes

def _analyze_meaning_systems(text):
    systems = []
    for system in _INTERNAL["meaning_systems"]:
        if system in text:
            systems.append(system)
    return systems

def run_approach(input_data):
    text = _helper(str(input_data))
    signs = _detect_signs(text)
    codes = _detect_codes(text)
    meaning_systems = _analyze_meaning_systems(text)
    
    return {
        "approach": "semiotic",
        "input": text,
        "signs": signs,
        "codes": codes,
        "meaning_systems": meaning_systems,
        "status": "complete"
    }
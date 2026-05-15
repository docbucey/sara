# Analytic Philosophy - Skeleton
# Pure ASCII. No imports.

_INTERNAL = {
    "definitions": ["is", "means", "refers to"],
    "logical_connectives": ["and", "or", "if", "then", "not"],
    "contradictory_pairs": [("true", "false"), ("yes", "no")]
}

def _helper(text):
    return text.lower()

def _extract_definitions(text):
    definitions = []
    for keyword in _INTERNAL["definitions"]:
        if keyword in text:
            definitions.append(keyword)
    return definitions

def _detect_logical_structure(text):
    structure = []
    for connective in _INTERNAL["logical_connectives"]:
        if connective in text:
            structure.append(connective)
    return structure

def _flag_contradictions(text):
    contradictions = []
    for pair in _INTERNAL["contradictory_pairs"]:
        if pair[0] in text and pair[1] in text:
            contradictions.append(pair)
    return contradictions

def run_approach(input_data):
    text = _helper(str(input_data))
    definitions = _extract_definitions(text)
    logical_structure = _detect_logical_structure(text)
    contradictions = _flag_contradictions(text)
    
    return {
        "approach": "analytic",
        "input": text,
        "definitions": definitions,
        "logical_structure": logical_structure,
        "contradictions": contradictions,
        "status": "complete"
    }
# Pragmatic Philosophy - Skeleton
# Pure ASCII. No imports.

_INTERNAL = {
    "consequence_keywords": ["result", "effect", "outcome", "impact"],
    "usefulness_indicators": ["useful", "practical", "beneficial", "advantageous"]
}

def _helper(text):
    return text.lower()

def _scan_consequences(text):
    consequences = []
    for keyword in _INTERNAL["consequence_keywords"]:
        if keyword in text:
            consequences.append(keyword)
    return consequences

def _evaluate_usefulness(text):
    usefulness_score = 0
    for indicator in _INTERNAL["usefulness_indicators"]:
        if indicator in text:
            usefulness_score += 1
    return usefulness_score

def run_approach(input_data):
    text = _helper(str(input_data))
    consequences = _scan_consequences(text)
    usefulness_score = _evaluate_usefulness(text)
    
    return {
        "approach": "pragmatic",
        "input": text,
        "consequences": consequences,
        "usefulness_score": usefulness_score,
        "status": "complete"
    }
# Tactical Tactics - Expanded
# Pure ASCII. No imports.

_INTERNAL = {
    "action_indicators": ["move", "adjust", "respond", "execute"],
    "optimization_terms": ["maximize", "minimize", "improve", "refine"],
    "situational_keywords": ["threat", "opportunity", "risk", "advantage"]
}

def _helper(text):
    return text.lower()

def _detect_immediate_actions(text):
    actions = []
    for indicator in _INTERNAL["action_indicators"]:
        if indicator in text:
            actions.append(indicator)
    return actions

def _detect_local_optimization(text):
    optimizations = []
    for term in _INTERNAL["optimization_terms"]:
        if term in text:
            optimizations.append(term)
    return optimizations

def _detect_situational_responses(text):
    situations = []
    for keyword in _INTERNAL["situational_keywords"]:
        if keyword in text:
            situations.append(keyword)
    return situations

def run_approach(input_data):
    text = _helper(str(input_data))
    immediate_actions = _detect_immediate_actions(text)
    local_optimization = _detect_local_optimization(text)
    situational_responses = _detect_situational_responses(text)
    
    return {
        "approach": "tactical",
        "input": text,
        "immediate_actions": immediate_actions,
        "local_optimization": local_optimization,
        "situational_responses": situational_responses,
        "status": "complete"
    }
# Strategic Tactics - Expanded
# Pure ASCII. No imports.

_INTERNAL = {
    "goals": ["maximize", "minimize", "achieve", "optimize"],
    "constraints": ["limited", "restricted", "bounded", "finite"],
    "planning_indicators": ["step", "phase", "sequence", "timeline"]
}

def _helper(text):
    return text.lower()

def _identify_goals(text):
    detected_goals = []
    for goal in _INTERNAL["goals"]:
        if goal in text:
            detected_goals.append(goal)
    return detected_goals

def _identify_constraints(text):
    detected_constraints = []
    for constraint in _INTERNAL["constraints"]:
        if constraint in text:
            detected_constraints.append(constraint)
    return detected_constraints

def _analyze_planning_indicators(text):
    planning_elements = []
    for indicator in _INTERNAL["planning_indicators"]:
        if indicator in text:
            planning_elements.append(indicator)
    return planning_elements

def run_approach(input_data):
    text = _helper(str(input_data))
    goals = _identify_goals(text)
    constraints = _identify_constraints(text)
    planning_indicators = _analyze_planning_indicators(text)
    
    return {
        "approach": "strategic",
        "input": text,
        "goals": goals,
        "constraints": constraints,
        "planning_indicators": planning_indicators,
        "status": "complete"
    }
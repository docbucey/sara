# Operational Tactics - Expanded
# Pure ASCII. No imports.

_INTERNAL = {
    "sequencing_indicators": ["first", "next", "then", "finally"],
    "coordination_terms": ["synchronize", "align", "coordinate", "integrate"],
    "resource_keywords": ["allocate", "distribute", "utilize", "deploy"]
}

def _helper(text):
    return text.lower()

def _detect_sequencing(text):
    sequence_steps = []
    for indicator in _INTERNAL["sequencing_indicators"]:
        if indicator in text:
            sequence_steps.append(indicator)
    return sequence_steps

def _detect_coordination(text):
    coordination_terms = []
    for term in _INTERNAL["coordination_terms"]:
        if term in text:
            coordination_terms.append(term)
    return coordination_terms

def _detect_resource_alignment(text):
    resources = []
    for keyword in _INTERNAL["resource_keywords"]:
        if keyword in text:
            resources.append(keyword)
    return resources

def run_approach(input_data):
    text = _helper(str(input_data))
    sequencing = _detect_sequencing(text)
    coordination = _detect_coordination(text)
    resource_alignment = _detect_resource_alignment(text)
    
    return {
        "approach": "operational",
        "input": text,
        "sequencing": sequencing,
        "coordination": coordination,
        "resource_alignment": resource_alignment,
        "status": "complete"
    }
# Creative Science - Expanded
# Pure ASCII. No imports.

_INTERNAL = {
    "analogy_sources": ["nature", "technology", "art", "history"],
    "reframing_methods": ["inversion", "expansion", "simplification", "abstraction"],
    "blending_strategies": ["merge", "overlay", "hybridize", "combine"]
}

def _helper(text):
    return text.lower()

def _generate_analogy(text):
    for source in _INTERNAL["analogy_sources"]:
        if source in text:
            return {"analogy": f"Derived analogy from {source}"}
    return {"analogy": "No analogy found"}

def _reframe_problem(text):
    for method in _INTERNAL["reframing_methods"]:
        if method in text:
            return {"reframed": f"Problem reframed using {method}"}
    return {"reframed": "No reframing applied"}

def _blend_structures(text):
    for strategy in _INTERNAL["blending_strategies"]:
        if strategy in text:
            return {"blend": f"Structures blended using {strategy}"}
    return {"blend": "No blending applied"}

def _transform_concept(analogy, reframed, blend):
    return {"transformation": f"Concept transformed using {analogy['analogy']}, {reframed['reframed']}, and {blend['blend']}"}

def run_approach(input_data):
    text = _helper(str(input_data))
    analogy = _generate_analogy(text)
    reframed = _reframe_problem(text)
    blend = _blend_structures(text)
    transformation = _transform_concept(analogy, reframed, blend)
    
    return {
        "approach": "creative_science",
        "input": text,
        "analogy": analogy,
        "reframed": reframed,
        "blend": blend,
        "transformation": transformation,
        "status": "complete"
    }
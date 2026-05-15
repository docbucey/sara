# Pattern Science - Expanded
# Pure ASCII. No imports.

_INTERNAL = {
    "patterns": ["linear", "cyclical", "hierarchical", "random"],
    "scoring_criteria": ["simplicity", "fit", "predictive_power"]
}

def _helper(text):
    return text.lower()

def _extract_structure(text):
    for pattern in _INTERNAL["patterns"]:
        if pattern in text:
            return {"structure": pattern}
    return {"structure": "unknown"}

def _generate_candidates(structure):
    candidates = []
    if structure["structure"] == "linear":
        candidates = ["trend", "progression"]
    elif structure["structure"] == "cyclical":
        candidates = ["seasonal", "repetitive"]
    elif structure["structure"] == "hierarchical":
        candidates = ["tree", "nested"]
    elif structure["structure"] == "random":
        candidates = ["noise", "chaos"]
    return candidates

def _score_candidates(candidates):
    scored = []
    for candidate in candidates:
        score = len(candidate)  # Deterministic scoring based on length
        scored.append({"candidate": candidate, "score": score})
    return sorted(scored, key=lambda x: x["score"], reverse=True)

def _select_best(scored_candidates):
    if scored_candidates:
        return scored_candidates[0]
    return {"candidate": "none", "score": 0}

def run_approach(input_data):
    text = _helper(str(input_data))
    structure = _extract_structure(text)
    candidates = _generate_candidates(structure)
    scored_candidates = _score_candidates(candidates)
    best_explanation = _select_best(scored_candidates)
    
    return {
        "approach": "pattern_science",
        "input": text,
        "structure": structure,
        "candidates": candidates,
        "scored_candidates": scored_candidates,
        "best_explanation": best_explanation,
        "status": "complete"
    }
# Adaptive Tactics - Expanded
# Pure ASCII. No imports.

_INTERNAL = {
    "feedback_indicators": ["observe", "monitor", "evaluate", "assess"],
    "adjustment_terms": ["modify", "adapt", "change", "shift"],
    "resilience_keywords": ["recover", "withstand", "persist", "endure"],
    "dynamic_response_phrases": ["real-time", "on-the-fly", "immediate", "flexible"]
}

def _helper(text):
    return text.lower()

def _detect_feedback(text):
    feedback = []
    for indicator in _INTERNAL["feedback_indicators"]:
        if indicator in text:
            feedback.append(indicator)
    return feedback

def _detect_adjustments(text):
    adjustments = []
    for term in _INTERNAL["adjustment_terms"]:
        if term in text:
            adjustments.append(term)
    return adjustments

def _detect_resilience(text):
    resilience_factors = []
    for keyword in _INTERNAL["resilience_keywords"]:
        if keyword in text:
            resilience_factors.append(keyword)
    return resilience_factors

def _detect_dynamic_responses(text):
    dynamic_responses = []
    for phrase in _INTERNAL["dynamic_response_phrases"]:
        if phrase in text:
            dynamic_responses.append(phrase)
    return dynamic_responses

def run_approach(input_data):
    text = _helper(str(input_data))
    feedback = _detect_feedback(text)
    adjustments = _detect_adjustments(text)
    resilience = _detect_resilience(text)
    dynamic_responses = _detect_dynamic_responses(text)
    
    return {
        "approach": "adaptive",
        "input": text,
        "feedback": feedback,
        "adjustments": adjustments,
        "resilience": resilience,
        "dynamic_responses": dynamic_responses,
        "status": "complete"
    }
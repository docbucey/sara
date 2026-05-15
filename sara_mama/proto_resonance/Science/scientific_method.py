# Scientific Method - Expanded
# Pure ASCII. No imports.

_INTERNAL = {
    "steps": ["observe", "hypothesize", "predict", "test", "refine"]
}

def _helper(text):
    return text.lower()

def _observe(problem):
    return {"observation": f"Observed: {problem}"}

def _hypothesize(observation):
    return {"hypothesis": f"Hypothesis based on {observation['observation']}"}

def _predict(hypothesis):
    return {"prediction": f"Prediction derived from {hypothesis['hypothesis']}"}

def _test(prediction):
    return {"result": f"Test result for {prediction['prediction']}"}

def _refine(hypothesis, result):
    return {"refined_hypothesis": f"Refined {hypothesis['hypothesis']} using {result['result']}"}

def run_approach(input_data):
    text = _helper(str(input_data))
    observation = _observe(text)
    hypothesis = _hypothesize(observation)
    prediction = _predict(hypothesis)
    result = _test(prediction)
    refined_hypothesis = _refine(hypothesis, result)
    
    return {
        "approach": "method_science",
        "input": text,
        "observation": observation,
        "hypothesis": hypothesis,
        "prediction": prediction,
        "result": result,
        "refined_hypothesis": refined_hypothesis,
        "status": "complete"
    }
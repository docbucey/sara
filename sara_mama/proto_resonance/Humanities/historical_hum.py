# Historical Humanities - Expanded
# Pure ASCII. No imports.

_INTERNAL = {
    "time_indicators": ["year", "century", "era", "period"],
    "place_indicators": ["region", "country", "city", "location"],
    "event_indicators": ["war", "revolution", "treaty", "discovery"],
    "causal_phrases": ["led to", "resulted in", "caused by", "due to"]
}

def _helper(text):
    return text.lower()

def _detect_time(text):
    detected_times = []
    for time in _INTERNAL["time_indicators"]:
        if time in text:
            detected_times.append(time)
    return detected_times

def _detect_place(text):
    detected_places = []
    for place in _INTERNAL["place_indicators"]:
        if place in text:
            detected_places.append(place)
    return detected_places

def _detect_events(text):
    detected_events = []
    for event in _INTERNAL["event_indicators"]:
        if event in text:
            detected_events.append(event)
    return detected_events

def _analyze_causal_chains(text):
    causal_chains = []
    for phrase in _INTERNAL["causal_phrases"]:
        if phrase in text:
            causal_chains.append(phrase)
    return causal_chains

def run_approach(input_data):
    text = _helper(str(input_data))
    times = _detect_time(text)
    places = _detect_place(text)
    events = _detect_events(text)
    causal_chains = _analyze_causal_chains(text)
    
    return {
        "approach": "historical",
        "input": text,
        "times": times,
        "places": places,
        "events": events,
        "causal_chains": causal_chains,
        "status": "complete"
    }
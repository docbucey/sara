# Ethical Humanities - Expanded
# Pure ASCII. No imports.

_INTERNAL = {
    "themes": ["justice", "morality", "virtue", "ethics"],
    "motifs": ["sacrifice", "redemption", "conflict", "choice"],
    "symbolism": ["light", "darkness", "chains", "freedom"],
    "narrative_indicators": ["beginning", "middle", "end", "climax", "resolution"]
}

def _helper(text):
    return text.lower()

def _detect_themes(text):
    detected_themes = []
    for theme in _INTERNAL["themes"]:
        if theme in text:
            detected_themes.append(theme)
    return detected_themes

def _detect_motifs(text):
    detected_motifs = []
    for motif in _INTERNAL["motifs"]:
        if motif in text:
            detected_motifs.append(motif)
    return detected_motifs

def _detect_symbolism(text):
    detected_symbols = []
    for symbol in _INTERNAL["symbolism"]:
        if symbol in text:
            detected_symbols.append(symbol)
    return detected_symbols

def _analyze_narrative_structure(text):
    structure_elements = []
    for indicator in _INTERNAL["narrative_indicators"]:
        if indicator in text:
            structure_elements.append(indicator)
    return structure_elements

def run_approach(input_data):
    text = _helper(str(input_data))
    themes = _detect_themes(text)
    motifs = _detect_motifs(text)
    symbolism = _detect_symbolism(text)
    narrative_structure = _analyze_narrative_structure(text)
    
    return {
        "approach": "ethical",
        "input": text,
        "themes": themes,
        "motifs": motifs,
        "symbolism": symbolism,
        "narrative_structure": narrative_structure,
        "status": "complete"
    }
"""
SARA SDK — Steno Chord Engine
Ported from DisabilityMapper/Services/StenoChordEngine.cs

Latch-mode stenotype keyboard for accessibility:
  - Click/press a key → latches it (stays active)
  - Click again → unlatches
  - Fire (Enter or auto-fire timeout) → look up chord → emit text
  - ✱ alone = undo last word

Canonical steno key order (Plover-compatible English):
  # S T K P W H R  A O * E U  -F -R -P -B -L -G -T -S -D -Z
"""

import json
import threading
from typing import Callable, Dict, List, Optional, Set


KEY_ORDER = [
    "#",
    "S", "T", "K", "P", "W", "H", "R",
    "A", "O", "*", "E", "U",
    "-F", "-R", "-P", "-B", "-L", "-G", "-T", "-S", "-D", "-Z",
]

_STARTER_DICT: Dict[str, str] = {
    "-T": "the", "-F": "of", "SKP": "and", "TO": "to",
    "AEU": "a", "TPH": "in", "T": "it", "-B": "be",
    "TH": "this", "TP": "for", "R": "are", "U": "you",
    "K": "can", "HR": "will", "SR": "have", "TPR": "from",
    "HE": "he", "WE": "we", "TKO": "do", "SO": "so",
    "TPHO": "no", "WA-S": "was", "S": "is", "KPW": "but",
    "EU": "I", "SHE": "she", "TPHU": "new", "WA": "way",
    "SEU": "say", "TPHA": "any", "A": "at", "O": "or",
    "AOU": "out", "EUPL": "I'm", "TKPWOT": "got",
    "TKAOE": "day", "KPH": "come", "TPH-G": "ing",
    "-S": "s", "-D": "d", "SKP-R": "and are", "SKP-T": "and the",
    "W-": "with", "PHAE": "may", "PWAO": "by", "AUL": "all",
    "TPHEUF": "if", "TKPWAO": "go", "TKPW": "good",
    "SHROEUP": "know", "HRAOEUBG": "like", "PHAEBG": "make",
    "TEUPL": "time", "PHOPB": "one", "PHRO": "people",
    "THAEUR": "their", "TWHAOER": "there", "AOEUR": "our",
    "AEUR": "your", "HA-F": "half", "PHEU": "my",
    "PHED": "me", "HO": "how", "WHEPB": "when",
    "WOBG": "work", "TEUBG": "think", "TKPWAOEU": "guy",
    "PREUB": "pretty", "PRAOEUBGS": "price",
}


class StenoChordEngine:
    """Latch-mode steno chord accumulator with Plover dictionary lookup."""

    def __init__(self):
        self._latched: Set[str] = set()
        self._history: List[str] = []
        self._dict: Dict[str, str] = dict(_STARTER_DICT)
        self._auto_fire_ms: int = 0
        self._auto_fire_timer: Optional[threading.Timer] = None

        self.on_text_ready: Optional[Callable[[str], None]] = None
        self.on_chord_changed: Optional[Callable[[str], None]] = None

    def _build_chord_string(self) -> str:
        return "".join(k for k in KEY_ORDER if k in self._latched)

    def _notify_chord_changed(self) -> None:
        if self.on_chord_changed:
            self.on_chord_changed(self._build_chord_string())

    def _reset_auto_fire(self) -> None:
        if self._auto_fire_ms <= 0:
            return
        if self._auto_fire_timer:
            self._auto_fire_timer.cancel()
        self._auto_fire_timer = threading.Timer(
            self._auto_fire_ms / 1000.0, self.fire
        )
        self._auto_fire_timer.daemon = True
        self._auto_fire_timer.start()

    def set_auto_fire(self, ms: int) -> None:
        self._auto_fire_ms = ms
        if self._auto_fire_timer:
            self._auto_fire_timer.cancel()
            self._auto_fire_timer = None

    def toggle_key(self, key_id: str) -> None:
        key = "S" if key_id == "S2" else key_id
        if key in self._latched:
            self._latched.discard(key)
        else:
            self._latched.add(key)
        self._notify_chord_changed()
        self._reset_auto_fire()

    def is_latched(self, key_id: str) -> bool:
        return ("S" if key_id == "S2" else key_id) in self._latched

    def fire(self) -> Optional[str]:
        if not self._latched:
            return None

        if self._latched == {"*"}:
            text = self.undo()
            self._latched.clear()
            self._notify_chord_changed()
            return text

        chord = self._build_chord_string()
        self._latched.clear()
        self._notify_chord_changed()

        word = self._dict.get(chord, f"[{chord}]")
        output = word + " "
        self._history.append(output)
        if self.on_text_ready:
            self.on_text_ready(output)
        return output

    def inject_raw(self, text: str) -> None:
        self._history.append(text)
        if self.on_text_ready:
            self.on_text_ready(text)

    def undo(self) -> Optional[str]:
        if not self._history:
            return None
        last = self._history.pop()
        backspace = "\b" * len(last)
        if self.on_text_ready:
            self.on_text_ready(backspace)
        return backspace

    def clear_latch(self) -> None:
        self._latched.clear()
        self._notify_chord_changed()

    @property
    def latched_keys(self) -> Set[str]:
        return set(self._latched)

    @property
    def current_chord(self) -> str:
        return self._build_chord_string()

    def add_entry(self, chord: str, word: str) -> None:
        self._dict[chord] = word

    def load_dictionary(self, path: str) -> int:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        count = 0
        for chord, translation in data.items():
            chord = chord.strip()
            if chord:
                self._dict[chord] = str(translation)
                count += 1
        return count

    @property
    def dictionary_size(self) -> int:
        return len(self._dict)

    def lookup(self, chord: str) -> Optional[str]:
        return self._dict.get(chord)

    def to_state_dict(self) -> dict:
        return {
            "latched": sorted(self._latched),
            "chord": self._build_chord_string(),
            "history_depth": len(self._history),
            "dict_size": len(self._dict),
            "auto_fire_ms": self._auto_fire_ms,
        }

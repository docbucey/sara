"""Adaptive jargon lexicon and text quality checking for MAMA."""

import difflib
import json
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Set

try:
    import language_tool_python  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    language_tool_python = None

try:
    from spellchecker import SpellChecker  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    SpellChecker = None


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


COMMON_WORDS: Set[str] = {
    "a", "about", "after", "all", "also", "an", "and", "any", "are", "as", "at",
    "be", "because", "been", "before", "best", "both", "build", "but", "by",
    "can", "check", "code", "core", "create", "data", "do", "each", "end", "error",
    "file", "files", "for", "from", "get", "good", "grammar", "has", "have", "help",
    "if", "in", "into", "is", "it", "its", "just", "key", "learn", "like", "list",
    "make", "memory", "mode", "model", "more", "most", "name", "need", "new", "no",
    "not", "now", "of", "on", "one", "or", "other", "our", "out", "path", "profile",
    "project", "proof", "ready", "reason", "research", "result", "run", "same", "set",
    "should", "simple", "so", "some", "spell", "start", "status", "store", "system",
    "term", "terms", "text", "that", "the", "their", "them", "then", "there", "this",
    "to", "tool", "type", "up", "use", "user", "using", "valid", "value", "want", "was",
    "we", "well", "when", "with", "word", "words", "work", "workflow", "you", "your",
}


def _normalize_term(term: str) -> str:
    return re.sub(r"[^A-Za-z0-9_\-]", "", str(term or "").strip())


def _tokenize_words(text: str) -> List[str]:
    return re.findall(r"[A-Za-z][A-Za-z0-9_\-']*", text or "")


def _is_acronymish(token: str) -> bool:
    return token.isupper() and len(token) >= 2


def _is_technical_token(token: str) -> bool:
    return (
        bool(re.search(r"[_\-]", token))
        or bool(re.search(r"[A-Z].*[a-z]|[a-z].*[A-Z]", token))
        or bool(re.search(r"\d", token))
    )


class AdaptiveJargonLexicon:
    """Persistent, mode-aware jargon storage and text quality checks."""

    def __init__(self, base_dir: Optional[str] = None):
        here = os.path.dirname(__file__)
        self.base_dir = base_dir or here
        self.logs_dir = os.path.join(self.base_dir, "logs")
        os.makedirs(self.logs_dir, exist_ok=True)
        self.lexicon_path = os.path.join(self.logs_dir, "mama_jargon_lexicon.json")
        self.grammar_tool = None
        if language_tool_python is not None:
            try:
                self.grammar_tool = language_tool_python.LanguageTool("en-US")
            except Exception:
                self.grammar_tool = None

        self.spell_tool = None
        if SpellChecker is not None:
            try:
                self.spell_tool = SpellChecker()
            except Exception:
                self.spell_tool = None

        self._state = self._load_state()

    def _default_state(self) -> Dict[str, Any]:
        return {
            "version": 1,
            "created_at": _iso_now(),
            "updated_at": _iso_now(),
            "global_jargon": [],
            "modes": {
                "research": [],
                "coding": [],
                "office": [],
            },
        }

    def _load_state(self) -> Dict[str, Any]:
        if not os.path.exists(self.lexicon_path):
            state = self._default_state()
            self._save_state(state)
            return state
        try:
            with open(self.lexicon_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if not isinstance(loaded, dict):
                raise ValueError("lexicon format invalid")
            return loaded
        except Exception:
            state = self._default_state()
            self._save_state(state)
            return state

    def _save_state(self, state: Dict[str, Any]) -> None:
        state["updated_at"] = _iso_now()
        with open(self.lexicon_path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)

    def _mode_list(self, mode: str) -> List[str]:
        modes = self._state.setdefault("modes", {})
        if mode not in modes:
            modes[mode] = []
        return modes[mode]

    def teach_terms(self, terms: Iterable[str], mode: Optional[str] = None) -> Dict[str, Any]:
        clean_terms: List[str] = []
        for t in terms:
            nt = _normalize_term(t)
            if nt:
                clean_terms.append(nt)

        added_global = 0
        added_mode = 0

        global_terms = set(self._state.setdefault("global_jargon", []))
        for term in clean_terms:
            if term not in global_terms:
                global_terms.add(term)
                added_global += 1
        self._state["global_jargon"] = sorted(global_terms)

        if mode:
            mode_terms = set(self._mode_list(mode))
            for term in clean_terms:
                if term not in mode_terms:
                    mode_terms.add(term)
                    added_mode += 1
            self._state["modes"][mode] = sorted(mode_terms)

        self._save_state(self._state)
        return {
            "status": "PASS",
            "mode": mode,
            "added_global": added_global,
            "added_mode": added_mode,
            "lexicon_path": self.lexicon_path,
        }

    def get_known_terms(self, mode: Optional[str] = None) -> Set[str]:
        known = set(self._state.get("global_jargon", []))
        if mode:
            known.update(self._mode_list(mode))
        return known

    def _build_known_wordset(self, mode: str) -> Set[str]:
        known = set(COMMON_WORDS)
        jargon = self.get_known_terms(mode)
        known.update(jargon)
        known.update({w.lower() for w in jargon})
        return known

    def _rule_based_grammar(self, text: str) -> List[Dict[str, Any]]:
        issues: List[Dict[str, Any]] = []
        repeated_word_pattern = re.compile(r"\b([A-Za-z]+)\s+\1\b", re.IGNORECASE)
        for m in repeated_word_pattern.finditer(text):
            issues.append({
                "type": "grammar",
                "message": "Repeated word detected",
                "span": [m.start(), m.end()],
                "suggestion": m.group(1),
            })

        for m in re.finditer(r"\s{2,}", text):
            issues.append({
                "type": "grammar",
                "message": "Multiple spaces detected",
                "span": [m.start(), m.end()],
                "suggestion": "Use one space",
            })

        sentence_end_pattern = re.compile(r"[A-Za-z0-9\)]\n")
        for m in sentence_end_pattern.finditer(text):
            issues.append({
                "type": "grammar",
                "message": "Possible missing punctuation before line break",
                "span": [m.start(), m.end()],
                "suggestion": "Consider ending the sentence with . ? or !",
            })

        return issues

    def _grammar_check(self, text: str) -> List[Dict[str, Any]]:
        if self.grammar_tool is None:
            return self._rule_based_grammar(text)

        try:
            matches = self.grammar_tool.check(text)
            issues: List[Dict[str, Any]] = []
            for m in matches:
                issues.append({
                    "type": "grammar",
                    "message": m.message,
                    "span": [m.offset, m.offset + m.errorLength],
                    "suggestion": (m.replacements[0] if m.replacements else None),
                    "rule": m.ruleId,
                })
            return issues
        except Exception:
            return self._rule_based_grammar(text)

    def _spell_suggestions(self, token: str, known_words: Set[str]) -> List[str]:
        token_lower = token.lower()
        if self.spell_tool is not None:
            try:
                candidates = list(self.spell_tool.candidates(token_lower))[:5]
                return [c for c in candidates if c in known_words][:3] or candidates[:3]
            except Exception:
                pass

        return difflib.get_close_matches(token_lower, list(known_words), n=3, cutoff=0.82)

    def _collect_unknown_tokens(self, text: str, mode: str) -> List[Dict[str, Any]]:
        known_words = self._build_known_wordset(mode)
        known_jargon = self.get_known_terms(mode)
        unknowns: List[Dict[str, Any]] = []

        for token in _tokenize_words(text):
            norm = _normalize_term(token)
            low = norm.lower()
            if not norm or len(norm) < 3:
                continue
            if _is_acronymish(norm) or _is_technical_token(norm):
                continue
            if norm in known_jargon or low in known_words:
                continue

            suggestions = self._spell_suggestions(norm, known_words)
            unknowns.append({
                "type": "spelling",
                "token": token,
                "suggestions": suggestions,
            })

        deduped: Dict[str, Dict[str, Any]] = {}
        for entry in unknowns:
            key = str(entry.get("token", "")).lower()
            if key and key not in deduped:
                deduped[key] = entry
        return list(deduped.values())

    def check_text(self,
                   text: str,
                   mode: str = "research",
                   user_jargon: Optional[Iterable[str]] = None,
                   auto_learn: bool = False) -> Dict[str, Any]:
        if user_jargon:
            self.teach_terms(user_jargon, mode=mode)

        spelling = self._collect_unknown_tokens(text, mode=mode)
        grammar = self._grammar_check(text)

        jargon_hits = [
            token for token in _tokenize_words(text)
            if _normalize_term(token) in self.get_known_terms(mode)
        ]

        if auto_learn:
            teach_candidates = [
                s["token"] for s in spelling
                if _normalize_term(s.get("token", "")) and _is_technical_token(_normalize_term(s["token"]))
            ]
            if teach_candidates:
                self.teach_terms(teach_candidates, mode=mode)

        return {
            "status": "PASS",
            "mode": mode,
            "valid": len(spelling) == 0 and len(grammar) == 0,
            "spelling_issues": spelling,
            "grammar_issues": grammar,
            "jargon_detected": sorted(set(jargon_hits)),
            "known_jargon_count": len(self.get_known_terms(mode)),
            "lexicon_path": self.lexicon_path,
        }

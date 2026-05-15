# reasoning_protocols.py
# Canonical first-class reasoning registry for MAMA Gen1.
# Source-of-truth: proto_resonance/* (21 models).
# Contract: CONTROL selects model, SECURITY validates, MAMA consumes advisory output.

import importlib.util
import os
import unicodedata
from typing import Any, Callable, Dict, List, Tuple

CANONICAL_REGISTRY_VERSION = "2026-04-11.first_class_repair"

_BASE_DIR = os.path.dirname(__file__)
_PROTO_BASE_DIR = os.path.join(_BASE_DIR, "proto_resonance")

_REASONING_MODELS: Dict[str, Dict[str, str]] = {
    "ethical_hum": {"domain": "Humanities", "file": "Humanities/ethical_hum.py"},
    "historical_hum": {"domain": "Humanities", "file": "Humanities/historical_hum.py"},
    "literary_hum": {"domain": "Humanities", "file": "Humanities/literary_hum.py"},
    "semiotic_hum": {"domain": "Humanities", "file": "Humanities/semiotic_hum.py"},
    "analytic_phil": {"domain": "Philosophy", "file": "Philosophy/analytic_phil.py"},
    "dialectical_phil": {"domain": "Philosophy", "file": "Philosophy/dialectical_phil.py"},
    "phenomenological_phil": {"domain": "Philosophy", "file": "Philosophy/phenomenological_phil.py"},
    "pragmatic_phil": {"domain": "Philosophy", "file": "Philosophy/pragmatic_phil.py"},
    "creative_science": {"domain": "Science", "file": "Science/creative_science.py"},
    "game_science": {"domain": "Science", "file": "Science/game_science.py"},
    "pattern_science": {"domain": "Science", "file": "Science/pattern_science.py"},
    "scientific_method": {"domain": "Science", "file": "Science/scientific_method.py"},
    "systems_science": {"domain": "Science", "file": "Science/systems_science.py"},
    "adaptive_tactics": {"domain": "Tactics", "file": "Tactics/adaptive_tactics.py"},
    "operational_tactics": {"domain": "Tactics", "file": "Tactics/operational_tactics.py"},
    "strategic_tactics": {"domain": "Tactics", "file": "Tactics/strategic_tactics.py"},
    "tactical_tactics": {"domain": "Tactics", "file": "Tactics/tactical_tactics.py"},
    "dogmatic_theo": {"domain": "Theology", "file": "Theology/dogmatic_theo.py"},
    "epoche_theo": {"domain": "Theology", "file": "Theology/epoche_theo.py"},
    "gnostic_theo": {"domain": "Theology", "file": "Theology/gnostic_theo.py"},
    "heuristic_theo": {"domain": "Theology", "file": "Theology/heuristic_theo.py"},
}

_LOADED_MODULES: Dict[str, Any] = {}


def _ascii_normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", str(text))
    return normalized.encode("ascii", "ignore").decode("ascii")


def _sanitize_ascii(value: Any) -> Any:
    if isinstance(value, dict):
        return {_ascii_normalize(k): _sanitize_ascii(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_sanitize_ascii(v) for v in value]
    if isinstance(value, tuple):
        return tuple(_sanitize_ascii(v) for v in value)
    if isinstance(value, str):
        return _ascii_normalize(value)
    return value


def _load_model_module(model_name: str) -> Any:
    if model_name in _LOADED_MODULES:
        return _LOADED_MODULES[model_name]

    spec = _REASONING_MODELS[model_name]
    file_path = os.path.join(_PROTO_BASE_DIR, spec["file"])
    module_name = "sara_reasoning_" + model_name
    module_spec = importlib.util.spec_from_file_location(module_name, file_path)
    if module_spec is None or module_spec.loader is None:
        raise RuntimeError("Unable to create module spec for " + model_name)

    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    _LOADED_MODULES[model_name] = module
    return module


def _fallback_gnostic(input_data: Any) -> Dict[str, Any]:
    text = _ascii_normalize(str(input_data)).lower()
    tokens = text.split()
    symbols = [k for k in ["alpha", "beta", "gamma", "delta", "omega"] if k in tokens]
    score = float(len(symbols)) / 5.0
    interpretation = "No internal symbols detected; coherence minimal."
    if score > 0.0:
        interpretation = "Internal symbolic structure detected; meaningful alignment."
    return {
        "approach": "gnostic",
        "input": text,
        "symbols_detected": symbols,
        "coherence_score": score,
        "interpretation": interpretation,
        "notes": "ASCII-safe fallback adapter used for quarantined raw gnostic source.",
        "adapter_mode": "quarantine_fallback",
        "status": "complete",
    }


def _invoke_model(model_name: str, input_data: Any) -> Dict[str, Any]:
    if model_name == "gnostic_theo":
        try:
            module = _load_model_module(model_name)
            raw = module.run_approach(input_data)
            safe = _sanitize_ascii(raw)
            safe["adapter_mode"] = "raw_wrapped_ascii_normalized"
            return safe
        except Exception:
            return _fallback_gnostic(input_data)

    module = _load_model_module(model_name)
    raw = module.run_approach(input_data)
    safe = _sanitize_ascii(raw)
    if not isinstance(safe, dict):
        return {
            "approach": model_name,
            "input": _ascii_normalize(str(input_data)),
            "status": "error",
            "error": "Model returned non-dict output.",
        }
    return safe


def _make_invoker(model_name: str) -> Callable[[Any], Dict[str, Any]]:
    def _runner(input_data: Any) -> Dict[str, Any]:
        return _invoke_model(model_name, input_data)

    return _runner


REASONING_PROTOCOLS: Dict[str, Callable[[Any], Dict[str, Any]]] = {
    name: _make_invoker(name) for name in sorted(_REASONING_MODELS.keys())
}


def list_reasoning_models() -> List[Dict[str, str]]:
    rows: List[Tuple[str, str, str]] = []
    for name, meta in _REASONING_MODELS.items():
        rows.append((meta["domain"], name, meta["file"]))
    rows.sort(key=lambda r: (r[0], r[1]))
    return [{"domain": d, "model": m, "file": f} for d, m, f in rows]


def run_reasoning_protocol(protocol_name: str, input_data: Any, mediation: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(mediation, dict):
        return {
            "status": "REJECTED",
            "error": "mediation_contract_required",
            "protocol": protocol_name,
        }

    selected_by = str(mediation.get("selected_by") or "")
    selected_model = str(mediation.get("selected_model") or "")
    security_validated = bool(mediation.get("security_validated"))
    envelope_validated = bool(mediation.get("envelope_validated"))

    if selected_by != "CONTROL":
        return {
            "status": "REJECTED",
            "error": "control_selection_required",
            "protocol": protocol_name,
        }
    if selected_model != protocol_name:
        return {
            "status": "REJECTED",
            "error": "selected_model_mismatch",
            "protocol": protocol_name,
            "selected_model": selected_model,
        }
    if not security_validated or not envelope_validated:
        return {
            "status": "REJECTED",
            "error": "security_validation_required",
            "protocol": protocol_name,
        }

    fn = REASONING_PROTOCOLS.get(protocol_name)
    if not fn:
        return {
            "status": "REJECTED",
            "error": "unknown_protocol",
            "protocol": protocol_name,
        }

    model_output = fn(input_data)
    return {
        "status": "OK",
        "registry_version": CANONICAL_REGISTRY_VERSION,
        "protocol": protocol_name,
        "domain": _REASONING_MODELS[protocol_name]["domain"],
        "selected_by": selected_by,
        "selected_model": selected_model,
        "security_validated": security_validated,
        "envelope_validated": envelope_validated,
        "advisory_only": True,
        "presentation_only": True,
        "schema_safe": True,
        "model_output": model_output,
    }

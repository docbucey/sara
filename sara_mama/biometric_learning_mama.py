"""
SARA MAMA — Biometric Learning Bridge

Provides concrete try/reflect/adapt functions that plug into CONTROL's LearnManager
for experiential biometric learning. Connects the signal processing pipeline
(biometrics_mama.py) to persistent storage (MamaLedger) and cross-session adaptation.

This is the core loop:
  1. try_fn:   Capture a biometric window, analyze tremor signature
  2. reflect_fn: Compare against baseline, measure filter effectiveness
  3. adapt_fn:  Update filter sensitivity curve, persist to ledger, emit CONTROL shunt
"""

import json
import os
import time
import uuid
from collections import deque
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple

from .ledger_mama import MamaLedger, _iso_now


_BIOMETRIC_LEDGER_KEY = "biometrics"
_TREMOR_HISTORY_KEY = "tremor_history"
_SENSITIVITY_CURVE_KEY = "sensitivity_curve"
_BASELINE_KEY = "baseline_profile"
_DISABILITY_PROFILE_KEY = "learned_disability_profile"
_PROGRESSION_KEY = "progression_analysis"


def _ensure_biometric_section(ledger_dir: str) -> str:
    """Ensure the biometric NDJSON ledger file exists."""
    bio_path = os.path.join(ledger_dir, "mama_biometric_ledger.ndjson")
    os.makedirs(os.path.dirname(bio_path), exist_ok=True)
    if not os.path.exists(bio_path):
        with open(bio_path, "w", encoding="utf-8") as f:
            f.write("")
    return bio_path


def _append_biometric_entry(bio_path: str, entry: Dict[str, Any]) -> None:
    entry["ts"] = _iso_now()
    with open(bio_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, default=str) + "\n")


def _load_biometric_entries(bio_path: str, entry_type: Optional[str] = None) -> List[Dict[str, Any]]:
    entries = []
    if not os.path.exists(bio_path):
        return entries
    with open(bio_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                if entry_type is None or rec.get("entry_type") == entry_type:
                    entries.append(rec)
            except json.JSONDecodeError:
                continue
    return entries


def _load_latest_baseline(bio_path: str) -> Optional[Dict[str, Any]]:
    baselines = _load_biometric_entries(bio_path, "baseline")
    return baselines[-1] if baselines else None


def _load_sensitivity_curve(bio_path: str) -> List[Dict[str, Any]]:
    curves = _load_biometric_entries(bio_path, "sensitivity_curve")
    return curves[-1].get("curve", []) if curves else []


def store_baseline(ledger: MamaLedger, baseline_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Store a baseline calibration result."""
    bio_path = _ensure_biometric_section(ledger.logs_dir)
    entry = {
        "entry_type": "baseline",
        "user_id": baseline_dict.get("user_id", "default"),
        "baseline_date": baseline_dict.get("baseline_date", _iso_now()),
        "resting_tremor": baseline_dict.get("resting_tremor", {}),
        "movement_tremor": baseline_dict.get("movement_tremor", {}),
        "task_tremor": baseline_dict.get("task_tremor", {}),
        "stress_tremor": baseline_dict.get("stress_tremor", {}),
        "calibration_quality": baseline_dict.get("calibration_quality", 0.0),
        "notes": baseline_dict.get("notes", ""),
    }
    _append_biometric_entry(bio_path, entry)
    return {"success": True, "stored": entry}


def store_drill_result(ledger: MamaLedger, drill_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Store a TechBallCamp drill result."""
    bio_path = _ensure_biometric_section(ledger.logs_dir)
    entry = {
        "entry_type": "drill_result",
        **drill_dict,
    }
    _append_biometric_entry(bio_path, entry)
    return {"success": True, "stored": entry}


def store_tremor_snapshot(ledger: MamaLedger, tremor_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Store a real-time tremor analysis snapshot."""
    bio_path = _ensure_biometric_section(ledger.logs_dir)
    entry = {
        "entry_type": "tremor_snapshot",
        **tremor_dict,
    }
    _append_biometric_entry(bio_path, entry)
    return {"success": True, "stored": entry}


def update_sensitivity_curve(
    ledger: MamaLedger,
    difficulty_level: int,
    recommended_sensitivity: int,
    rationale: str,
    filter_effectiveness: float,
) -> Dict[str, Any]:
    """Update or append a sensitivity curve entry."""
    bio_path = _ensure_biometric_section(ledger.logs_dir)
    existing_curve = _load_sensitivity_curve(bio_path)

    updated = False
    for item in existing_curve:
        if item.get("difficulty_level") == difficulty_level:
            item["recommended_filter_sensitivity"] = recommended_sensitivity
            item["rationale"] = rationale
            item["filter_effectiveness"] = filter_effectiveness
            item["last_updated"] = _iso_now()
            updated = True
            break

    if not updated:
        existing_curve.append({
            "difficulty_level": difficulty_level,
            "recommended_filter_sensitivity": recommended_sensitivity,
            "rationale": rationale,
            "filter_effectiveness": filter_effectiveness,
            "last_updated": _iso_now(),
        })

    existing_curve.sort(key=lambda x: x.get("difficulty_level", 0))
    entry = {
        "entry_type": "sensitivity_curve",
        "curve": existing_curve,
    }
    _append_biometric_entry(bio_path, entry)
    return {"success": True, "curve": existing_curve}


def build_biometric_recommendation_shunt(
    new_sensitivity: int,
    reason: str,
    tremor_freq: float = 0.0,
    tremor_amp: float = 0.0,
    detected_condition: str = "unknown",
) -> Dict[str, Any]:
    """
    Build a BuceyShunt envelope from MAMA → CONTROL requesting a filter adjustment.
    Per BIOMETRIC_PROTOCOL_SPEC.md section 9.
    """
    return {
        "shunt_id": str(uuid.uuid4()),
        "timestamp": _iso_now(),
        "source_pillar": "MAMA",
        "target_pillar": "CONTROL",
        "intent": "adjust_filter_sensitivity",
        "requires_response": True,
        "context_tags": ["biometric", "ada_adaptation", "filter_adjustment"],
        "payload": {
            "new_sensitivity": new_sensitivity,
            "reason": reason,
            "tremor_frequency_hz": tremor_freq,
            "tremor_amplitude_px": tremor_amp,
            "detected_condition": detected_condition,
            "local_only": True,
            "ada_compliance": True,
        },
    }


def make_biometric_try_fn(
    analyze_fn: Callable,
    input_events: list,
) -> Callable:
    """
    Create a try_fn for LearnManager that captures and analyzes biometric data.

    analyze_fn should be biometrics_mama.analyze_tremor_signature
    input_events should be a list of RawInputEvent objects
    """
    def try_fn():
        if not input_events:
            return {
                "success": False,
                "reason": "no_input_events",
                "tremor_profile": None,
            }
        profile = analyze_fn(input_events)
        return {
            "success": True,
            "tremor_profile": profile if not hasattr(profile, "__dataclass_fields__") else asdict(profile),
            "event_count": len(input_events),
        }
    return try_fn


def make_biometric_reflect_fn(
    ledger: MamaLedger,
    filter_sensitivity: int,
    accuracy_with_filter: float,
    accuracy_without_filter: float,
) -> Callable:
    """
    Create a reflect_fn for LearnManager that evaluates filter effectiveness
    against baseline.
    """
    def reflect_fn(try_result: Dict[str, Any]) -> Dict[str, Any]:
        if not try_result.get("success"):
            return {
                "score": 0.0,
                "filter_effective": False,
                "recommendation": "insufficient_data",
            }

        effectiveness = accuracy_with_filter - accuracy_without_filter
        bio_path = _ensure_biometric_section(ledger.logs_dir)
        baseline = _load_latest_baseline(bio_path)

        tremor = try_result.get("tremor_profile", {})
        freq = tremor.get("frequency_hz", 0.0) if isinstance(tremor, dict) else 0.0
        baseline_freq = 0.0
        if baseline and isinstance(baseline.get("resting_tremor"), dict):
            baseline_freq = baseline["resting_tremor"].get("frequency_hz", 0.0)

        freq_drift = abs(freq - baseline_freq) if baseline_freq > 0 else 0.0

        if effectiveness > 0.3:
            recommendation = "maintain"
        elif effectiveness < -0.1:
            recommendation = "decrease_sensitivity"
        elif effectiveness > 0.05:
            recommendation = "slight_increase"
        else:
            recommendation = "maintain"

        return {
            "score": round(effectiveness, 4),
            "filter_effective": effectiveness > 0.0,
            "filter_sensitivity_used": filter_sensitivity,
            "accuracy_with_filter": accuracy_with_filter,
            "accuracy_without_filter": accuracy_without_filter,
            "baseline_available": baseline is not None,
            "frequency_drift_hz": round(freq_drift, 3),
            "recommendation": recommendation,
        }
    return reflect_fn


def make_biometric_adapt_fn(
    ledger: MamaLedger,
    current_sensitivity: int,
    difficulty_level: int = 1,
) -> Callable:
    """
    Create an adapt_fn for LearnManager that updates the filter sensitivity curve
    and emits a recommendation shunt.
    """
    def adapt_fn(feedback: Dict[str, Any]) -> Dict[str, Any]:
        recommendation = feedback.get("recommendation", "maintain")
        effectiveness = feedback.get("score", 0.0)

        if recommendation == "decrease_sensitivity":
            new_sensitivity = max(1, current_sensitivity - 1)
        elif recommendation == "slight_increase":
            new_sensitivity = min(10, current_sensitivity + 1)
        else:
            new_sensitivity = current_sensitivity

        curve_result = update_sensitivity_curve(
            ledger,
            difficulty_level=difficulty_level,
            recommended_sensitivity=new_sensitivity,
            rationale=f"LearnManager adaptation: {recommendation} (effectiveness={effectiveness:.3f})",
            filter_effectiveness=effectiveness,
        )

        shunt = None
        if new_sensitivity != current_sensitivity:
            shunt = build_biometric_recommendation_shunt(
                new_sensitivity=new_sensitivity,
                reason=f"Biometric learning: {recommendation}",
                detected_condition=feedback.get("detected_condition", "unknown"),
            )

        return {
            "adapted": True,
            "previous_sensitivity": current_sensitivity,
            "new_sensitivity": new_sensitivity,
            "recommendation": recommendation,
            "curve_updated": curve_result.get("success", False),
            "shunt_emitted": shunt is not None,
            "shunt": shunt,
        }
    return adapt_fn


def run_biometric_learning_cycle(
    ledger: MamaLedger,
    analyze_fn: Callable,
    input_events: list,
    current_sensitivity: int,
    difficulty_level: int,
    accuracy_with_filter: float,
    accuracy_without_filter: float,
    n_trials: int = 1,
) -> Dict[str, Any]:
    """
    Convenience function: runs a complete biometric learning cycle through
    CONTROL's LearnManager pattern without requiring LearnManager import.

    Returns the full cycle result including any adaptation shunts.
    """
    try_fn = make_biometric_try_fn(analyze_fn, input_events)
    reflect_fn = make_biometric_reflect_fn(
        ledger, current_sensitivity, accuracy_with_filter, accuracy_without_filter,
    )
    adapt_fn = make_biometric_adapt_fn(ledger, current_sensitivity, difficulty_level)

    results = []
    for trial in range(1, n_trials + 1):
        try_result = try_fn()
        feedback = reflect_fn(try_result)
        adaptation = adapt_fn(feedback)
        results.append({
            "trial": trial,
            "try_result": try_result,
            "feedback": feedback,
            "adaptation": adaptation,
        })

        if try_result.get("success") and isinstance(try_result.get("tremor_profile"), dict):
            store_tremor_snapshot(ledger, try_result["tremor_profile"])

    final = results[-1] if results else {}
    return {
        "success": True,
        "trials": len(results),
        "final_sensitivity": final.get("adaptation", {}).get("new_sensitivity", current_sensitivity),
        "final_recommendation": final.get("feedback", {}).get("recommendation", "unknown"),
        "shunt": final.get("adaptation", {}).get("shunt"),
        "results": results,
    }


def get_biometric_status(ledger: MamaLedger) -> Dict[str, Any]:
    """Get current biometric learning status — baseline, curve, progression."""
    bio_path = _ensure_biometric_section(ledger.logs_dir)
    baseline = _load_latest_baseline(bio_path)
    curve = _load_sensitivity_curve(bio_path)
    tremor_snapshots = _load_biometric_entries(bio_path, "tremor_snapshot")
    drill_results = _load_biometric_entries(bio_path, "drill_result")

    return {
        "baseline_calibrated": baseline is not None,
        "baseline_date": baseline.get("baseline_date") if baseline else None,
        "calibration_quality": baseline.get("calibration_quality", 0.0) if baseline else 0.0,
        "sensitivity_curve_levels": len(curve),
        "total_tremor_snapshots": len(tremor_snapshots),
        "total_drill_sessions": len(drill_results),
        "last_snapshot": tremor_snapshots[-1] if tremor_snapshots else None,
        "last_drill": drill_results[-1] if drill_results else None,
        "ada_active": True,
        "constant_local_adaptation": True,
    }

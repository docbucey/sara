"""
Biometric context extraction, tremor detection, adaptive filtering, and progressive
disability profiling for MAMA.

This module implements the full signal-processing pipeline described in
BIOMETRIC_PROTOCOL_SPEC.md.  It captures raw input events, extracts tremor
signatures via frequency-domain analysis, classifies conditions against known
disability profiles, applies a Kalman-inspired adaptive filter, tracks condition
progression across sessions, and integrates with MamaLedger for cross-session
learning.

Design constraints
------------------
* Pure-Python fallbacks for every numpy call so the module works on machines
  without numpy installed.
* No external dependencies beyond what SARA already uses.
* All biometric data is aggregate / statistical — never raw samples — to
  respect privacy and HIPAA-adjacent constraints.
"""

from __future__ import annotations

import math
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

try:
    import numpy as _np  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover
    _np = None  # pure-Python fallbacks used throughout

from .osh_mama import _phase1_osh_surface_mama


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class RawInputEvent:
    """A single unified HID event, matching DisabilityMapper's HidEvent model.

    Everything comes through one struct — keyboard keys, mouse buttons, gamepad
    axes, touch contacts, adaptive controllers, sip-and-puff, whatever. The
    biometric pipeline analyzes the timing and value stream regardless of what
    hardware produced it. Per-device tremor filtering (debounce, deadzone,
    smooth alpha) lives in the filter layer, not here.
    """
    device_id: str             # stable device path/guid from HidService
    input_name: str            # e.g. "Key_A", "Mouse.Left", "Button3", "Axis_X+", "Contact1_Down"
    value: float               # 1.0/0.0 for buttons, -1..+1 for axes, 0..1 for sliders
    timestamp: float           # time.time() epoch seconds
    # Legacy compat fields (optional, default to zero/empty)
    raw_x: int = 0
    raw_y: int = 0
    raw_delta_time: float = 0.0


@dataclass
class HidBiometricProfile:
    """Unified biometric profile from any HID device stream.

    Analyzes timing patterns, rhythm consistency, correction rate, and fatigue
    regardless of whether the input came from a keyboard, gamepad, adaptive
    controller, or anything else. No device-type branching.
    """
    avg_inter_event_ms: float       # average time between input events
    inter_event_std_ms: float       # timing consistency
    rhythm_regularity: float        # 0-1, how consistent the input rhythm is
    correction_rate: float          # fraction of correction/undo events
    event_rate_hz: float            # events per second
    fatigue_score: float            # 0-1, composite fatigue indicator
    fatigue_color: str              # "green" | "yellow" | "red" — the only thing the UI shows
    detected_condition: str         # condition estimate from input patterns
    confidence: float               # 0-1
    active_devices: int             # how many distinct devices contributed
    timestamp: float


@dataclass
class TremorProfile:
    """Result of a single tremor-analysis window."""
    frequency_hz: float
    amplitude_px: float
    regularity_score: float    # 0–1
    detected_condition: str    # parkinsons | essential_tremor | tardive_dyskinesia | age_related | none
    confidence: float          # 0–1
    timestamp: float


@dataclass
class DrillResult:
    """Performance metrics from one TechBallCamp drill session."""
    drill_name: str
    difficulty_level: int
    duration_sec: float
    targets: int
    hits: int
    accuracy: float
    tremor_interference_events: int
    avg_reaction_time_ms: float
    reaction_time_std_dev_ms: float
    fatigue_trend: str         # "stable" | "increasing" | "decreasing"
    detected_condition: str
    tremor_frequency_hz: float
    tremor_amplitude_px: float
    session_date: str
    sara_filter_applied: bool
    filter_sensitivity_level: int


@dataclass
class ProgressionAnalysis:
    """Cross-session trend analysis for a user's condition."""
    progression_status: str    # STABLE | WORSENING | IMPROVING | UNCERTAIN
    tremor_frequency_trend: float
    tremor_amplitude_trend: float
    accuracy_trend: float
    recommendation: str


@dataclass
class BaselineProfile:
    """Calibration snapshot captured during initial warm-up drills."""
    user_id: str
    baseline_date: str
    resting_tremor: dict
    movement_tremor: dict
    task_tremor: dict
    stress_tremor: dict
    calibration_quality: float
    notes: str


# ---------------------------------------------------------------------------
# Known disability profiles & drill constants
# ---------------------------------------------------------------------------

DISABILITY_PROFILES: Dict[str, Dict[str, Any]] = {
    "parkinsons": {
        "freq_range": (4.0, 6.0),
        "amplitude_typical": 2.5,
        "onset": "resting",
        "pattern": "regular",
    },
    "essential_tremor": {
        "freq_range": (6.0, 12.0),
        "amplitude_typical": 4.0,
        "onset": "action",
        "pattern": "variable",
    },
    "tardive_dyskinesia": {
        "freq_range": (1.0, 3.0),
        "amplitude_typical": 5.0,
        "onset": "induced",
        "pattern": "irregular",
    },
    "age_related": {
        "freq_range": (3.0, 8.0),
        "amplitude_typical": 3.0,
        "onset": "progressive",
        "pattern": "fatigue_linked",
    },
}

DRILL_TYPES: List[str] = [
    "precision_tap",
    "reaction_time",
    "sweep",
    "rhythm",
    "endurance",
    "ball_tracking",
    "multi_tap",
    "hold_steady",
]

CONDITION_ADAPTATIONS: Dict[str, Dict[str, Any]] = {
    "parkinsons": {
        "drill_pacing": "moderate",
        "rest_interval_sec": 120,
        "filter_approach": "smooth_pursuit_suppression",
        "alert_frequency_hz": (3.8, 6.5),
        "alert_amplitude_px": 3.5,
        "medication_cycle_tracking": True,
        "best_drill_sequence": ["hold_steady", "sweep", "ball_tracking", "rhythm"],
    },
    "essential_tremor": {
        "drill_pacing": "fast",
        "rest_interval_sec": 90,
        "filter_approach": "active_movement_damping",
        "alert_frequency_hz": (5.5, 14.0),
        "alert_amplitude_px": 4.5,
        "medication_cycle_tracking": False,
        "best_drill_sequence": ["sweep", "multi_tap", "precision_tap", "rhythm"],
    },
    "tardive_dyskinesia": {
        "drill_pacing": "variable",
        "rest_interval_sec": 150,
        "filter_approach": "movement_prediction_and_correction",
        "alert_frequency_hz": (0.8, 4.0),
        "alert_amplitude_px": 5.5,
        "medication_cycle_tracking": True,
        "best_drill_sequence": ["hold_steady", "ball_tracking", "rhythm", "sweep"],
    },
}


# ---------------------------------------------------------------------------
# Circular buffer for real-time event storage
# ---------------------------------------------------------------------------

class InputBuffer:
    """Circular buffer holding the last 10 minutes of RawInputEvents.

    ``maxlen`` is derived from an assumed sample rate of ~125 Hz (USB HID
    default polling rate) × 600 seconds = 75 000 events.  The actual storage
    is a :class:`collections.deque` so old events are dropped automatically.
    """

    _DEFAULT_SAMPLE_RATE_HZ = 125
    _WINDOW_SECONDS = 600  # 10 minutes

    def __init__(self, sample_rate_hz: int = _DEFAULT_SAMPLE_RATE_HZ) -> None:
        self._sample_rate = sample_rate_hz
        cap = sample_rate_hz * self._WINDOW_SECONDS
        self._buf: deque[RawInputEvent] = deque(maxlen=cap)

    # -- public API ----------------------------------------------------------

    @property
    def sample_rate(self) -> int:
        return self._sample_rate

    def push(self, event: RawInputEvent) -> None:
        self._buf.append(event)

    def __len__(self) -> int:
        return len(self._buf)

    def __bool__(self) -> bool:
        return len(self._buf) > 0

    def events(self) -> List[RawInputEvent]:
        """Return a snapshot of buffered events (oldest-first)."""
        return list(self._buf)

    def recent(self, n: int) -> List[RawInputEvent]:
        """Return the *n* most-recent events."""
        if n >= len(self._buf):
            return list(self._buf)
        return list(self._buf)[-n:]

    def clear(self) -> None:
        self._buf.clear()


# ---------------------------------------------------------------------------
# Helpers — safe math with numpy fallback
# ---------------------------------------------------------------------------

def _mean(values: List[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _std(values: List[float]) -> float:
    if len(values) < 2:
        return 0.0
    mu = _mean(values)
    return math.sqrt(sum((v - mu) ** 2 for v in values) / len(values))


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


# ---------------------------------------------------------------------------
# Signal processing functions
# ---------------------------------------------------------------------------

def calculate_velocity(e1: RawInputEvent, e2: RawInputEvent) -> float:
    """Pixel-per-millisecond velocity between two consecutive events."""
    dx = e2.raw_x - e1.raw_x
    dy = e2.raw_y - e1.raw_y
    dist = math.hypot(dx, dy)
    dt_ms = (e2.timestamp - e1.timestamp) * 1000.0
    if dt_ms <= 0:
        return 0.0
    return dist / dt_ms


def extract_dominant_frequency(velocities: List[float], sample_rate: float) -> float:
    """Return the dominant oscillation frequency (Hz) of *velocities*.

    Uses numpy's FFT when available; otherwise falls back to a pure-Python
    Goertzel algorithm probing 0.5 Hz bins from 0.5 Hz to ``sample_rate / 2``.
    """
    n = len(velocities)
    if n < 4:
        return 0.0

    if _np is not None:
        arr = _np.array(velocities, dtype=float)
        arr = arr - _np.mean(arr)
        fft_vals = _np.abs(_np.fft.rfft(arr))
        freqs = _np.fft.rfftfreq(n, d=1.0 / sample_rate)
        # Ignore DC component (index 0)
        if len(fft_vals) > 1:
            idx = int(_np.argmax(fft_vals[1:])) + 1
            return float(freqs[idx])
        return 0.0

    # Pure-Python Goertzel for specific frequency bins
    mean_v = _mean(velocities)
    centered = [v - mean_v for v in velocities]

    best_mag = 0.0
    best_freq = 0.0
    max_freq = sample_rate / 2.0
    freq = 0.5
    while freq <= max_freq:
        k = int(round(freq * n / sample_rate))
        if k < 1:
            freq += 0.5
            continue
        omega = 2.0 * math.pi * k / n
        coeff = 2.0 * math.cos(omega)
        s0 = 0.0
        s1 = 0.0
        s2 = 0.0
        for sample in centered:
            s0 = sample + coeff * s1 - s2
            s2 = s1
            s1 = s0
        mag = math.sqrt(s1 * s1 + s2 * s2 - coeff * s1 * s2)
        if mag > best_mag:
            best_mag = mag
            best_freq = freq
        freq += 0.5

    return best_freq


def find_peaks(values: List[float], threshold: float = 0.0) -> List[int]:
    """Return indices of local maxima in *values* that exceed *threshold*."""
    peaks: List[int] = []
    for i in range(1, len(values) - 1):
        if values[i] > values[i - 1] and values[i] > values[i + 1] and values[i] > threshold:
            peaks.append(i)
    return peaks


# ---------------------------------------------------------------------------
# Unified HID biometric analysis (device-agnostic, matches DisabilityMapper)
# ---------------------------------------------------------------------------

# Input names that indicate a correction/undo action
_CORRECTION_INPUTS = frozenset({
    "Key_BACK", "Key_DELETE", "Key_ESCAPE",
    "Key_Back", "Key_Delete", "Key_Escape",
    "Key_VK_08", "Key_VK_2E",
})


def analyze_hid_stream(events: List[RawInputEvent]) -> HidBiometricProfile:
    """Analyze a unified HID event stream from any combination of devices.

    Works identically whether the events came from a keyboard, gamepad,
    adaptive controller, touch screen, or any mix. Matches the DisabilityMapper
    HidEvent model: (DeviceId, InputName, Value, Timestamp).

    Produces a fatigue color — the only biometric signal the UI should show:
      green  = you're ok, good to go
      yellow = getting tired, consider a break soon
      red    = time to stop
    """
    now = time.time()

    if len(events) < 4:
        return HidBiometricProfile(
            avg_inter_event_ms=0.0, inter_event_std_ms=0.0,
            rhythm_regularity=1.0, correction_rate=0.0,
            event_rate_hz=0.0, fatigue_score=0.0, fatigue_color="green",
            detected_condition="none", confidence=0.0, active_devices=0,
            timestamp=now,
        )

    # --- Timing analysis (device-agnostic) ---
    inter_event_ms = []
    for i in range(1, len(events)):
        dt = (events[i].timestamp - events[i - 1].timestamp) * 1000.0
        if 0 < dt < 5000:  # ignore pauses > 5s
            inter_event_ms.append(dt)

    corrections = sum(1 for e in events if e.input_name in _CORRECTION_INPUTS)
    total_events = len(events)
    correction_rate = corrections / total_events if total_events > 0 else 0.0

    avg_ie = _mean(inter_event_ms)
    std_ie = _std(inter_event_ms)

    # Rhythm regularity: 1.0 = perfectly consistent, 0.0 = chaotic
    rhythm = _clamp(1.0 - (std_ie / (avg_ie + 1e-9)), 0.0, 1.0) if avg_ie > 0 else 0.5

    # Event rate
    total_time = events[-1].timestamp - events[0].timestamp
    event_rate = total_events / total_time if total_time > 0 else 0.0

    # Distinct devices
    active_devices = len(set(e.device_id for e in events))

    # --- Fatigue scoring (split-half comparison) ---
    half = len(inter_event_ms) // 2
    if half >= 2:
        first_half = inter_event_ms[:half]
        second_half = inter_event_ms[half:]

        slowdown = (_mean(second_half) - _mean(first_half)) / (_mean(first_half) + 1e-9)
        erratic_increase = (_std(second_half) - _std(first_half)) / (_std(first_half) + 1e-9)

        # Correction rate in second half vs first
        half_ev = len(events) // 2
        first_corr = sum(1 for e in events[:half_ev] if e.input_name in _CORRECTION_INPUTS)
        second_corr = sum(1 for e in events[half_ev:] if e.input_name in _CORRECTION_INPUTS)
        corr_increase = (second_corr - first_corr) / (first_corr + 1e-9) if first_corr > 0 else 0.0
    else:
        slowdown = 0.0
        erratic_increase = 0.0
        corr_increase = 0.0

    correction_fatigue = _clamp(correction_rate / 0.15, 0.0, 1.0)

    fatigue_score = _clamp(
        0.30 * max(0.0, slowdown)
        + 0.25 * max(0.0, erratic_increase)
        + 0.20 * correction_fatigue
        + 0.15 * max(0.0, corr_increase / 2.0)
        + 0.10 * (1.0 - rhythm),
        0.0, 1.0,
    )

    if fatigue_score >= 0.65:
        fatigue_color = "red"
    elif fatigue_score >= 0.35:
        fatigue_color = "yellow"
    else:
        fatigue_color = "green"

    # --- Condition detection from unified timing patterns ---
    condition, confidence = _match_hid_to_condition(
        avg_ie, std_ie, rhythm, correction_rate, event_rate,
    )

    return HidBiometricProfile(
        avg_inter_event_ms=round(avg_ie, 1),
        inter_event_std_ms=round(std_ie, 1),
        rhythm_regularity=round(rhythm, 3),
        correction_rate=round(correction_rate, 3),
        event_rate_hz=round(event_rate, 2),
        fatigue_score=round(fatigue_score, 3),
        fatigue_color=fatigue_color,
        detected_condition=condition,
        confidence=round(confidence, 3),
        active_devices=active_devices,
        timestamp=now,
    )


def _match_hid_to_condition(
    avg_ie: float, std_ie: float,
    rhythm: float, correction_rate: float,
    event_rate: float,
) -> Tuple[str, float]:
    """Match unified HID timing patterns against known disability profiles.

    These signatures come from the input timing, not the device type — the same
    Parkinson's resting tremor that makes a mouse shake also makes keystroke
    timing irregular in a characteristic way.
    """
    HID_PROFILES = {
        "parkinsons": {
            "avg_ie_range": (200, 600),
            "rhythm_range": (0.4, 0.8),
            "correction_range": (0.05, 0.20),
            "rate_range": (1.5, 5.0),
            "weight": {"ie": 0.30, "rhythm": 0.25, "correction": 0.20, "rate": 0.25},
        },
        "essential_tremor": {
            "avg_ie_range": (80, 350),
            "rhythm_range": (0.2, 0.5),
            "correction_range": (0.10, 0.30),
            "rate_range": (3.0, 12.0),
            "weight": {"ie": 0.20, "rhythm": 0.30, "correction": 0.30, "rate": 0.20},
        },
        "tardive_dyskinesia": {
            "avg_ie_range": (150, 800),
            "rhythm_range": (0.1, 0.4),
            "correction_range": (0.08, 0.25),
            "rate_range": (1.0, 6.0),
            "weight": {"ie": 0.15, "rhythm": 0.40, "correction": 0.25, "rate": 0.20},
        },
    }

    best_name = "none"
    best_score = 0.0

    for name, prof in HID_PROFILES.items():
        ie_lo, ie_hi = prof["avg_ie_range"]
        rhy_lo, rhy_hi = prof["rhythm_range"]
        corr_lo, corr_hi = prof["correction_range"]
        rate_lo, rate_hi = prof["rate_range"]
        w = prof["weight"]

        ie_fit = 1.0 if ie_lo <= avg_ie <= ie_hi else max(0.0, 1.0 - min(abs(avg_ie - ie_lo), abs(avg_ie - ie_hi)) / (ie_hi - ie_lo + 1e-9))
        rhy_fit = 1.0 if rhy_lo <= rhythm <= rhy_hi else max(0.0, 1.0 - min(abs(rhythm - rhy_lo), abs(rhythm - rhy_hi)) / (rhy_hi - rhy_lo + 1e-9))
        corr_fit = 1.0 if corr_lo <= correction_rate <= corr_hi else max(0.0, 1.0 - min(abs(correction_rate - corr_lo), abs(correction_rate - corr_hi)) / (corr_hi - corr_lo + 1e-9))
        rate_fit = 1.0 if rate_lo <= event_rate <= rate_hi else max(0.0, 1.0 - min(abs(event_rate - rate_lo), abs(event_rate - rate_hi)) / (rate_hi - rate_lo + 1e-9))

        score = w["ie"] * ie_fit + w["rhythm"] * rhy_fit + w["correction"] * corr_fit + w["rate"] * rate_fit
        if score > best_score:
            best_score = score
            best_name = name

    if best_score < 0.15:
        return ("none", 0.0)
    return (best_name, _clamp(best_score, 0.0, 1.0))


def get_fatigue_color(events: List[RawInputEvent]) -> str:
    """Returns just the color for the UI status indicator.

    green  = you're ok, good to go
    yellow = getting tired, break soon
    red    = time to stop

    Works on any HID device stream — keyboard, gamepad, adaptive controller, anything.
    """
    if len(events) < 4:
        return "green"
    return analyze_hid_stream(events).fatigue_color


def analyze_tremor_signature(events: List[RawInputEvent]) -> TremorProfile:
    """Full pipeline: velocity → FFT → amplitude → regularity → condition match.

    Requires at least 4 events to produce meaningful output; returns a zeroed
    ``TremorProfile`` with ``detected_condition="none"`` otherwise.
    """
    now = time.time()
    if len(events) < 4:
        return TremorProfile(0.0, 0.0, 0.0, "none", 0.0, now)

    velocities = [calculate_velocity(events[i], events[i + 1]) for i in range(len(events) - 1)]

    # Estimate effective sample rate from timestamps
    total_dt = events[-1].timestamp - events[0].timestamp
    if total_dt <= 0:
        return TremorProfile(0.0, 0.0, 0.0, "none", 0.0, now)
    effective_sr = len(velocities) / total_dt

    dominant_freq = extract_dominant_frequency(velocities, effective_sr)

    amplitude = max(velocities) - min(velocities) if velocities else 0.0

    peak_indices = find_peaks(velocities, threshold=_mean(velocities))
    if len(peak_indices) >= 2:
        intervals = [float(peak_indices[i + 1] - peak_indices[i]) for i in range(len(peak_indices) - 1)]
        mean_interval = _mean(intervals)
        if mean_interval > 0:
            regularity = _clamp(1.0 - (_std(intervals) / mean_interval), 0.0, 1.0)
        else:
            regularity = 0.0
    else:
        regularity = 0.0

    condition, confidence = match_to_disability_profile(dominant_freq, amplitude, regularity)

    return TremorProfile(
        frequency_hz=round(dominant_freq, 2),
        amplitude_px=round(amplitude, 2),
        regularity_score=round(regularity, 3),
        detected_condition=condition,
        confidence=round(confidence, 3),
        timestamp=now,
    )


def match_to_disability_profile(
    freq: float,
    amplitude: float,
    regularity: float,
) -> Tuple[str, float]:
    """Compare observed tremor parameters against known disability profiles.

    Returns ``(condition_name, confidence)`` where *confidence* ∈ [0, 1].
    The best-matching profile is returned; if none exceeds a minimal threshold
    the result is ``("none", 0.0)``.
    """
    best_name = "none"
    best_score = 0.0

    for name, prof in DISABILITY_PROFILES.items():
        lo, hi = prof["freq_range"]
        # Frequency fit: 1.0 when inside range, decaying outside
        if lo <= freq <= hi:
            freq_fit = 1.0
        else:
            dist = min(abs(freq - lo), abs(freq - hi))
            freq_fit = max(0.0, 1.0 - dist / (hi - lo + 1e-9))

        # Amplitude similarity
        amp_expected = prof["amplitude_typical"]
        amp_fit = max(0.0, 1.0 - abs(amplitude - amp_expected) / (amp_expected + 1e-9))

        # Regularity bonus: regular patterns score higher for parkinsons, lower for irregular conditions
        if prof["pattern"] == "regular":
            reg_fit = regularity
        elif prof["pattern"] == "irregular":
            reg_fit = 1.0 - regularity
        else:
            reg_fit = 0.5

        score = 0.50 * freq_fit + 0.30 * amp_fit + 0.20 * reg_fit
        if score > best_score:
            best_score = score
            best_name = name

    confidence = _clamp(best_score, 0.0, 1.0)
    if confidence < 0.15:
        return ("none", 0.0)
    return (best_name, round(confidence, 3))


# ---------------------------------------------------------------------------
# Baseline calibration
# ---------------------------------------------------------------------------

def _summarize_events(events: List[RawInputEvent]) -> dict:
    """Produce a tremor-summary dict for a set of calibration events."""
    profile = analyze_tremor_signature(events)
    return {
        "frequency_hz": profile.frequency_hz,
        "amplitude_px": profile.amplitude_px,
        "condition_confidence": profile.confidence,
        "detected_condition": profile.detected_condition,
    }


def run_baseline_calibration(
    resting_events: List[RawInputEvent],
    movement_events: List[RawInputEvent],
    task_events: List[RawInputEvent],
    stress_events: List[RawInputEvent],
    user_id: str,
) -> BaselineProfile:
    """Run a full baseline calibration from four categories of input events.

    Each event list corresponds to one phase of the TechBallCamp warm-up.
    """
    resting = _summarize_events(resting_events)
    movement = _summarize_events(movement_events)
    task = _summarize_events(task_events)
    stress = _summarize_events(stress_events)

    confidences = [
        resting.get("condition_confidence", 0.0),
        movement.get("condition_confidence", 0.0),
        task.get("condition_confidence", 0.0),
        stress.get("condition_confidence", 0.0),
    ]
    cal_quality = _mean(confidences)

    conditions = [
        d.get("detected_condition", "none")
        for d in (resting, movement, task, stress)
        if d.get("detected_condition", "none") != "none"
    ]
    if conditions:
        primary = max(set(conditions), key=conditions.count)
        notes = f"consistent {primary} signature" if conditions.count(primary) >= 2 else "mixed condition signals"
        if stress.get("amplitude_px", 0) > resting.get("amplitude_px", 0):
            notes += "; tremor increases with fatigue"
    else:
        notes = "no significant tremor detected during calibration"

    return BaselineProfile(
        user_id=user_id,
        baseline_date=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        resting_tremor=resting,
        movement_tremor=movement,
        task_tremor=task,
        stress_tremor=stress,
        calibration_quality=round(cal_quality, 3),
        notes=notes,
    )


# ---------------------------------------------------------------------------
# Adaptive filter
# ---------------------------------------------------------------------------

def apply_adaptive_filter(
    raw_x: float,
    raw_y: float,
    tremor_profile: TremorProfile,
    filter_sensitivity: int,
    last_x: float,
    last_y: float,
) -> Tuple[float, float]:
    """Simplified Kalman-inspired filter.

    *filter_sensitivity* is on a 1–10 scale where 1 preserves user agency and
    10 aggressively suppresses tremor.  Alpha blends raw input toward the
    predicted (previous) position, then clamps the displacement to an expected
    maximum derived from the tremor amplitude.
    """
    alpha = _clamp(filter_sensitivity / 10.0, 0.0, 1.0)

    predicted_x = last_x
    predicted_y = last_y

    filtered_x = (1.0 - alpha) * raw_x + alpha * predicted_x
    filtered_y = (1.0 - alpha) * raw_y + alpha * predicted_y

    max_move = max(1.0, tremor_profile.amplitude_px * 3.0)
    dx = filtered_x - last_x
    dy = filtered_y - last_y
    dist = math.hypot(dx, dy)
    if dist > max_move and dist > 0:
        scale = max_move / dist
        filtered_x = last_x + dx * scale
        filtered_y = last_y + dy * scale

    return (round(filtered_x, 2), round(filtered_y, 2))


def auto_tune_filter_sensitivity(last_effectiveness: float, current_sensitivity: int) -> int:
    """Adjust filter sensitivity based on recent effectiveness measurement.

    See spec §7.2 for the tuning algorithm.
    """
    if last_effectiveness > 0.3:
        return current_sensitivity
    elif last_effectiveness < -0.1:
        return max(1, current_sensitivity - 1)
    elif last_effectiveness > 0.05:
        return min(10, current_sensitivity + 1)
    return current_sensitivity


def measure_filter_effectiveness(accuracy_with_filter: float, accuracy_without_filter: float) -> float:
    """Return filter effectiveness in [-1.0, 1.0]."""
    return _clamp(accuracy_with_filter - accuracy_without_filter, -1.0, 1.0)


# ---------------------------------------------------------------------------
# Progressive disability profiling
# ---------------------------------------------------------------------------

def analyze_condition_progression(
    baseline: BaselineProfile,
    recent_drills: List[DrillResult],
    lookback_days: int = 30,
) -> ProgressionAnalysis:
    """Compare baseline to recent drill results to detect condition trend.

    *recent_drills* should already be filtered to the desired lookback window
    by the caller; *lookback_days* is informational metadata.
    """
    if not recent_drills:
        return ProgressionAnalysis(
            progression_status="UNCERTAIN",
            tremor_frequency_trend=0.0,
            tremor_amplitude_trend=0.0,
            accuracy_trend=0.0,
            recommendation=generate_recommendation("UNCERTAIN"),
        )

    recent_freq = _mean([d.tremor_frequency_hz for d in recent_drills])
    recent_amp = _mean([d.tremor_amplitude_px for d in recent_drills])
    recent_acc = _mean([d.accuracy for d in recent_drills])

    baseline_freq = baseline.resting_tremor.get("frequency_hz", recent_freq)
    baseline_amp = baseline.resting_tremor.get("amplitude_px", recent_amp)
    # Baseline doesn't store accuracy directly — use task_tremor confidence as proxy
    baseline_acc = baseline.task_tremor.get("condition_confidence", recent_acc)

    freq_delta = recent_freq - baseline_freq
    amp_delta = recent_amp - baseline_amp
    acc_delta = recent_acc - baseline_acc

    if abs(freq_delta) < 0.5 and abs(amp_delta) < 1.0 and acc_delta > -0.05:
        status = "STABLE"
    elif freq_delta > 0.5 or amp_delta > 1.0 or acc_delta < -0.10:
        status = "WORSENING"
    elif acc_delta > 0.05 and amp_delta < -0.5:
        status = "IMPROVING"
    else:
        status = "UNCERTAIN"

    return ProgressionAnalysis(
        progression_status=status,
        tremor_frequency_trend=round(freq_delta, 3),
        tremor_amplitude_trend=round(amp_delta, 3),
        accuracy_trend=round(acc_delta, 3),
        recommendation=generate_recommendation(status),
    )


def generate_recommendation(progression_status: str) -> str:
    """Return a human-readable recommendation for the given progression status."""
    _RECS = {
        "STABLE": (
            "Condition appears stable. Continue current drill schedule and "
            "filter settings. Re-evaluate in 30 days."
        ),
        "WORSENING": (
            "Tremor metrics show a worsening trend. Consider increasing filter "
            "sensitivity, shortening drill durations, and consulting your "
            "healthcare provider."
        ),
        "IMPROVING": (
            "Performance is improving — your motor compensation is getting "
            "stronger. Consider gradually reducing filter sensitivity to build "
            "further independence."
        ),
        "UNCERTAIN": (
            "Not enough data to determine a clear trend. Complete additional "
            "drill sessions so SARA can build a reliable picture."
        ),
    }
    return _RECS.get(progression_status, _RECS["UNCERTAIN"])


def build_learned_disability_profile(
    baseline: BaselineProfile,
    drill_history: List[DrillResult],
) -> dict:
    """Construct the full learned-disability-profile JSON (spec §5.2).

    This aggregates baseline data and all drill history into a comprehensive
    profile suitable for long-term storage in MamaLedger.
    """
    if not drill_history:
        return {
            "user_id": baseline.user_id,
            "learned_disability_profile": {
                "primary_condition": baseline.resting_tremor.get("detected_condition", "none"),
                "severity_level": "unknown",
                "tremor_characteristics": {},
                "fatigue_pattern": {},
                "optimal_work_intervals": {},
                "personalized_recommendations": {},
                "progression_notes": [],
            },
        }

    freqs = [d.tremor_frequency_hz for d in drill_history]
    amps = [d.tremor_amplitude_px for d in drill_history]
    accs = [d.accuracy for d in drill_history]

    avg_freq = _mean(freqs)
    avg_amp = _mean(amps)

    conditions = [d.detected_condition for d in drill_history if d.detected_condition != "none"]
    primary = max(set(conditions), key=conditions.count) if conditions else "none"

    if avg_amp < 2.0:
        severity = "mild"
    elif avg_amp < 4.0:
        severity = "mild_to_moderate"
    elif avg_amp < 6.0:
        severity = "moderate"
    else:
        severity = "severe"

    fatigue_durations = [d.duration_sec for d in drill_history if d.fatigue_trend == "increasing"]
    onset_time = _mean(fatigue_durations) if fatigue_durations else 180.0

    acc_drop_per_min = 0.0
    if len(accs) >= 2:
        first_half = _mean(accs[: len(accs) // 2])
        second_half = _mean(accs[len(accs) // 2:])
        total_mins = sum(d.duration_sec for d in drill_history) / 60.0
        if total_mins > 0:
            acc_drop_per_min = round((first_half - second_half) / total_mins, 4)

    progression = analyze_condition_progression(baseline, drill_history)

    notes = []
    notes.append({
        "date": baseline.baseline_date[:10] if len(baseline.baseline_date) >= 10 else baseline.baseline_date,
        "observation": f"Baseline established; {severity} tremor profile",
    })
    if drill_history:
        last_date = drill_history[-1].session_date
        notes.append({
            "date": last_date,
            "observation": f"Condition {progression.progression_status.lower()} over recent drills; "
                           f"freq trend {progression.tremor_frequency_trend:+.1f} Hz",
        })

    return {
        "user_id": baseline.user_id,
        "learned_disability_profile": {
            "primary_condition": primary,
            "severity_level": severity,
            "tremor_characteristics": {
                "frequency_hz": round(avg_freq, 2),
                "amplitude_px": round(avg_amp, 2),
                "increases_with": ["fatigue", "stress", "higher_difficulty"],
                "decreases_with": ["rest", "medication_timing", "lower_difficulty"],
            },
            "fatigue_pattern": {
                "onset_time_sec": round(onset_time, 1),
                "progression": "linear_increase",
                "accuracy_drop_per_minute": acc_drop_per_min,
                "tremor_amplification_per_minute": round(
                    (_std(amps) / (sum(d.duration_sec for d in drill_history) / 60.0))
                    if drill_history else 0.0, 3
                ),
            },
            "optimal_work_intervals": {
                "high_precision_tasks": f"{int(onset_time * 0.5)}_seconds_then_break",
                "moderate_tasks": f"{int(onset_time * 0.67)}_seconds_then_break",
                "low_intensity_tasks": f"{int(onset_time)}_seconds_then_break",
            },
            "personalized_recommendations": {
                "condition_adaptations": CONDITION_ADAPTATIONS.get(primary, {}),
            },
            "progression_notes": notes,
        },
    }


# ---------------------------------------------------------------------------
# MamaLedger integration
# ---------------------------------------------------------------------------

def store_biometric_session(
    ledger_dict: dict,
    drill_result: DrillResult,
    tremor_profile: TremorProfile,
) -> None:
    """Append a session record to ``mama_ledger["biometrics"]["tremor_history"]``."""
    bio = ledger_dict.setdefault("biometrics", {})
    history: list = bio.setdefault("tremor_history", [])
    history.append({
        "session_date": drill_result.session_date,
        "drill_name": drill_result.drill_name,
        "tremor_frequency_hz": tremor_profile.frequency_hz,
        "tremor_amplitude_px": tremor_profile.amplitude_px,
        "detected_condition": tremor_profile.detected_condition,
        "confidence": tremor_profile.confidence,
        "accuracy": drill_result.accuracy,
        "filter_sensitivity": drill_result.filter_sensitivity_level,
        "filter_applied": drill_result.sara_filter_applied,
    })


def load_sensitivity_curve(ledger_dict: dict) -> List[dict]:
    """Return the learned sensitivity curve from the ledger, or an empty list."""
    bio = ledger_dict.get("biometrics", {})
    curve = bio.get("sensitivity_curve", {})
    if isinstance(curve, dict):
        return curve.get("learned_sensitivity_curve", [])
    if isinstance(curve, list):
        return curve
    return []


def update_sensitivity_curve(
    ledger_dict: dict,
    drill_result: DrillResult,
    filter_effectiveness: float,
) -> None:
    """Update the learned sensitivity curve with data from the latest drill."""
    bio = ledger_dict.setdefault("biometrics", {})
    curve_container: dict = bio.setdefault("sensitivity_curve", {})
    curve: list = curve_container.setdefault("learned_sensitivity_curve", [])

    level = drill_result.difficulty_level
    new_sens = auto_tune_filter_sensitivity(filter_effectiveness, drill_result.filter_sensitivity_level)

    if filter_effectiveness > 0.3:
        rationale = "Filter highly effective; maintaining sensitivity"
    elif filter_effectiveness > 0.05:
        rationale = "Filter helping; slight sensitivity increase may help"
    elif filter_effectiveness < -0.1:
        rationale = "Over-filtering detected; reducing sensitivity"
    else:
        rationale = "Neutral effectiveness; maintaining current setting"

    for entry in curve:
        if entry.get("difficulty_level") == level:
            entry["recommended_filter_sensitivity"] = new_sens
            entry["rationale"] = rationale
            break
    else:
        curve.append({
            "difficulty_level": level,
            "recommended_filter_sensitivity": new_sens,
            "rationale": rationale,
        })

    curve.sort(key=lambda e: e.get("difficulty_level", 0))
    curve_container["last_updated"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    sessions = curve_container.get("sessions_used_to_learn", 0)
    curve_container["sessions_used_to_learn"] = sessions + 1


def build_biometric_recommendation_shunt(
    tremor_profile: TremorProfile,
    new_sensitivity: int,
    reason: str,
) -> dict:
    """Build a BuceyShunt envelope from MAMA→CONTROL (spec §9).

    This is how biometric analysis results are routed through CONTROL for
    validation before any filter adjustment takes effect.
    """
    return {
        "shunt_type": "biometric_recommendation",
        "source_pillar": "MAMA",
        "target_pillar": "CONTROL",
        "intent": "adjust_filter_sensitivity",
        "payload": {
            "new_sensitivity": new_sensitivity,
            "reason": reason,
            "tremor_frequency_hz": tremor_profile.frequency_hz,
            "tremor_amplitude_px": tremor_profile.amplitude_px,
            "detected_condition": tremor_profile.detected_condition,
            "confidence": tremor_profile.confidence,
            "timestamp": tremor_profile.timestamp,
        },
        "requires_user_acknowledgement": True,
    }


# ---------------------------------------------------------------------------
# Existing functions (presentation-layer biometric context)
# ---------------------------------------------------------------------------

def _extract_biometric_context_mama(
    amip_payload: Optional[Dict[str, Any]] = None,
    result: Optional[Dict[str, Any]] = None,
    input_buffer: Optional[InputBuffer] = None,
) -> Dict[str, Any]:
    """
    Build a bounded biometric/context bundle for presentation-scoped adaptation.
    This does not perform identity matching, routing mutation, or policy changes.

    Biometric context is always evaluated for local, in-program human/ADA adaptation
    when SECURITY visibility allows (phase-1 outcome). There is no end-user opt-out
    in payload; misuse or off-device sharing is a SECURITY/policy matter, not a UX toggle.
    """
    request = dict(amip_payload or {})
    payload = request.get("payload") if isinstance(request.get("payload"), dict) else {}
    biometrics = payload.get("biometrics") if isinstance(payload.get("biometrics"), dict) else {}

    phase1 = _phase1_osh_surface_mama(result)
    phase1_outcome = str(phase1.get("phase1_outcome") or "pending")
    security_allows_visibility = phase1_outcome in {"allow", "constrain"}

    voice = biometrics.get("voice") if isinstance(biometrics.get("voice"), dict) else {}
    video = biometrics.get("video") if isinstance(biometrics.get("video"), dict) else {}
    interaction = biometrics.get("interaction") if isinstance(biometrics.get("interaction"), dict) else {}

    context_bundle: Dict[str, Any] = {
        "enabled": bool(security_allows_visibility),
        "prediction_enabled": bool(security_allows_visibility),
        "constant_local_adaptation": True,
        "security_allows_visibility": security_allows_visibility,
        "phase1_outcome": phase1_outcome,
        "signals": {
            "voice": {
                "speech_rate_wpm": voice.get("speech_rate_wpm"),
                "pause_ratio": voice.get("pause_ratio"),
                "volume_variance": voice.get("volume_variance"),
            },
            "video": {
                "gaze_stability": video.get("gaze_stability"),
                "motion_level": video.get("motion_level"),
                "blink_rate": video.get("blink_rate"),
            },
            "interaction": {
                "typing_hesitation": interaction.get("typing_hesitation"),
                "correction_rate": interaction.get("correction_rate"),
                "latency_ms": interaction.get("latency_ms"),
            },
        },
        "guardrails": {
            "identity_inference": False,
            "policy_mutation": False,
            "routing_mutation": False,
            "presentation_only": True,
            "local_device_program_intent": True,
        },
    }

    if input_buffer and len(input_buffer) >= 4 and security_allows_visibility:
        all_events = input_buffer.events()
        hid_profile = analyze_hid_stream(all_events)
        context_bundle["hid_biometric"] = {
            "fatigue_color": hid_profile.fatigue_color,
            "fatigue_score": hid_profile.fatigue_score,
            "rhythm_regularity": hid_profile.rhythm_regularity,
            "correction_rate": hid_profile.correction_rate,
            "detected_condition": hid_profile.detected_condition,
            "confidence": hid_profile.confidence,
            "active_devices": hid_profile.active_devices,
            "timestamp": hid_profile.timestamp,
        }
        # Axis/position analysis for devices that provide coordinates
        has_position = any(e.raw_x != 0 or e.raw_y != 0 for e in all_events[-20:])
        if has_position:
            tremor = analyze_tremor_signature(all_events)
            context_bundle["tremor"] = {
                "frequency_hz": tremor.frequency_hz,
                "amplitude_px": tremor.amplitude_px,
                "regularity_score": tremor.regularity_score,
                "detected_condition": tremor.detected_condition,
                "confidence": tremor.confidence,
                "timestamp": tremor.timestamp,
            }

    return context_bundle


def _predict_contextual_state_mama(context_bundle: Dict[str, Any], mode: str, strain: str) -> Dict[str, Any]:
    """
    Deterministic contextual prediction for UX adaptation only.
    Output is advisory; CONTROL/SECURITY remain authoritative.
    """
    if not isinstance(context_bundle, dict) or not context_bundle.get("prediction_enabled"):
        return {
            "enabled": False,
            "predicted_state": "prediction_disabled",
            "confidence": 0.0,
            "recommended_ux_mode": "guided" if mode == "interactive" else "quiet",
            "advisory_only": True,
        }

    signals = context_bundle.get("signals") if isinstance(context_bundle.get("signals"), dict) else {}
    voice = signals.get("voice") if isinstance(signals.get("voice"), dict) else {}
    video = signals.get("video") if isinstance(signals.get("video"), dict) else {}
    interaction = signals.get("interaction") if isinstance(signals.get("interaction"), dict) else {}

    score = 0.0
    if isinstance(voice.get("pause_ratio"), (int, float)) and float(voice.get("pause_ratio")) > 0.35:
        score += 0.25
    if isinstance(interaction.get("typing_hesitation"), (int, float)) and float(interaction.get("typing_hesitation")) > 0.4:
        score += 0.25
    if isinstance(interaction.get("correction_rate"), (int, float)) and float(interaction.get("correction_rate")) > 0.3:
        score += 0.2
    if isinstance(video.get("motion_level"), (int, float)) and float(video.get("motion_level")) > 0.6:
        score += 0.15
    if strain in {"high", "critical", "constrained"}:
        score += 0.15

    if score >= 0.65:
        predicted = "overload_risk"
        recommended = "recovery_guided"
    elif score >= 0.35:
        predicted = "fatigue_risk"
        recommended = "low_strain_guided"
    else:
        predicted = "stable"
        recommended = "guided" if mode == "interactive" else "quiet"

    return {
        "enabled": True,
        "predicted_state": predicted,
        "confidence": min(1.0, round(score, 3)),
        "recommended_ux_mode": recommended,
        "advisory_only": True,
        "presentation_only": True,
    }

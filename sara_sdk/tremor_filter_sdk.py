"""
SARA SDK — Tremor Filter Service
Ported from DisabilityMapper/Services/TremorFilterService.cs

Two-stage filter for raw HID input:
  1. Debounce — ignores button presses shorter than debounce_ms
  2. Dead-zone — ignores axis movement within dead_zone radius
  3. Smoothing — exponential low-pass filter on axis values
"""

import threading
from dataclasses import dataclass
from typing import Callable, Dict, Optional, Tuple


@dataclass
class TremorFilterSettings:
    enabled: bool = True
    debounce_ms: int = 80
    axis_dead_zone: float = 0.15
    axis_smooth_alpha: float = 0.3

    @classmethod
    def from_dict(cls, d: dict) -> "TremorFilterSettings":
        return cls(
            enabled=d.get("enabled", d.get("IsEnabled", True)),
            debounce_ms=d.get("debounce_ms", d.get("DebounceMs", 80)),
            axis_dead_zone=d.get("axis_dead_zone", d.get("AxisDeadZone", 0.15)),
            axis_smooth_alpha=d.get("axis_smooth_alpha", d.get("AxisSmoothAlpha", 0.3)),
        )


class TremorFilterService:
    """Per-device debounce + dead-zone + exponential smoothing filter."""

    def __init__(self, settings: Optional[TremorFilterSettings] = None):
        self._cfg = settings or TremorFilterSettings()
        self._btn_timers: Dict[str, threading.Timer] = {}
        self._btn_pending: Dict[str, Tuple[bool, float]] = {}
        self._axis_smoothed: Dict[str, float] = {}

        self.on_filtered_button: Optional[Callable[[str, bool], None]] = None
        self.on_filtered_axis: Optional[Callable[[str, float], None]] = None

    def update_settings(self, settings: TremorFilterSettings) -> None:
        self._cfg = settings

    @property
    def settings(self) -> TremorFilterSettings:
        return self._cfg

    def on_raw_button(self, source_input: str, is_pressed: bool) -> None:
        if not self._cfg.enabled:
            if self.on_filtered_button:
                self.on_filtered_button(source_input, is_pressed)
            return

        old_timer = self._btn_timers.pop(source_input, None)
        if old_timer is not None:
            old_timer.cancel()

        def _fire() -> None:
            self._btn_timers.pop(source_input, None)
            if self.on_filtered_button:
                self.on_filtered_button(source_input, is_pressed)

        t = threading.Timer(self._cfg.debounce_ms / 1000.0, _fire)
        t.daemon = True
        self._btn_timers[source_input] = t
        t.start()

    def on_raw_axis(self, source_input: str, raw_value: float) -> float:
        if not self._cfg.enabled:
            if self.on_filtered_axis:
                self.on_filtered_axis(source_input, raw_value)
            return raw_value

        deadzoned = 0.0 if abs(raw_value) < self._cfg.axis_dead_zone else raw_value

        prev = self._axis_smoothed.get(source_input, 0.0)
        alpha = self._cfg.axis_smooth_alpha
        smoothed = alpha * deadzoned + (1.0 - alpha) * prev
        self._axis_smoothed[source_input] = smoothed

        if self.on_filtered_axis:
            self.on_filtered_axis(source_input, smoothed)
        return smoothed

    def dispose(self) -> None:
        for t in self._btn_timers.values():
            t.cancel()
        self._btn_timers.clear()

    def to_state_dict(self) -> dict:
        return {
            "enabled": self._cfg.enabled,
            "debounce_ms": self._cfg.debounce_ms,
            "axis_dead_zone": self._cfg.axis_dead_zone,
            "axis_smooth_alpha": self._cfg.axis_smooth_alpha,
            "active_timers": len(self._btn_timers),
            "tracked_axes": len(self._axis_smoothed),
        }

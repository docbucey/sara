using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using DisabilityMapper.Models;

namespace DisabilityMapper.Services
{
    /// <summary>
    /// Applies a two-stage tremor filter to raw HID input events:
    ///  1. Debounce  – ignores short button presses shorter than DebounceMs.
    ///  2. Dead-zone – ignores axis movement within AxisDeadZone radius.
    ///  3. Smoothing – exponential low-pass filter on axis values.
    /// </summary>
    public class TremorFilterService
    {
        private TremorFilterSettings _cfg;

        // Per-button state for debounce
        private readonly Dictionary<string, (bool PendingState, DateTime PressedAt)> _btnState = new();
        private readonly Dictionary<string, CancellationTokenSource> _btnTimers = new();

        // Per-axis smoothed value cache
        private readonly Dictionary<string, double> _axisSmoothed = new();

        public event Action<string, bool>?   FilteredButtonEvent;  // (sourceInput, isPressed)
        public event Action<string, double>? FilteredAxisEvent;    // (sourceInput, value -1..1)

        public TremorFilterService(TremorFilterSettings cfg)
        {
            _cfg = cfg;
        }

        public void UpdateSettings(TremorFilterSettings cfg)
        {
            _cfg = cfg;
        }

        // ── Button Input ──────────────────────────────────────────────────────

        /// <summary>
        /// Feed a raw button event. The filter fires FilteredButtonEvent only when
        /// the state has been stable for DebounceMs milliseconds.
        /// </summary>
        public void OnRawButton(string sourceInput, bool isPressed)
        {
            if (!_cfg.IsEnabled)
            {
                FilteredButtonEvent?.Invoke(sourceInput, isPressed);
                return;
            }

            // Cancel any pending timer for this button
            if (_btnTimers.TryGetValue(sourceInput, out var oldCts))
            {
                oldCts.Cancel();
                oldCts.Dispose();
            }

            var cts = new CancellationTokenSource();
            _btnTimers[sourceInput] = cts;
            _btnState[sourceInput] = (isPressed, DateTime.UtcNow);

            Task.Delay(_cfg.DebounceMs, cts.Token).ContinueWith(t =>
            {
                if (t.IsCanceled) return;
                FilteredButtonEvent?.Invoke(sourceInput, isPressed);
            }, TaskScheduler.Default);
        }

        // ── Axis Input ────────────────────────────────────────────────────────

        /// <summary>
        /// Feed a raw axis value in [-1.0, +1.0]. Returns the filtered value
        /// and fires FilteredAxisEvent.
        /// </summary>
        public double OnRawAxis(string sourceInput, double rawValue)
        {
            if (!_cfg.IsEnabled)
            {
                FilteredAxisEvent?.Invoke(sourceInput, rawValue);
                return rawValue;
            }

            // Dead-zone
            var deadzoned = Math.Abs(rawValue) < _cfg.AxisDeadZone ? 0.0 : rawValue;

            // Low-pass smoothing  y = α·x + (1-α)·y_prev
            var prev = _axisSmoothed.TryGetValue(sourceInput, out var p) ? p : 0.0;
            var smoothed = _cfg.AxisSmoothAlpha * deadzoned + (1.0 - _cfg.AxisSmoothAlpha) * prev;
            _axisSmoothed[sourceInput] = smoothed;

            FilteredAxisEvent?.Invoke(sourceInput, smoothed);
            return smoothed;
        }

        public void Dispose()
        {
            foreach (var cts in _btnTimers.Values)
            {
                cts.Cancel();
                cts.Dispose();
            }
            _btnTimers.Clear();
        }
    }
}

using System;
using System.Collections.Generic;
using System.IO;
using System.Threading;
using Newtonsoft.Json.Linq;
using InputSimulatorStandard;
using InputSimulatorStandard.Native;

namespace DisabilityMapper.Services
{
    /// <summary>
    /// Loads input_map.json and translates device axis/button events into
    /// keyboard and mouse input via InputSimulatorStandard (SendInput under the hood).
    ///
    /// Hot-reloads automatically when SARA writes a mapping change.
    /// The user never touches this file directly — they tell SARA what they want.
    /// </summary>
    public class InputMapService : IDisposable
    {
        private readonly string _mapPath;
        private JObject _map = new();
        private readonly FileSystemWatcher _watcher;
        private readonly IInputSimulator _sim = new InputSimulator();
        private readonly object _lock = new();
        private Timer? _reloadDebounce;

        public InputMapService(string saraRoot)
        {
            _mapPath = Path.Combine(saraRoot, "input_map.json");
            Reload();

            // Watch for SARA writing a new mapping
            _watcher = new FileSystemWatcher(saraRoot, "input_map.json")
            {
                NotifyFilter = NotifyFilters.LastWrite,
                EnableRaisingEvents = true
            };
            _watcher.Changed += (_, _) =>
            {
                // Debounce: file writer may flush in chunks
                _reloadDebounce?.Dispose();
                _reloadDebounce = new Timer(_ => Reload(), null, 300, Timeout.Infinite);
            };
        }

        public void Reload()
        {
            try
            {
                if (!File.Exists(_mapPath)) return;
                var text = File.ReadAllText(_mapPath);
                lock (_lock) { _map = JObject.Parse(text); }
            }
            catch { /* keep last known good map */ }
        }

        // ─── Axis dispatch ────────────────────────────────────────────────────────

        /// <summary>
        /// Dispatch an axis reading. normalized is -1.0 to +1.0, deadzone already applied.
        /// axisKey: "axis_x", "axis_y", "axis_rx" etc — matches input_map.json keys.
        /// </summary>
        public void DispatchAxis(string axisKey, double normalized)
        {
            JObject? axes;
            lock (_lock) { axes = _map["axes"] as JObject; }
            if (axes?[axisKey] is not JObject rule) return;

            double scale = rule.Value<double?>("scale") ?? DefaultAxisScale;
            bool invert  = rule.Value<bool?>("invert") ?? false;
            double val   = normalized * scale * (invert ? -1 : 1);
            int delta    = (int)Math.Round(val);
            if (delta == 0) return;

            switch (rule.Value<string>("type") ?? "")
            {
                case "mouse_rel_x": _sim.Mouse.MoveMouseBy(delta, 0); break;
                case "mouse_rel_y": _sim.Mouse.MoveMouseBy(0, delta); break;
                case "scroll_y":    _sim.Mouse.VerticalScroll(delta > 0 ? 1 : -1); break;
                case "scroll_x":    _sim.Mouse.HorizontalScroll(delta > 0 ? 1 : -1); break;
            }
        }

        // ─── Button dispatch ──────────────────────────────────────────────────────

        /// <summary>
        /// Dispatch a button event. buttonKey: "button_0", "pov_up" etc.
        /// Only fires on press (pressed=true); release is ignored for simple keys.
        /// </summary>
        public void DispatchButton(string buttonKey, bool pressed)
        {
            if (!pressed) return;

            JObject? buttons;
            lock (_lock) { buttons = _map["buttons"] as JObject; }
            if (buttons?[buttonKey] is not JObject rule) return;

            switch (rule.Value<string>("type") ?? "")
            {
                case "mouse_left":   _sim.Mouse.LeftButtonClick();   break;
                case "mouse_right":  _sim.Mouse.RightButtonClick();  break;
                case "mouse_middle": _sim.Mouse.MiddleButtonClick(); break;

                case "key":
                    if (Enum.TryParse<VirtualKeyCode>(rule.Value<string>("vk"), out var vk))
                        _sim.Keyboard.KeyPress(vk);
                    break;

                case "key_combo":
                    var keys = rule["keys"]?.ToObject<List<string>>() ?? new();
                    SendCombo(keys);
                    break;
            }
        }

        /// <summary>Convenience wrapper for hat/POV directions.</summary>
        public void DispatchPov(string direction, bool pressed)
            => DispatchButton("pov_" + direction, pressed);

        // ─── Helpers ──────────────────────────────────────────────────────────────

        private void SendCombo(List<string> keys)
        {
            var codes = new List<VirtualKeyCode>();
            foreach (var k in keys)
                if (Enum.TryParse<VirtualKeyCode>(k, out var vk))
                    codes.Add(vk);
            if (codes.Count == 0) return;
            if (codes.Count == 1) { _sim.Keyboard.KeyPress(codes[0]); return; }

            var mods = codes.GetRange(0, codes.Count - 1);
            var main = codes[codes.Count - 1];
            _sim.Keyboard.ModifiedKeyStroke(mods, main);
        }

        public double GetDeadzone(string axisKey)
        {
            lock (_lock)
            {
                if (_map["axes"]?[axisKey] is JObject rule)
                    return rule.Value<double?>("deadzone") ?? 0.15;
                return _map["defaults"]?.Value<double?>("axis_deadzone") ?? 0.15;
            }
        }

        private double DefaultAxisScale
        {
            get { lock (_lock) return _map["defaults"]?.Value<double?>("axis_scale") ?? 15.0; }
        }

        public void Dispose()
        {
            _watcher.Dispose();
            _reloadDebounce?.Dispose();
        }
    }
}

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using SharpDX.DirectInput;
using DisabilityMapper.Models;

namespace DisabilityMapper.Services
{
    /// <summary>
    /// A normalized HID event emitted for every raw input occurrence.
    /// Value is 1.0/0.0 for buttons, -1..+1 for axes, 0..1 for sliders.
    /// </summary>
    public readonly record struct HidEvent(
        string   DeviceId,
        string   InputName,
        double   Value,
        DateTime Timestamp);

    public class HidService : IDisposable
    {
        private readonly DirectInput              _di        = new();
        private readonly ProfileStore             _store;
        private readonly MacroEngine              _macro     = new();
        private readonly RawInputService          _rawInput  = new();
        private readonly TouchService             _touch     = new();
        private readonly WakeDeviceService        _wake      = new();
        private readonly List<DeviceWatcher>      _watchers  = new();
        private          VirtualDeviceService?        _vds;
        // Per-path profile+filter for raw-input (keyboard + mouse) devices
        private readonly Dictionary<string, RawHidDeviceProfile> _rawKbProfiles    = new();
        private readonly Dictionary<string, RawHidDeviceProfile> _mouseProfiles     = new();
        private readonly Dictionary<string, RawHidDeviceProfile> _touchProfiles     = new();
        private          CancellationTokenSource? _cts;

        // Tracks whether we have added the virtual Touchscreen / Pen device
        private bool _touchDeviceAdded;
        private bool _penDeviceAdded;

        public event Action<string, string>? DeviceConnected;    // (guid, name)
        public event Action<string>?          DeviceDisconnected; // (guid)

        // Profiles of devices that have disconnected — used by the reconnect loop
        private readonly Dictionary<string, DeviceProfile> _disconnectedProfiles = new();

        /// <summary>
        /// Fires for every raw input event before filtering.
        /// Args: (deviceGuid/path, label) e.g. ("guid", "Button3") or ("path", "Axis_X+") or ("path", "Key_A").
        /// Used by the Learn button and live input monitor.
        /// </summary>
        public event Action<string, string>? RawInputDetected;

    /// <summary>Fires the full structured HidEvent for every raw input.</summary>
    public event Action<HidEvent>? RawHidEvent;

        /// <summary>
        /// Connects or disconnects the Console Bridge (ViGEmBus virtual controller).
        /// Pass null to disable forwarding.
        /// </summary>
        public void SetVirtualDevice(VirtualDeviceService? vds)
        {
            _vds = vds;
            lock (_watchers)
                foreach (var w in _watchers)
                    w.VirtualDevice = vds;
        }
        /// <summary>
        /// Pass-through to MacroEngine.StenoToggleCallback.
        /// Set this from MainViewModel after construction so that StenoToggle
        /// mappings show/hide the steno keyboard without coupling to any UI type.
        /// </summary>
        public Action? StenoToggleCallback
        {
            get => _macro.StenoToggleCallback;
            set => _macro.StenoToggleCallback = value;
        }

        /// <summary>
        /// Injects a raw text string (from a steno chord) into the focused window.
        /// </summary>
        public void InjectRaw(string text) => _macro.InjectRaw(text);

        public HidService(ProfileStore store)
        {
            _store = store;
            _rawInput.RawKeyEvent    += OnRawKeyEvent;
            _rawInput.MouseRawEvent  += OnMouseRawEvent;
            _rawInput.MouseAxisEvent += OnMouseAxisEvent;
            _touch.PointerEvent      += OnPointerEvent;
        }

        // ── Discovery ────────────────────────────────────────────────────────

        /// <summary>
        /// Enumerates attached HID devices.
        /// Joysticks/gamepads come from DirectInput; keyboard devices come from
        /// Raw Input (with proper product names).
        /// </summary>
        /// <summary>
        /// Enumerates attached HID devices: joysticks/gamepads (DirectInput),
        /// keyboards and mice (Raw Input), and wake-capable input devices (SetupAPI).
        /// </summary>
        public IEnumerable<(string Guid, string Name, string Type)> EnumerateDevices()
        {
            var seen = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

            // DirectInput: joysticks and gamepads
            foreach (var info in _di.GetDevices(DeviceType.Gamepad, DeviceEnumerationFlags.AttachedOnly)
                .Concat(_di.GetDevices(DeviceType.Joystick, DeviceEnumerationFlags.AttachedOnly)))
            {
                var guid = info.InstanceGuid.ToString();
                if (!seen.Add(guid)) continue;
                var type = info.Type == DeviceType.Gamepad ? "Gamepad" : "Joystick";
                yield return (guid, info.InstanceName.TrimEnd('\0'), type);
            }

            // Raw Input: keyboards
            foreach (var (path, name) in _rawInput.EnumerateKeyboardDevices())
            {
                if (!seen.Add(path)) continue;
                yield return (path, name, "Keyboard");
            }

            // Raw Input: mice
            foreach (var (path, name) in _rawInput.EnumerateMouseDevices())
            {
                if (!seen.Add(path)) continue;
                yield return (path, name, "Mouse");
            }

            // SetupAPI: wake-capable input devices not already enumerated above
            foreach (var (devId, name, devClass) in _wake.EnumerateWakeCapableDevices())
            {
                if (!seen.Add(devId)) continue;
                yield return (devId, name, "Wake");
            }
        }

        // ── Raw Input registration ────────────────────────────────────────────

        /// <summary>Must be called once the main window handle is available (Window.Loaded).</summary>
        public void RegisterRawInput(IntPtr hwnd) => _rawInput.Register(hwnd);

        /// <summary>Forward WM_INPUT lParam here from the WPF window hook.</summary>
        public void ProcessRawInput(IntPtr lParam) => _rawInput.ProcessRawInput(lParam);

        /// <summary>
        /// Forward WM_POINTER* messages from the WPF WndProc hook so touch and pen
        /// input is recognized and routed through the mapping pipeline.
        /// </summary>
        public void ProcessPointerMessage(int msg, IntPtr wParam) =>
            _touch.ProcessPointerMessage(msg, wParam);

        // ── Polling ──────────────────────────────────────────────────────────

        /// <summary>True while background polling is running.</summary>
        public bool IsPolling => _cts is not null && !_cts.IsCancellationRequested;

        public void StartPolling()
        {
            StopPolling();
            _cts = new CancellationTokenSource();
            var token = _cts.Token;

            foreach (var (guid, name, type) in EnumerateDevices())
            {
                var profile = _store.Load(guid) ?? new DeviceProfile
                {
                    DeviceGuid = guid,
                    DeviceName = name,
                    DeviceType = type,
                    CanWake    = type == "Wake"
                };
                if (!profile.IsEnabled) continue;

                if (type == "Keyboard")
                {
                    _rawKbProfiles[guid] = new RawHidDeviceProfile(profile, _macro);
                }
                else if (type == "Mouse")
                {
                    _mouseProfiles[guid] = new RawHidDeviceProfile(profile, _macro);
                }
                else if (type is "Touchscreen" or "Pen" or "Wake")
                {
                    // No polling needed; events arrive via ProcessPointerMessage / SetupAPI
                }
                else
                {
                    CreateAndStartWatcher(profile, guid, token);
                }
                DeviceConnected?.Invoke(guid, name);
            }

            // Reconnect monitor — runs until the token is cancelled
            var reconnectThread = new Thread(() => ReconnectLoop(token)) { IsBackground = true };
            reconnectThread.Start();
        }

        /// <summary>
        /// Starts mapping for a single newly-discovered device while polling is already
        /// running. Safe to call from the UI thread. No-op if polling is not active or
        /// a watcher for this GUID already exists.
        /// </summary>
        public void StartDevice(DeviceProfile profile)
        {
            if (_cts is null || _cts.IsCancellationRequested) return;

            var guid = profile.DeviceGuid;

            if (profile.DeviceType == "Keyboard")
            {
                lock (_rawKbProfiles)
                {
                    if (_rawKbProfiles.ContainsKey(guid)) return;
                    _rawKbProfiles[guid] = new RawHidDeviceProfile(profile, _macro);
                }
                DeviceConnected?.Invoke(guid, profile.DeviceName);
                return;
            }

            if (profile.DeviceType == "Mouse")
            {
                lock (_mouseProfiles)
                {
                    if (_mouseProfiles.ContainsKey(guid)) return;
                    _mouseProfiles[guid] = new RawHidDeviceProfile(profile, _macro);
                }
                DeviceConnected?.Invoke(guid, profile.DeviceName);
                return;
            }

            if (profile.DeviceType is "Touchscreen" or "Pen" or "Wake")
            {
                DeviceConnected?.Invoke(guid, profile.DeviceName);
                return;
            }

            lock (_watchers)
            {
                // Guard: don't create a duplicate watcher for a GUID already being polled
                if (_watchers.Any(w => w.ProfileGuid.Equals(guid, StringComparison.OrdinalIgnoreCase)))
                    return;
            }

            CreateAndStartWatcher(profile, guid, _cts.Token);
            DeviceConnected?.Invoke(guid, profile.DeviceName);
        }

        private void ReconnectLoop(CancellationToken ct)
        {
            while (!ct.IsCancellationRequested)
            {
                Thread.Sleep(3000);
                if (_disconnectedProfiles.Count == 0) continue;

                string[] guids;
                lock (_disconnectedProfiles)
                    guids = _disconnectedProfiles.Keys.ToArray();

                var available = _di
                    .GetDevices(DeviceType.Gamepad,  DeviceEnumerationFlags.AttachedOnly)
                    .Concat(_di.GetDevices(DeviceType.Joystick, DeviceEnumerationFlags.AttachedOnly))
                    .Select(d => d.InstanceGuid.ToString())
                    .ToHashSet(StringComparer.OrdinalIgnoreCase);

                foreach (var guid in guids)
                {
                    if (!available.Contains(guid)) continue;

                    DeviceProfile? profile;
                    lock (_disconnectedProfiles)
                    {
                        if (!_disconnectedProfiles.TryGetValue(guid, out profile)) continue;
                        _disconnectedProfiles.Remove(guid);
                    }

                    CreateAndStartWatcher(profile, guid, ct);
                    DeviceConnected?.Invoke(guid, profile.DeviceName);
                }
            }
        }

        public void StopPolling()
        {
            _cts?.Cancel();
            lock (_watchers)
            {
                foreach (var w in _watchers) w.Dispose();
                _watchers.Clear();
            }
            lock (_disconnectedProfiles) _disconnectedProfiles.Clear();
            _rawKbProfiles.Clear();
            _mouseProfiles.Clear();
            _touchProfiles.Clear();
        }

        private void CreateAndStartWatcher(DeviceProfile profile, string guid, CancellationToken token)
        {
            var capturedGuid    = guid;
            var capturedProfile = profile;
            var watcher = new DeviceWatcher(_di, profile, _macro, token);
            watcher.RawDetected = (label, value) =>
            {
                // Normalize directional axis labels for the Learn / live-monitor display.
                // e.g. "Axis_X+" and "Axis_X-" both surface as "Axis_X" so a single row
                // covers the whole axis.  The underlying +/- distinction is preserved inside
                // DeviceWatcher for execution routing.
                var displayLabel = NormalizeAxisLabel(label);
                RawInputDetected?.Invoke(capturedGuid, displayLabel);
                RawHidEvent?.Invoke(new HidEvent(capturedGuid, displayLabel, value, DateTime.UtcNow));
            };
            watcher.Disconnected = () =>
            {
                lock (_disconnectedProfiles)
                    _disconnectedProfiles[capturedGuid] = capturedProfile;
                DeviceDisconnected?.Invoke(capturedGuid);
            };
            watcher.VirtualDevice = _vds;
            lock (_watchers) _watchers.Add(watcher);
            watcher.Start();
        }

        /// <summary>
        /// Strips trailing '+' or '-' from an axis/slider label so both directions
        /// map to the same row in the UI (e.g. "Axis_X+" → "Axis_X").
        /// Buttons, hats, and other labels are returned unchanged.
        /// </summary>
        private static string NormalizeAxisLabel(string label)
        {
            if ((label.EndsWith("+") || label.EndsWith("-")) &&
                (label.StartsWith("Axis_") || label.StartsWith("Slider")))
                return label[..^1];
            return label;
        }

        private void OnRawKeyEvent(string devicePath, string keyName, bool isDown)
        {
            if (isDown)
            {
                var label = $"Key_{keyName}";
                RawInputDetected?.Invoke(devicePath, label);
                RawHidEvent?.Invoke(new HidEvent(devicePath, label, 1.0, DateTime.UtcNow));
            }
            if (!_rawKbProfiles.TryGetValue(devicePath, out var kbp)) return;
            kbp.Filter.OnRawButton(keyName, isDown);
        }

        private void OnMouseRawEvent(string devicePath, string inputName, bool isDown)
        {
            var displayLabel = NormalizeAxisLabel(inputName);
            RawInputDetected?.Invoke(devicePath, displayLabel);
            RawHidEvent?.Invoke(new HidEvent(devicePath, displayLabel, isDown ? 1.0 : 0.0, DateTime.UtcNow));

            if (!_mouseProfiles.TryGetValue(devicePath, out var mp)) return;
            mp.Filter.OnRawButton(inputName, isDown);

            // Also emit the normalized label (Mouse.X / Mouse.Y) so static analog rows
            // can be mapped without requiring separate +/- rows.
            if (!displayLabel.Equals(inputName, StringComparison.OrdinalIgnoreCase))
                mp.Filter.OnRawButton(displayLabel, isDown);
        }

        /// <summary>
        /// Handles analog scroll-wheel axis events from RawInputService.
        /// The label ("Mouse.ScrollV" / "Mouse.ScrollH") is surfaced directly as-is
        /// so one Learn row covers the whole axis regardless of scroll direction.
        /// </summary>
        private void OnMouseAxisEvent(string devicePath, string axisName, double value)
        {
            RawInputDetected?.Invoke(devicePath, axisName);
            RawHidEvent?.Invoke(new HidEvent(devicePath, axisName, value, DateTime.UtcNow));

            if (_mouseProfiles.TryGetValue(devicePath, out var mp))
                mp.Filter.OnRawAxis(axisName, value);
        }

        private void OnPointerEvent(string deviceId, string inputName)
        {
            // Add the virtual touchscreen / pen device to the list on first contact.
            if (deviceId == TouchService.TouchDeviceId && !_touchDeviceAdded)
            {
                _touchDeviceAdded = true;
                DeviceConnected?.Invoke(deviceId, "Touchscreen");
            }
            else if (deviceId == TouchService.PenDeviceId && !_penDeviceAdded)
            {
                _penDeviceAdded = true;
                DeviceConnected?.Invoke(deviceId, "Pen / Digitizer");
            }

            RawInputDetected?.Invoke(deviceId, inputName);
            RawHidEvent?.Invoke(new HidEvent(deviceId, inputName, 1.0, DateTime.UtcNow));

            if (_touchProfiles.TryGetValue(deviceId, out var tp))
                tp.Filter.OnRawButton(inputName, true);
        }

        public void Dispose()
        {
            StopPolling();
            _di.Dispose();
            _rawInput.Dispose();
            _touch.Dispose();
        }
    }


    // ── Generic raw HID device profile (keyboard, mouse, touch) ─────────────

    /// <summary>
    /// Pairs any Raw Input device profile with its per-device tremor filter and
    /// macro routing. Used for keyboards, mice, and touch/pen virtual devices.
    /// </summary>
    internal sealed class RawHidDeviceProfile
    {
        public readonly TremorFilterService Filter;
        private const double AxisDeadzone = 0.15;

        internal RawHidDeviceProfile(DeviceProfile profile, MacroEngine macro)
        {
            Filter = new TremorFilterService(profile.TremorFilter);
            Filter.FilteredButtonEvent += (src, isDown) =>
            {
                var m = profile.Mappings.Find(
                    x => x.SourceInput.Equals(src, StringComparison.OrdinalIgnoreCase));
                if (m is not null) _ = macro.ExecuteAsync(m.Action, isDown);
            };

            Filter.FilteredAxisEvent += (src, value) =>
            {
                var analogMapping = profile.Mappings.Find(
                    x => x.SourceInput.Equals(src, StringComparison.OrdinalIgnoreCase));
                var posMapping = profile.Mappings.Find(
                    x => x.SourceInput.Equals(src + "+", StringComparison.OrdinalIgnoreCase));
                var negMapping = profile.Mappings.Find(
                    x => x.SourceInput.Equals(src + "-", StringComparison.OrdinalIgnoreCase));

                if (analogMapping is not null)
                    _ = macro.ExecuteAsync(analogMapping.Action, Math.Abs(value) > AxisDeadzone);
                if (posMapping is not null)
                    _ = macro.ExecuteAsync(posMapping.Action, value > AxisDeadzone);
                if (negMapping is not null)
                    _ = macro.ExecuteAsync(negMapping.Action, value < -AxisDeadzone);
            };
        }
    }

    // ─────────────────────────────────────────────────────────────────────────

    /// <summary>
    /// Polls a single joystick/gamepad on a background thread.
    /// Handles buttons, axes (X/Y/Z/RX/RY/RZ), up to 4 POV hat switches, and 2 sliders.
    /// All events are normalized and routed through the tremor filter and mapping pipeline.
    /// </summary>
    internal sealed class DeviceWatcher : IDisposable
    {
        private readonly DirectInput       _di;
        private readonly DeviceProfile     _profile;
        private readonly MacroEngine       _macro;
        private readonly CancellationToken _ct;
        private          Joystick?         _joystick;
        private          Thread?           _thread;
        private readonly TremorFilterService _filter;
        private          VirtualDeviceService?  _vds;

        // Hat switch state: hatIndex → set of currently active direction names
        private readonly Dictionary<int, HashSet<string>> _prevHatDirs = new();

        // Deadzone for axis raw-detection events and mapping execution
        private const double AxisDeadzone = 0.15;

        /// <summary>Fires (inputName, value) for every qualifying raw event.</summary>
        internal Action<string, double>? RawDetected;

        /// <summary>Invoked on the poll thread when the device disconnects.</summary>
        internal Action? Disconnected;

        internal string ProfileGuid => _profile.DeviceGuid;

        /// <summary>Set or clear the virtual-controller output for this watcher.</summary>
        internal VirtualDeviceService? VirtualDevice { set => _vds = value; }

        internal DeviceWatcher(DirectInput di, DeviceProfile profile,
                               MacroEngine macro, CancellationToken ct)
        {
            _di      = di;
            _profile = profile;
            _macro   = macro;
            _ct      = ct;
            _filter  = new TremorFilterService(profile.TremorFilter);
            _filter.FilteredButtonEvent += OnFilteredButton;
            _filter.FilteredAxisEvent   += OnFilteredAxis;
        }

        internal void Start()
        {
            try
            {
                _joystick = new Joystick(_di, new Guid(_profile.DeviceGuid));
                _joystick.Properties.BufferSize = 128;
                _joystick.Acquire();
            }
            catch { return; }

            _thread = new Thread(PollLoop) { IsBackground = true };
            _thread.Start();
        }

        private void PollLoop()
        {
            if (_joystick is null) return;

            while (!_ct.IsCancellationRequested)
            {
                try
                {
                    _joystick.Poll();
                    var updates = _joystick.GetBufferedData();

                    foreach (var update in updates)
                    {
                        var offset = update.Offset;

                        // ── Buttons ───────────────────────────────────────────────────
                        if (offset >= JoystickOffset.Buttons0 &&
                            offset <= JoystickOffset.Buttons127)
                        {
                            var name   = $"Button{offset - JoystickOffset.Buttons0}";
                            var isDown = update.Value != 0;
                            if (isDown) RawDetected?.Invoke(name, 1.0);
                            _filter.OnRawButton(name, isDown);
                        }
                        // ── POV hat switches (up to 4) ────────────────────────────────
                        else if (offset == JoystickOffset.PointOfViewControllers0) ProcessPov(0, update.Value);
                        else if (offset == JoystickOffset.PointOfViewControllers1) ProcessPov(1, update.Value);
                        else if (offset == JoystickOffset.PointOfViewControllers2) ProcessPov(2, update.Value);
                        else if (offset == JoystickOffset.PointOfViewControllers3) ProcessPov(3, update.Value);
                        // ── Sliders ───────────────────────────────────────────────────
                        else if (offset == JoystickOffset.Sliders0) ProcessSlider(0, update.Value);
                        else if (offset == JoystickOffset.Sliders1) ProcessSlider(1, update.Value);
                        // ── Linear + rotation axes ────────────────────────────────────
                        else
                        {
                            var axisName = offset switch
                            {
                                JoystickOffset.X         => "Axis_X",
                                JoystickOffset.Y         => "Axis_Y",
                                JoystickOffset.Z         => "Axis_Z",
                                JoystickOffset.RotationX => "Axis_RX",
                                JoystickOffset.RotationY => "Axis_RY",
                                JoystickOffset.RotationZ => "Axis_RZ",
                                _                        => (string?)null
                            };
                            if (axisName is not null)
                                ProcessAxis(axisName, update.Value);
                        }
                    }
                }
                catch (SharpDX.SharpDXException) { break; }

                Thread.Sleep(8); // ~120 Hz
            }

            Disconnected?.Invoke();
        }

        // ── Input processors ───────────────────────────────────────────────────

        private void ProcessAxis(string axisName, int rawValue)
        {
            var n = (rawValue - 32767.0) / 32767.0;
            if      (n >  AxisDeadzone) RawDetected?.Invoke(axisName + "+", n);
            else if (n < -AxisDeadzone) RawDetected?.Invoke(axisName + "-", n);
            _filter.OnRawAxis(axisName, n);
        }

        private void ProcessSlider(int index, int rawValue)
        {
            var name  = $"Slider{index}";
            var value = rawValue / 65535.0;            // normalised 0..1
            RawDetected?.Invoke(name, value);
            _filter.OnRawAxis(name, value * 2.0 - 1.0); // remap to -1..+1 for filter
        }

        /// <summary>
        /// Converts a DirectInput POV value (centidegrees, -1 = neutral) into
        /// Hat{n}_Up / Right / Down / Left button events, supporting diagonals.
        /// </summary>
        private void ProcessPov(int hatIndex, int pov)
        {
            var active = new HashSet<string>();
            if (pov != -1)
            {
                var deg    = pov / 100.0;
                var prefix = $"Hat{hatIndex}_";
                if (deg >= 315.0 || deg <  45.0) active.Add(prefix + "Up");
                if (deg >=  45.0 && deg < 135.0) active.Add(prefix + "Right");
                if (deg >= 135.0 && deg < 225.0) active.Add(prefix + "Down");
                if (deg >= 225.0 && deg < 315.0) active.Add(prefix + "Left");
            }

            var prev = _prevHatDirs.TryGetValue(hatIndex, out var p)
                ? p : new HashSet<string>();

            foreach (var dir in active.Except(prev))
            {
                RawDetected?.Invoke(dir, 1.0);
                _filter.OnRawButton(dir, true);
            }
            foreach (var dir in prev.Except(active))
                _filter.OnRawButton(dir, false);

            _prevHatDirs[hatIndex] = active;
        }

        // ── Filtered event handlers ────────────────────────────────────────────

        private void OnFilteredButton(string source, bool isPressed)
        {
            _vds?.Forward(source, isPressed ? 1.0 : 0.0);
            var mapping = _profile.Mappings
                .Find(m => m.SourceInput.Equals(source, StringComparison.OrdinalIgnoreCase));
            if (mapping is null) return;
            _ = _macro.ExecuteAsync(mapping.Action, isPressed);
        }

        private void OnFilteredAxis(string source, double value)
        {
            _vds?.Forward(source, value);
            var posMapping = _profile.Mappings
                .Find(m => m.SourceInput.Equals(source + "+", StringComparison.OrdinalIgnoreCase));
            var negMapping = _profile.Mappings
                .Find(m => m.SourceInput.Equals(source + "-", StringComparison.OrdinalIgnoreCase));
            var analogMapping = _profile.Mappings
                .Find(m => m.SourceInput.Equals(source, StringComparison.OrdinalIgnoreCase));

            if (posMapping is not null)
                _ = _macro.ExecuteAsync(posMapping.Action, value > AxisDeadzone);
            if (negMapping is not null)
                _ = _macro.ExecuteAsync(negMapping.Action, value < -AxisDeadzone);

            // Optional analog-row mapping support for cheat-sheet rows like Axis_X or Slider0.
            if (analogMapping is not null)
                _ = _macro.ExecuteAsync(analogMapping.Action, Math.Abs(value) > AxisDeadzone);
        }

        public void Dispose()
        {
            _joystick?.Unacquire();
            _joystick?.Dispose();
            _filter.Dispose();
        }
    }
}

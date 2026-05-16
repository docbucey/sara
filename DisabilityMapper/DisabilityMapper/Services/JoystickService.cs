using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using SharpDX.DirectInput;

namespace DisabilityMapper.Services
{
    /// <summary>
    /// The TSR.
    ///
    /// Polls every DirectInput device (joystick, HOTAS, G13, gamepad, flight stick)
    /// in a tight background loop and dispatches axis/button/POV events to
    /// InputMapService, which translates them to keyboard and mouse input.
    ///
    /// Philosophy: Windows HID class driver accepts any standard HID device
    /// automatically — no Logitech software, no Steam Input, no plugin.
    /// DirectInput reads whatever the OS accepted. InputMapService decides
    /// what that input means. SARA decides what the map should be.
    ///
    /// Same concept as a DOS TSR: sit in memory, own the input stream, redirect it.
    /// </summary>
    public class JoystickService : IDisposable
    {
        private readonly InputMapService _map;
        private readonly DirectInput _di = new();
        private readonly List<Joystick> _devices = new();
        private readonly CancellationTokenSource _cts = new();
        private Task? _pollTask;

        private readonly Dictionary<Guid, bool[]> _prevButtons = new();
        private readonly Dictionary<Guid, int[]>  _prevAxes    = new();
        private readonly Dictionary<Guid, int[]>  _prevPov     = new();

        // DirectInput default axis range
        private const int DI_MID   = 32767;
        private const int DI_RANGE = 65535;
        private const int POLL_MS  = 8;   // ~120 Hz — smooth enough for cursor control

        private static readonly string[] AxisKeys =
            { "axis_x", "axis_y", "axis_z", "axis_rx", "axis_ry", "axis_rz" };

        public JoystickService(InputMapService mapService)
        {
            _map = mapService;
        }

        public void Start()
        {
            RefreshDevices();
            _pollTask = Task.Run(PollLoop, _cts.Token);
        }

        // ─── Device management ────────────────────────────────────────────────────

        private void RefreshDevices()
        {
            foreach (var d in _devices) { try { d.Unacquire(); d.Dispose(); } catch { } }
            _devices.Clear();
            _prevButtons.Clear();
            _prevAxes.Clear();
            _prevPov.Clear();

            foreach (var info in _di.GetDevices(DeviceClass.GameControl, DeviceEnumerationFlags.AllDevices))
            {
                try
                {
                    var js = new Joystick(_di, info.InstanceGuid);
                    js.Properties.BufferSize = 128;
                    js.Acquire();
                    _devices.Add(js);
                    _prevButtons[info.InstanceGuid] = new bool[128];
                    _prevAxes[info.InstanceGuid]    = new int[6];
                    _prevPov[info.InstanceGuid]     = new int[4];
                }
                catch { /* device not available */ }
            }
        }

        public IReadOnlyList<string> DeviceNames()
        {
            var names = new List<string>();
            foreach (var js in _devices)
                names.Add(js.Information.ProductName);
            return names;
        }

        // ─── Poll loop ────────────────────────────────────────────────────────────

        private async Task PollLoop()
        {
            while (!_cts.Token.IsCancellationRequested)
            {
                for (int i = _devices.Count - 1; i >= 0; i--)
                {
                    try
                    {
                        var js = _devices[i];
                        js.Poll();
                        var state = js.GetCurrentState();
                        ProcessAxes(js, state);
                        ProcessButtons(js, state);
                        ProcessPov(js, state);
                    }
                    catch (SharpDX.SharpDXException)
                    {
                        // Device disconnected — refresh on next cycle
                        RefreshDevices();
                        break;
                    }
                }

                try { await Task.Delay(POLL_MS, _cts.Token); }
                catch (OperationCanceledException) { break; }
            }
        }

        // ─── State processing ─────────────────────────────────────────────────────

        private void ProcessAxes(Joystick js, JoystickState state)
        {
            var guid = js.Information.InstanceGuid;
            var prev = _prevAxes[guid];

            Span<int> raw = stackalloc int[6]
                { state.X, state.Y, state.Z, state.RotationX, state.RotationY, state.RotationZ };

            for (int i = 0; i < raw.Length; i++)
            {
                if (raw[i] == prev[i]) continue;
                prev[i] = raw[i];

                // Normalize to -1.0 .. +1.0
                double normalized = (raw[i] - DI_MID) / (double)DI_MID;

                // Apply deadzone (removes drift/tremor in center zone)
                double dz = _map.GetDeadzone(AxisKeys[i]);
                if (Math.Abs(normalized) < dz)
                    normalized = 0;
                else
                    normalized = (normalized - Math.Sign(normalized) * dz) / (1.0 - dz);

                if (Math.Abs(normalized) > 0.001)
                    _map.DispatchAxis(AxisKeys[i], normalized);
            }
        }

        private void ProcessButtons(Joystick js, JoystickState state)
        {
            var guid = js.Information.InstanceGuid;
            var prev = _prevButtons[guid];
            var btns = state.Buttons;

            int count = Math.Min(btns.Length, prev.Length);
            for (int i = 0; i < count; i++)
            {
                if (btns[i] == prev[i]) continue;
                prev[i] = btns[i];
                _map.DispatchButton($"button_{i}", btns[i]);
            }
        }

        private void ProcessPov(Joystick js, JoystickState state)
        {
            var pov = state.PointOfViewControllers;
            if (pov == null || pov.Length == 0) return;

            int angle = pov[0];  // -1 = centered; 0-35999 = angle in hundredths of degrees

            bool up    = angle >= 0 && (angle <= 4500  || angle >= 31500);
            bool right = angle >= 4500  && angle <= 13500;
            bool down  = angle >= 13500 && angle <= 22500;
            bool left  = angle >= 22500 && angle <= 31500;

            _map.DispatchPov("up",    up);
            _map.DispatchPov("right", right);
            _map.DispatchPov("down",  down);
            _map.DispatchPov("left",  left);
        }

        // ─── Cleanup ──────────────────────────────────────────────────────────────

        public void Dispose()
        {
            _cts.Cancel();
            _pollTask?.Wait(500);
            foreach (var d in _devices) { try { d.Unacquire(); d.Dispose(); } catch { } }
            _di.Dispose();
            _cts.Dispose();
        }
    }
}

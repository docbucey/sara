using System;
using Nefarius.ViGEm.Client;
using Nefarius.ViGEm.Client.Targets;
using Nefarius.ViGEm.Client.Targets.Xbox360;

namespace DisabilityMapper.Services
{
    /// <summary>
    /// Presents any connected HOTAS / joystick as a virtual Xbox 360 controller via ViGEmBus.
    /// Requires the ViGEmBus driver installed separately:
    ///   github.com/nefarius/ViGEmBus/releases
    /// </summary>
    public sealed class VirtualDeviceService : IDisposable
    {
        private ViGEmClient?        _client;
        private IXbox360Controller? _ctrl;
        private bool                _connected;

        // ── Lifecycle ─────────────────────────────────────────────────────────

        /// <summary>
        /// Attempts to connect to ViGEmBus and create a virtual Xbox 360 controller.
        /// Returns true on success; sets <paramref name="message"/> to a human-readable status.
        /// </summary>
        public bool TryConnect(out string message)
        {
            try
            {
                _client    = new ViGEmClient();
                _ctrl      = _client.CreateXbox360Controller();
                _ctrl.Connect();
                _connected = true;
                message    = "Console Bridge: active";
                return true;
            }
            catch (Exception ex)
            {
                Disconnect();
                // ViGEmBus not installed → VIGEM_ERROR_BUS_NOT_FOUND (0xE0000001)
                message = (uint)ex.HResult == 0xE0000001
                    ? "ViGEmBus driver not found — install from github.com/nefarius/ViGEmBus/releases"
                    : $"Console Bridge failed: {ex.Message}";
                return false;
            }
        }

        /// <summary>Tears down the virtual controller cleanly.</summary>
        public void Disconnect()
        {
            _connected = false;
            try { _ctrl?.Disconnect(); }   catch { /* ignore teardown errors */ }
            try { _client?.Dispose(); }    catch { }
            _ctrl   = null;
            _client = null;
        }

        // ── Input forwarding ──────────────────────────────────────────────────

        /// <summary>
        /// Routes a named input event onto the virtual controller.
        /// Axis values arrive normalised to −1..+1; button values are 0.0 or 1.0.
        /// </summary>
        public void Forward(string inputName, double value)
        {
            if (!_connected || _ctrl is null) return;

            try
            {
                switch (inputName)
                {
                    // ── Left thumb-stick ─────────────────────────────────────
                    case "Axis_X":
                        _ctrl.SetAxisValue(Xbox360Axis.LeftThumbX, ToShort(value));
                        break;
                    case "Axis_Y":
                        // DirectInput Y+ = down; XInput Y+ = up — invert
                        _ctrl.SetAxisValue(Xbox360Axis.LeftThumbY, ToShortInv(value));
                        break;

                    // ── Right thumb-stick ────────────────────────────────────
                    case "Axis_RX":
                        _ctrl.SetAxisValue(Xbox360Axis.RightThumbX, ToShort(value));
                        break;
                    case "Axis_RY":
                        _ctrl.SetAxisValue(Xbox360Axis.RightThumbY, ToShortInv(value));
                        break;

                    // ── Triggers ─────────────────────────────────────────────
                    case "Axis_Z":
                    case "Slider0":
                        _ctrl.SetSliderValue(Xbox360Slider.LeftTrigger, ToTrigger(value));
                        break;
                    case "Axis_RZ":
                    case "Slider1":
                        _ctrl.SetSliderValue(Xbox360Slider.RightTrigger, ToTrigger(value));
                        break;

                    // ── D-pad from hat switch ────────────────────────────────
                    case "Hat0_Up":    _ctrl.SetButtonState(Xbox360Button.Up,    value > 0.5); break;
                    case "Hat0_Down":  _ctrl.SetButtonState(Xbox360Button.Down,  value > 0.5); break;
                    case "Hat0_Left":  _ctrl.SetButtonState(Xbox360Button.Left,  value > 0.5); break;
                    case "Hat0_Right": _ctrl.SetButtonState(Xbox360Button.Right, value > 0.5); break;

                    // ── Face + shoulder buttons (0-9) ────────────────────────
                    // Layout: A  B  X  Y  LB  RB  Back  Start  LThumb  RThumb
                    case "Button0": _ctrl.SetButtonState(Xbox360Button.A,             value > 0.5); break;
                    case "Button1": _ctrl.SetButtonState(Xbox360Button.B,             value > 0.5); break;
                    case "Button2": _ctrl.SetButtonState(Xbox360Button.X,             value > 0.5); break;
                    case "Button3": _ctrl.SetButtonState(Xbox360Button.Y,             value > 0.5); break;
                    case "Button4": _ctrl.SetButtonState(Xbox360Button.LeftShoulder,  value > 0.5); break;
                    case "Button5": _ctrl.SetButtonState(Xbox360Button.RightShoulder, value > 0.5); break;
                    case "Button6": _ctrl.SetButtonState(Xbox360Button.Back,          value > 0.5); break;
                    case "Button7": _ctrl.SetButtonState(Xbox360Button.Start,         value > 0.5); break;
                    case "Button8": _ctrl.SetButtonState(Xbox360Button.LeftThumb,     value > 0.5); break;
                    case "Button9": _ctrl.SetButtonState(Xbox360Button.RightThumb,    value > 0.5); break;

                    default: return; // nothing to submit for unknown inputs
                }

                _ctrl.SubmitReport();
            }
            catch
            {
                // Lost connection to ViGEmBus — mark inactive so Forward is a no-op
                _connected = false;
            }
        }

        // ── Conversion helpers ────────────────────────────────────────────────

        // Normalised −1..+1  →  XInput short  −32767..+32767
        private static short ToShort(double v)
            => (short)Math.Clamp(v * 32767.0, -32768, 32767);

        // Same but inverted for Y axes
        private static short ToShortInv(double v)
            => (short)Math.Clamp(-v * 32767.0, -32768, 32767);

        // Normalised −1..+1  →  trigger byte  0 (idle) .. 255 (fully pressed)
        private static byte ToTrigger(double v)
            => (byte)Math.Clamp((v + 1.0) / 2.0 * 255.0, 0, 255);

        public void Dispose() => Disconnect();
    }
}

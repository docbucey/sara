using System;
using InputSimulatorStandard;
using InputSimulatorStandard.Native;

namespace DisabilityMapper.Services
{
    /// <summary>
    /// Routes physical controller inputs to Windows keyboard and mouse events
    /// via SendInput (Windows accessibility API).
    ///
    /// Uses InputSimulatorStandard — no kernel driver or external installation required.
    /// Compatible with VA workstation security policies and Section 508 requirements.
    ///
    /// Default mapping:
    ///   Left stick X/Y   → mouse cursor movement
    ///   Right stick X/Y  → horizontal / vertical scroll
    ///   Left trigger     → left mouse button
    ///   Right trigger    → right mouse button
    ///   D-pad            → arrow keys
    ///   A / B / X / Y   → Space / Escape / E / Q
    ///   LB / RB          → Left Shift / Left Control
    ///   Back / Start     → Tab / Return
    ///   L3 / R3          → F1 / F2
    /// </summary>
    public sealed class VirtualDeviceService : IDisposable
    {
        private readonly IInputSimulator _sim = new InputSimulator();
        private const double MouseScale       = 12.0; // normalised axis → pixels per poll
        private const double TriggerThreshold = 0.5;  // value above this = pressed
        private bool _ltHeld;
        private bool _rtHeld;

        // ── Lifecycle ─────────────────────────────────────────────────────────

        /// <summary>
        /// Always succeeds — no external driver required.
        /// </summary>
        public bool TryConnect(out string message)
        {
            message = "Input Adapter: active";
            return true;
        }

        /// <summary>No-op — no external resource to release.</summary>
        public void Disconnect() { }

        // ── Input forwarding ──────────────────────────────────────────────────

        /// <summary>
        /// Routes a named input event to keyboard or mouse output via SendInput.
        /// Axis values arrive normalised to −1..+1; button values are 0.0 or 1.0.
        /// </summary>
        public void Forward(string inputName, double value)
        {
            switch (inputName)
            {
                // ── Left stick → mouse cursor ──────────────────────────────────
                case "Axis_X":
                    MoveMouseX(value);
                    break;
                case "Axis_Y":
                    // Invert: joystick Y+ = forward/up → cursor moves up (screen Y-)
                    MoveMouseY(-value);
                    break;

                // ── Right stick → scroll ───────────────────────────────────────
                case "Axis_RX":
                    { int n = (int)Math.Round(value * 2.0); if (n != 0) _sim.Mouse.HorizontalScroll(n); }
                    break;
                case "Axis_RY":
                    { int n = (int)Math.Round(-value * 2.0); if (n != 0) _sim.Mouse.VerticalScroll(n); }
                    break;

                // ── Left trigger → left click ──────────────────────────────────
                case "Axis_Z":
                case "Slider0":
                    ToggleMouseButton(value, ref _ltHeld, leftButton: true);
                    break;

                // ── Right trigger → right click ────────────────────────────────
                case "Axis_RZ":
                case "Slider1":
                    ToggleMouseButton(value, ref _rtHeld, leftButton: false);
                    break;

                // ── D-pad → arrow keys ─────────────────────────────────────────
                case "Hat0_Up":    ToggleKey(VirtualKeyCode.UP,    value > 0.5); break;
                case "Hat0_Down":  ToggleKey(VirtualKeyCode.DOWN,  value > 0.5); break;
                case "Hat0_Left":  ToggleKey(VirtualKeyCode.LEFT,  value > 0.5); break;
                case "Hat0_Right": ToggleKey(VirtualKeyCode.RIGHT, value > 0.5); break;

                // ── Face + shoulder buttons ────────────────────────────────────
                // A=Space  B=Escape  X=E  Y=Q
                // LB=LShift  RB=LCtrl  Back=Tab  Start=Return  L3=F1  R3=F2
                case "Button0": ToggleKey(VirtualKeyCode.SPACE,    value > 0.5); break;
                case "Button1": ToggleKey(VirtualKeyCode.ESCAPE,   value > 0.5); break;
                case "Button2": ToggleKey(VirtualKeyCode.VK_E,     value > 0.5); break;
                case "Button3": ToggleKey(VirtualKeyCode.VK_Q,     value > 0.5); break;
                case "Button4": ToggleKey(VirtualKeyCode.LSHIFT,   value > 0.5); break;
                case "Button5": ToggleKey(VirtualKeyCode.LCONTROL, value > 0.5); break;
                case "Button6": ToggleKey(VirtualKeyCode.TAB,      value > 0.5); break;
                case "Button7": ToggleKey(VirtualKeyCode.RETURN,   value > 0.5); break;
                case "Button8": ToggleKey(VirtualKeyCode.F1,       value > 0.5); break;
                case "Button9": ToggleKey(VirtualKeyCode.F2,       value > 0.5); break;
            }
        }

        // ── Helpers ───────────────────────────────────────────────────────────

        private void MoveMouseX(double v)
        {
            int delta = (int)Math.Round(v * MouseScale);
            if (delta != 0) _sim.Mouse.MoveMouseBy(delta, 0);
        }

        private void MoveMouseY(double v)
        {
            int delta = (int)Math.Round(v * MouseScale);
            if (delta != 0) _sim.Mouse.MoveMouseBy(0, delta);
        }

        private void ToggleKey(VirtualKeyCode key, bool pressed)
        {
            if (pressed) _sim.Keyboard.KeyDown(key);
            else         _sim.Keyboard.KeyUp(key);
        }

        private void ToggleMouseButton(double value, ref bool held, bool leftButton)
        {
            bool pressed = value > TriggerThreshold;
            if (pressed == held) return;
            held = pressed;
            if (leftButton)
            {
                if (pressed) _sim.Mouse.LeftButtonDown();
                else         _sim.Mouse.LeftButtonUp();
            }
            else
            {
                if (pressed) _sim.Mouse.RightButtonDown();
                else         _sim.Mouse.RightButtonUp();
            }
        }

        public void Dispose() { }
    }
}

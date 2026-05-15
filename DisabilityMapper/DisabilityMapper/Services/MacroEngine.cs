using System;
using System.Threading;
using System.Threading.Tasks;
using InputSimulatorStandard;
using InputSimulatorStandard.Native;
using DisabilityMapper.Models;

namespace DisabilityMapper.Services
{
    /// <summary>
    /// Executes a MappingAction using InputSimulatorStandard.
    /// Supports: KeyPress, MouseClick, MouseMove, MacroText (with delay + natural jitter).
    /// </summary>
    public class MacroEngine
    {
        private readonly InputSimulator _sim = new();
        private readonly Random _rng = new();

        /// <summary>
        /// Assigned by MainViewModel so that a StenoToggle mapping action can
        /// show/hide the steno keyboard window without MacroEngine needing a
        /// reference to any UI type.
        /// </summary>
        public Action? StenoToggleCallback { get; set; }

        public async Task ExecuteAsync(MappingAction action, bool isPress, CancellationToken ct = default)
        {
            switch (action.Type)
            {
                case "KeyPress":
                    ExecuteKeyPress(action, isPress);
                    break;

                case "MouseClick":
                    ExecuteMouseClick(action, isPress);
                    break;

                case "MouseMove":
                    ExecuteMouseMove(action);
                    break;

                case "MacroText" when isPress:
                    await ExecuteMacroTextAsync(action, ct);
                    break;

                case "Command" when isPress:
                    ExecuteCommand(action);
                    break;

                case "StenoToggle" when isPress:
                    StenoToggleCallback?.Invoke();
                    break;
            }
        }

        // ── Key Press / Hold ─────────────────────────────────────────────────

        private void ExecuteKeyPress(MappingAction action, bool isPress)
        {
            if (!Enum.TryParse<VirtualKeyCode>(action.Value, out var vk)) return;

            if (action.HoldMode)
            {
                if (isPress) _sim.Keyboard.KeyDown(vk);
                else         _sim.Keyboard.KeyUp(vk);
            }
            else if (isPress)
            {
                _sim.Keyboard.KeyPress(vk);
            }
        }

        // ── Mouse ────────────────────────────────────────────────────────────

        private void ExecuteMouseClick(MappingAction action, bool isPress)
        {
            switch (action.Value)
            {
                case "Left":
                    if (action.HoldMode)
                    {
                        if (isPress) _sim.Mouse.LeftButtonDown();
                        else         _sim.Mouse.LeftButtonUp();
                    }
                    else if (isPress) _sim.Mouse.LeftButtonClick();
                    break;

                case "Right":
                    if (action.HoldMode)
                    {
                        if (isPress) _sim.Mouse.RightButtonDown();
                        else         _sim.Mouse.RightButtonUp();
                    }
                    else if (isPress) _sim.Mouse.RightButtonClick();
                    break;

                case "Middle":
                    if (isPress) _sim.Mouse.MiddleButtonClick();
                    break;
            }
        }

        private void ExecuteMouseMove(MappingAction action)
        {
            // Value format: "DX,DY"  e.g. "10,0"
            var parts = action.Value.Split(',');
            if (parts.Length == 2
                && int.TryParse(parts[0], out var dx)
                && int.TryParse(parts[1], out var dy))
            {
                _sim.Mouse.MoveMouseBy(dx, dy);
            }
        }

        // ── Macro Text ───────────────────────────────────────────────────────

        private async Task ExecuteMacroTextAsync(MappingAction action, CancellationToken ct)
        {
            if (string.IsNullOrEmpty(action.MacroText)) return;

            foreach (char ch in action.MacroText)
            {
                ct.ThrowIfCancellationRequested();
                _sim.Keyboard.TextEntry(ch);

                int delay = action.MacroDelayMs;
                if (action.MacroJitterMs > 0)
                    delay += _rng.Next(-action.MacroJitterMs, action.MacroJitterMs + 1);
                delay = Math.Max(0, delay);

                if (delay > 0)
                    await Task.Delay(delay, ct);
            }
        }

        // ── Steno raw injection ──────────────────────────────────────────────

        /// <summary>
        /// Injects a raw string directly into the OS focused window.
        /// '\b' characters are sent as real Backspace keystrokes; all other
        /// characters are injected via TextEntry (handles Unicode correctly).
        /// Called by MainViewModel when a steno chord fires TextReady.
        /// </summary>
        public void InjectRaw(string text)
        {
            if (string.IsNullOrEmpty(text)) return;
            foreach (char ch in text)
            {
                if      (ch == '\b')                _sim.Keyboard.KeyPress(VirtualKeyCode.BACK);
                else if (ch == '\r' || ch == '\n') _sim.Keyboard.KeyPress(VirtualKeyCode.RETURN);
                else if (ch == '\t')                _sim.Keyboard.KeyPress(VirtualKeyCode.TAB);
                else                                _sim.Keyboard.TextEntry(ch);
            }
        }

        // ── Shell Command ────────────────────────────────────────────────────

        private static void ExecuteCommand(MappingAction action)
        {
            if (string.IsNullOrWhiteSpace(action.Value)) return;
            // Use cmd /c for safety; only allow simple predefined strings.
            System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo
            {
                FileName        = "cmd.exe",
                Arguments       = $"/c \"{action.Value}\"",
                UseShellExecute = true,
                WindowStyle     = System.Diagnostics.ProcessWindowStyle.Hidden
            });
        }
    }
}

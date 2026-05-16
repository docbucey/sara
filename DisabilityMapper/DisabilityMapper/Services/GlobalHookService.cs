using System;
using System.Collections.Concurrent;
using System.Runtime.InteropServices;

namespace DisabilityMapper.Services
{
    /// <summary>
    /// Installs system-wide low-level keyboard and mouse hooks to apply
    /// tremor-filtering at the OS layer so every app (Word, Outlook, browser…)
    /// sees SARA-filtered input without any per-app integration.
    ///
    /// Keyboard — debounce: suppress a key-down event if the same key was
    ///   already pressed within <see cref="DebounceMs"/> milliseconds.
    ///
    /// Mouse — dead-zone: suppress WM_MOUSEMOVE events where the delta from
    ///   the last allowed position is smaller than <see cref="MouseDeadZone"/>
    ///   pixels in both axes; the cursor is snapped back so it doesn't visually
    ///   jitter even though the OS has already moved it.
    ///
    /// Both hooks detect injected synthetic events (LLKHF_INJECTED /
    /// LLMHF_INJECTED) and pass them through unchanged to avoid feedback loops.
    ///
    /// Must be created and <see cref="Start"/>-ed on the WPF UI thread (or any
    /// STA thread that pumps messages) so Windows can dispatch hook callbacks.
    /// </summary>
    public sealed class GlobalHookService : IDisposable
    {
        // ── Win32 constants ────────────────────────────────────────────────

        private const int  WH_KEYBOARD_LL  = 13;
        private const int  WH_MOUSE_LL     = 14;
        private const int  WM_KEYDOWN      = 0x0100;
        private const int  WM_SYSKEYDOWN   = 0x0104;
        private const int  WM_MOUSEMOVE    = 0x0200;
        private const uint LLKHF_INJECTED  = 0x10;   // keyboard struct flags
        private const uint LLMHF_INJECTED  = 0x01;   // mouse struct flags

        // ── P/Invoke ────────────────────────────────────────────────────────

        [UnmanagedFunctionPointer(CallingConvention.StdCall)]
        private delegate IntPtr HookProc(int nCode, IntPtr wParam, IntPtr lParam);

        [DllImport("user32.dll", CharSet = CharSet.Auto, SetLastError = true)]
        private static extern IntPtr SetWindowsHookEx(
            int idHook, HookProc lpfn, IntPtr hMod, uint dwThreadId);

        [DllImport("user32.dll", CharSet = CharSet.Auto, SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool UnhookWindowsHookEx(IntPtr hhk);

        [DllImport("user32.dll", CharSet = CharSet.Auto, SetLastError = true)]
        private static extern IntPtr CallNextHookEx(
            IntPtr hhk, int nCode, IntPtr wParam, IntPtr lParam);

        [DllImport("kernel32.dll", CharSet = CharSet.Auto, SetLastError = true)]
        private static extern IntPtr GetModuleHandle(string? lpModuleName);

        [DllImport("user32.dll", SetLastError = true)]
        private static extern bool GetCursorPos(out POINT lpPoint);

        [DllImport("user32.dll", SetLastError = true)]
        private static extern bool SetCursorPos(int X, int Y);

        [StructLayout(LayoutKind.Sequential)]
        private struct KBDLLHOOKSTRUCT
        {
            public uint   vkCode;
            public uint   scanCode;
            public uint   flags;
            public uint   time;
            public IntPtr dwExtraInfo;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct POINT { public int x; public int y; }

        [StructLayout(LayoutKind.Sequential)]
        private struct MSLLHOOKSTRUCT
        {
            public POINT  pt;
            public uint   mouseData;
            public uint   flags;
            public uint   time;
            public IntPtr dwExtraInfo;
        }

        // ── Settings (thread-safe reads; set before or after Start) ─────────

        /// <summary>Minimum milliseconds between two presses of the same key.
        /// Presses arriving sooner are swallowed. Default 100 ms.</summary>
        public int DebounceMs { get; set; } = 100;

        /// <summary>Mouse movements smaller than this (px, both axes) are
        /// suppressed and the cursor is snapped back.  Default 5 px.</summary>
        public int MouseDeadZone { get; set; } = 5;

        /// <summary>Enable keyboard debounce hook.  Default true.</summary>
        public bool KeyboardEnabled { get; set; } = true;

        /// <summary>Enable mouse dead-zone hook.  Default true.</summary>
        public bool MouseEnabled { get; set; } = true;

        // ── Hook handles (GC-pinned via fields) ──────────────────────────────

        private IntPtr   _kbHook    = IntPtr.Zero;
        private IntPtr   _mouseHook = IntPtr.Zero;
        private HookProc _kbProc    = null!;
        private HookProc _mouseProc = null!;

        public bool IsActive => _kbHook != IntPtr.Zero || _mouseHook != IntPtr.Zero;

        // ── Keyboard state ───────────────────────────────────────────────────

        // Key: virtual-key code.  Value: Environment.TickCount64 of last allowed press.
        private readonly ConcurrentDictionary<uint, long> _lastKeyTick = new();

        // ── Mouse state ──────────────────────────────────────────────────────

        private int  _prevMouseX;
        private int  _prevMouseY;
        private bool _snapPending;   // set on same thread before SetCursorPos re-entry

        // ── Public API ───────────────────────────────────────────────────────

        /// <summary>Install hooks. Must be called on the UI/message-pump thread.</summary>
        public void Start()
        {
            if (IsActive) return;

            var hMod = GetModuleHandle(null);

            if (KeyboardEnabled)
            {
                _kbProc = KbCallback;       // must be kept alive as a field
                _kbHook = SetWindowsHookEx(WH_KEYBOARD_LL, _kbProc, hMod, 0);
            }

            if (MouseEnabled)
            {
                if (GetCursorPos(out var pt))
                {
                    _prevMouseX = pt.x;
                    _prevMouseY = pt.y;
                }
                _mouseProc  = MouseCallback;
                _mouseHook  = SetWindowsHookEx(WH_MOUSE_LL, _mouseProc, hMod, 0);
            }
        }

        /// <summary>Remove hooks.</summary>
        public void Stop()
        {
            if (_kbHook != IntPtr.Zero)
            {
                UnhookWindowsHookEx(_kbHook);
                _kbHook = IntPtr.Zero;
            }

            if (_mouseHook != IntPtr.Zero)
            {
                UnhookWindowsHookEx(_mouseHook);
                _mouseHook = IntPtr.Zero;
            }

            _lastKeyTick.Clear();
            _snapPending = false;
        }

        public void Dispose() => Stop();

        // ── Keyboard hook callback ────────────────────────────────────────────

        private IntPtr KbCallback(int nCode, IntPtr wParam, IntPtr lParam)
        {
            if (nCode < 0)
                return CallNextHookEx(_kbHook, nCode, wParam, lParam);

            var data = Marshal.PtrToStructure<KBDLLHOOKSTRUCT>(lParam);

            // Always pass through events that were injected by other software
            // (or by our own future re-injection path) to avoid infinite loops.
            if ((data.flags & LLKHF_INJECTED) != 0)
                return CallNextHookEx(_kbHook, nCode, wParam, lParam);

            int msg = wParam.ToInt32();

            if (msg == WM_KEYDOWN || msg == WM_SYSKEYDOWN)
            {
                long nowMs = Environment.TickCount64;

                if (_lastKeyTick.TryGetValue(data.vkCode, out long lastMs) &&
                    nowMs - lastMs < DebounceMs)
                {
                    // Within debounce window — swallow this repeat press.
                    return new IntPtr(1);
                }

                _lastKeyTick[data.vkCode] = nowMs;
            }
            else
            {
                // Key-up: clear the debounce entry so the very next down is always fresh.
                _lastKeyTick.TryRemove(data.vkCode, out _);
            }

            return CallNextHookEx(_kbHook, nCode, wParam, lParam);
        }

        // ── Mouse hook callback ───────────────────────────────────────────────

        private IntPtr MouseCallback(int nCode, IntPtr wParam, IntPtr lParam)
        {
            if (nCode < 0)
                return CallNextHookEx(_mouseHook, nCode, wParam, lParam);

            // Re-entrant call generated by our own SetCursorPos snap-back.
            // Pass it through so the cursor actually lands at the snapped position.
            if (_snapPending)
            {
                _snapPending = false;
                return CallNextHookEx(_mouseHook, nCode, wParam, lParam);
            }

            var data = Marshal.PtrToStructure<MSLLHOOKSTRUCT>(lParam);

            // Pass through injected events (SendInput, etc.)
            if ((data.flags & LLMHF_INJECTED) != 0)
                return CallNextHookEx(_mouseHook, nCode, wParam, lParam);

            if (wParam.ToInt32() == WM_MOUSEMOVE)
            {
                int dx = data.pt.x - _prevMouseX;
                int dy = data.pt.y - _prevMouseY;

                if (Math.Abs(dx) <= MouseDeadZone && Math.Abs(dy) <= MouseDeadZone)
                {
                    // Jitter within dead-zone — snap cursor back to last allowed
                    // position so the user doesn't see visual tremor.
                    _snapPending = true;
                    SetCursorPos(_prevMouseX, _prevMouseY);
                    return new IntPtr(1);   // suppress original WM_MOUSEMOVE
                }

                // Intentional movement — accept it and update our baseline.
                _prevMouseX = data.pt.x;
                _prevMouseY = data.pt.y;
            }

            return CallNextHookEx(_mouseHook, nCode, wParam, lParam);
        }
    }
}

using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;

namespace DisabilityMapper.Services
{
    /// <summary>
    /// Processes WM_POINTER messages from the WPF WndProc hook and translates
    /// them into normalized touch/pen events that feed into the HID mapping pipeline.
    /// Supports per-contact tracking (up to 10 simultaneous contacts) and gesture
    /// recognition: Tap, Hold, Swipe (N/S/E/W).
    /// </summary>
    public sealed class TouchService : IDisposable
    {
        // ── WM_POINTER message IDs ────────────────────────────────────────────
        public const int WM_POINTERDOWN   = 0x0246;
        public const int WM_POINTERUP     = 0x0247;
        public const int WM_POINTERUPDATE = 0x0245;

        // pointer type codes
        private const uint PT_TOUCH = 2;
        private const uint PT_PEN   = 3;

        // ── P/Invoke ──────────────────────────────────────────────────────────

        [StructLayout(LayoutKind.Sequential)]
        private struct POINTER_INFO
        {
            public uint   pointerType;
            public uint   pointerId;
            public uint   frameId;
            public uint   pointerFlags;
            public IntPtr sourceDevice;         // HANDLE  (8 bytes on x64)
            public IntPtr hwndTarget;           // HWND    (8 bytes on x64)
            public POINT  ptPixelLocation;
            public POINT  ptHimetricLocation;
            public POINT  ptPixelLocationRaw;
            public POINT  ptHimetricLocationRaw;
            public uint   dwTime;
            public uint   historyCount;
            public int    InputData;
            public uint   dwKeyStates;
            public ulong  PerformanceCount;
            public uint   buttonChangeType;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct POINT { public int X; public int Y; }

        [DllImport("user32.dll", SetLastError = true)]
        private static extern bool GetPointerInfo(uint pointerId, out POINTER_INFO pointerInfo);

        [DllImport("user32.dll", SetLastError = true)]
        private static extern bool EnableMouseInPointer(bool fEnable);

        // ── Well-known virtual device IDs ─────────────────────────────────────

        /// <summary>Stable DeviceId used for the virtual Touchscreen entry in the device list.</summary>
        public const string TouchDeviceId = "VIRTUAL_TOUCHSCREEN";
        /// <summary>Stable DeviceId used for the virtual Pen / Digitizer entry.</summary>
        public const string PenDeviceId   = "VIRTUAL_PEN";

        // ── Gesture thresholds ────────────────────────────────────────────────

        private const int TapMaxMovePx = 30;
        private const int TapMaxMs     = 400;
        private const int HoldMinMs    = 750;
        private const int SwipeMinPx   = 60;

        // ── Contact state tracking ────────────────────────────────────────────

        private sealed record ContactState(uint PointerId, int StartX, int StartY, DateTime StartTime);
        private readonly Dictionary<uint, ContactState> _contacts = new();

        // ── Events ────────────────────────────────────────────────────────────

        /// <summary>
        /// Fires (deviceId, inputName) for every touch/pen event.
        /// deviceId is <see cref="TouchDeviceId"/> or <see cref="PenDeviceId"/>.
        /// inputName examples: "Contact1_Down", "Contact1_Up", "Gesture_Tap",
        ///   "Gesture_Hold", "Gesture_Swipe_North", "Gesture_Swipe_East".
        /// </summary>
        public event Action<string, string>? PointerEvent;

        // ── Construction ──────────────────────────────────────────────────────

        public TouchService()
        {
            // Prevent mouse-emulation pointer events from re-firing for the same physical action.
            EnableMouseInPointer(false);
        }

        // ── WndProc bridge ────────────────────────────────────────────────────

        /// <summary>
        /// Call from the WPF window's WndProc hook for WM_POINTERDOWN,
        /// WM_POINTERUP, and WM_POINTERUPDATE messages.
        /// </summary>
        public void ProcessPointerMessage(int msg, IntPtr wParam)
        {
            uint pointerId = (uint)(wParam.ToInt64() & 0xFFFF);
            if (!GetPointerInfo(pointerId, out var info)) return;

            var deviceId = info.pointerType switch
            {
                PT_TOUCH => TouchDeviceId,
                PT_PEN   => PenDeviceId,
                _        => null
            };
            if (deviceId is null) return;

            int x = info.ptPixelLocation.X;
            int y = info.ptPixelLocation.Y;

            switch (msg)
            {
                case WM_POINTERDOWN:
                {
                    int idx = AllocContactIndex(pointerId);
                    _contacts[pointerId] = new ContactState(pointerId, x, y, DateTime.UtcNow);
                    PointerEvent?.Invoke(deviceId, $"Contact{idx}_Down");
                    break;
                }
                case WM_POINTERUP:
                {
                    if (!_contacts.TryGetValue(pointerId, out var state)) break;

                    int idx     = CurrentContactIndex(pointerId);
                    double dx   = x - state.StartX;
                    double dy   = y - state.StartY;
                    double dist = Math.Sqrt(dx * dx + dy * dy);
                    double ms   = (DateTime.UtcNow - state.StartTime).TotalMilliseconds;

                    PointerEvent?.Invoke(deviceId, $"Contact{idx}_Up");

                    if (dist < TapMaxMovePx && ms < TapMaxMs)
                    {
                        PointerEvent?.Invoke(deviceId, "Gesture_Tap");
                    }
                    else if (dist >= SwipeMinPx)
                    {
                        double angle = Math.Atan2(dy, dx) * 180.0 / Math.PI;
                        string dir = angle switch
                        {
                            >= -45  and < 45  => "East",
                            >= 45   and < 135 => "South",
                            >= -135 and < -45 => "North",
                            _                 => "West"
                        };
                        PointerEvent?.Invoke(deviceId, $"Gesture_Swipe_{dir}");
                    }
                    else if (dist < TapMaxMovePx && ms >= HoldMinMs)
                    {
                        PointerEvent?.Invoke(deviceId, "Gesture_Hold");
                    }

                    _contacts.Remove(pointerId);
                    break;
                }
                // WM_POINTERUPDATE: update position — useful for tracking but
                // we do not fire events to avoid overwhelming the pipeline.
            }
        }

        // ── Helpers ───────────────────────────────────────────────────────────

        /// <summary>
        /// Assigns the next available 1-based contact slot, reusing released slots.
        /// </summary>
        private int AllocContactIndex(uint pointerId)
        {
            var used = new HashSet<int>();
            foreach (var kvp in _contacts)
                if (kvp.Key != pointerId)
                    used.Add(CurrentContactIndex(kvp.Key));
            for (int i = 1; i <= 10; i++)
                if (!used.Contains(i)) return i;
            return 10;
        }

        private int CurrentContactIndex(uint pointerId)
        {
            var keys = new List<uint>(_contacts.Keys);
            keys.Sort();
            int idx = keys.IndexOf(pointerId);
            return idx >= 0 ? idx + 1 : 1;
        }

        public void Dispose() { }
    }
}

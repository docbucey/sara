using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using Microsoft.Win32.SafeHandles;
using InputSimulatorStandard.Native;

namespace DisabilityMapper.Services
{
    /// <summary>
    /// Uses the Windows Raw Input API to enumerate keyboard-class HID devices
    /// with their real product names (e.g. "Logitech G13 Gaming Keyboard") and to
    /// dispatch per-device key events via WM_INPUT so the G13 and the physical
    /// keyboard are distinguishable.
    /// </summary>
    public sealed class RawInputService : IDisposable
    {
        // ── Win32 constants ──────────────────────────────────────────────────
        public  const int    WM_INPUT         = 0x00FF;
        private const uint   RIM_TYPEMOUSE    = 0;
        private const uint   RIM_TYPEKEYBOARD = 1;
        private const uint   RIDI_DEVICENAME  = 0x20000007;
        private const uint   RID_INPUT        = 0x10000003;
        private const uint   RIDEV_INPUTSINK  = 0x00000100;
        private const ushort HID_USAGE_PAGE_GENERIC = 0x01;
        private const ushort HID_USAGE_KEYBOARD     = 0x06;
        private const ushort HID_USAGE_MOUSE        = 0x02;
        private const ushort RI_KEY_BREAK    = 0x01;
        private const uint   FILE_SHARE_READ  = 0x00000001;
        private const uint   FILE_SHARE_WRITE = 0x00000002;
        private const uint   OPEN_EXISTING    = 3;

        // ── Mouse button flags (RAWMOUSE.ButtonFlags) ─────────────────────────
        private const ushort RI_MOUSE_LEFT_BUTTON_DOWN   = 0x0001;
        private const ushort RI_MOUSE_LEFT_BUTTON_UP     = 0x0002;
        private const ushort RI_MOUSE_RIGHT_BUTTON_DOWN  = 0x0004;
        private const ushort RI_MOUSE_RIGHT_BUTTON_UP    = 0x0008;
        private const ushort RI_MOUSE_MIDDLE_BUTTON_DOWN = 0x0010;
        private const ushort RI_MOUSE_MIDDLE_BUTTON_UP   = 0x0020;
        private const ushort RI_MOUSE_BUTTON_4_DOWN      = 0x0040;
        private const ushort RI_MOUSE_BUTTON_4_UP        = 0x0080;
        private const ushort RI_MOUSE_BUTTON_5_DOWN      = 0x0100;
        private const ushort RI_MOUSE_BUTTON_5_UP        = 0x0200;
        private const ushort RI_MOUSE_WHEEL              = 0x0400;
        private const ushort RI_MOUSE_HWHEEL             = 0x0800;   // horizontal wheel
        private const int    WHEEL_DELTA                 = 120;

        // ── P/Invoke structs ─────────────────────────────────────────────────

        [StructLayout(LayoutKind.Sequential)]
        private struct RAWINPUTDEVICELIST
        {
            public IntPtr hDevice;
            public uint   dwType;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct RAWINPUTDEVICE
        {
            public ushort usUsagePage;
            public ushort usUsage;
            public uint   dwFlags;
            public IntPtr hwndTarget;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct RAWINPUTHEADER
        {
            public uint   dwType;
            public uint   dwSize;
            public IntPtr hDevice;  // HANDLE  – 8 bytes on x64
            public IntPtr wParam;   // WPARAM  – 8 bytes on x64
        }

        /// <summary>
        /// Raw mouse data appended after RAWINPUTHEADER.
        /// Offsets follow the Win32 RAWMOUSE layout exactly (LayoutKind.Explicit).
        /// </summary>
        [StructLayout(LayoutKind.Explicit)]
        private struct RAWMOUSE
        {
            [FieldOffset(0)]  public ushort Flags;
            /// <summary>Button transition flags (RI_MOUSE_* constants).</summary>
            [FieldOffset(2)]  public ushort ButtonFlags;
            /// <summary>Wheel delta (signed), valid when RI_MOUSE_WHEEL is set.</summary>
            [FieldOffset(4)]  public short  ButtonData;
            [FieldOffset(6)]  public uint   RawButtons;
            /// <summary>Relative X motion (positive = right).</summary>
            [FieldOffset(10)] public int    LastX;
            /// <summary>Relative Y motion (positive = down).</summary>
            [FieldOffset(14)] public int    LastY;
            [FieldOffset(18)] public uint   ExtraInformation;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct RAWKEYBOARD
        {
            public ushort MakeCode;
            public ushort Flags;
            public ushort Reserved;
            public ushort VKey;
            public uint   Message;
            public uint   ExtraInformation;  // ULONG – always 4 bytes
        }

        // ── P/Invoke declarations ─────────────────────────────────────────────

        [DllImport("user32.dll", SetLastError = true)]
        private static extern uint GetRawInputDeviceList(
            [Out] RAWINPUTDEVICELIST[]? pList, ref uint puiNumDevices, uint cbSize);

        // Two overloads: one with IntPtr (for sizing call), one with char[] (for data)
        [DllImport("user32.dll", CharSet = CharSet.Unicode, SetLastError = true,
                   EntryPoint = "GetRawInputDeviceInfoW")]
        private static extern uint GetRawInputDeviceInfoSize(
            IntPtr hDevice, uint uiCommand, IntPtr pData, ref uint pcbSize);

        [DllImport("user32.dll", CharSet = CharSet.Unicode, SetLastError = true,
                   EntryPoint = "GetRawInputDeviceInfoW")]
        private static extern uint GetRawInputDeviceInfoChars(
            IntPtr hDevice, uint uiCommand, [Out] char[] pData, ref uint pcbSize);

        [DllImport("user32.dll", SetLastError = true)]
        private static extern bool RegisterRawInputDevices(
            RAWINPUTDEVICE[] pRawInputDevices, uint uiNumDevices, uint cbSize);

        [DllImport("user32.dll", SetLastError = true)]
        private static extern uint GetRawInputData(
            IntPtr hRawInput, uint uiCommand, IntPtr pData,
            ref uint pcbSize, uint cbSizeHeader);

        [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        private static extern SafeFileHandle CreateFile(
            string lpFileName, uint dwDesiredAccess, uint dwShareMode,
            IntPtr lpSecurityAttributes, uint dwCreationDisposition,
            uint dwFlagsAndAttributes, IntPtr hTemplateFile);

        [DllImport("hid.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        private static extern bool HidD_GetProductString(
            SafeFileHandle HidDeviceObject, [Out] char[] Buffer, uint BufferLength);

        // ── State ────────────────────────────────────────────────────────────

        // Maps raw-input device handle → device instance path
        private readonly Dictionary<IntPtr, string> _handleToPath = new();

        // ── Events ───────────────────────────────────────────────────────────

        /// <summary>
        /// Fired for every accepted keyboard event.
        /// devicePath uniquely identifies the physical device.
        /// keyName is the VirtualKeyCode name (e.g. "RETURN", "F1", "VK_41").
        /// </summary>
        public event Action<string, string, bool>? RawKeyEvent; // (devicePath, keyName, isDown)

        /// <summary>
        /// Fired for mouse button presses, releases, and movement deltas.
        /// inputName examples: "Mouse.Left", "Mouse.Right", "Mouse.X+", "Mouse.Y-".
        /// isDown: true = button pressed / axis moved in positive direction.
        /// </summary>
        public event Action<string, string, bool>? MouseRawEvent; // (devicePath, inputName, isDown)

        /// <summary>
        /// Fired for scroll-wheel axes with the real signed delta value.
        /// axisName: "Mouse.ScrollV" (vertical) or "Mouse.ScrollH" (horizontal).
        /// value: signed clicks (±1 per detent); positive = up/right, negative = down/left.
        /// </summary>
        public event Action<string, string, double>? MouseAxisEvent; // (devicePath, axisName, value)

        // ── Device enumeration ───────────────────────────────────────────────

        /// <summary>
        /// Enumerates all keyboard-class HID devices attached to the system.
        /// Returns (instancePath, friendlyName).
        /// instancePath is stable and used as the DeviceProfile.DeviceGuid value.
        /// </summary>
        /// <summary>
        /// Enumerates keyboard-class HID devices (dwType == 1).
        /// </summary>
        public IEnumerable<(string Path, string FriendlyName)> EnumerateKeyboardDevices()
            => EnumerateDevicesOfType(RIM_TYPEKEYBOARD, "Keyboard");

        /// <summary>
        /// Enumerates mouse-class HID devices (dwType == 0).
        /// </summary>
        public IEnumerable<(string Path, string FriendlyName)> EnumerateMouseDevices()
            => EnumerateDevicesOfType(RIM_TYPEMOUSE, "Mouse");

        private IEnumerable<(string Path, string FriendlyName)> EnumerateDevicesOfType(
            uint dwType, string typeLabel)
        {
            uint count = 0;
            GetRawInputDeviceList(null, ref count,
                (uint)Marshal.SizeOf<RAWINPUTDEVICELIST>());
            if (count == 0) yield break;

            var list = new RAWINPUTDEVICELIST[count];
            if (GetRawInputDeviceList(list, ref count,
                    (uint)Marshal.SizeOf<RAWINPUTDEVICELIST>()) == uint.MaxValue)
                yield break;

            foreach (var item in list)
            {
                if (item.dwType != dwType) continue;

                var path = GetDevicePath(item.hDevice);
                if (string.IsNullOrEmpty(path)) continue;

                _handleToPath[item.hDevice] = path;

                var friendly = TryGetProductString(path, typeLabel)
                               ?? BuildNameFromPath(path, typeLabel);
                yield return (path, friendly);
            }
        }

        private string? GetDevicePath(IntPtr hDevice)
        {
            uint sz = 0;
            GetRawInputDeviceInfoSize(hDevice, RIDI_DEVICENAME, IntPtr.Zero, ref sz);
            if (sz == 0) return null;

            var buf = new char[sz];
            GetRawInputDeviceInfoChars(hDevice, RIDI_DEVICENAME, buf, ref sz);
            return new string(buf).TrimEnd('\0');
        }

        private static string? TryGetProductString(string devicePath, string typeLabel)
        {
            try
            {
                using var handle = CreateFile(
                    devicePath, 0,
                    FILE_SHARE_READ | FILE_SHARE_WRITE,
                    IntPtr.Zero, OPEN_EXISTING, 0, IntPtr.Zero);

                if (handle.IsInvalid) return null;

                var buf = new char[128];
                if (!HidD_GetProductString(handle, buf, (uint)(buf.Length * 2)))
                    return null;

                var name = new string(buf).TrimEnd('\0');
                return string.IsNullOrWhiteSpace(name) ? null : $"{typeLabel} [{name}]";
            }
            catch { return null; }
        }

        /// <summary>
        /// Parses the HID instance path for VID/PID and builds a human-readable label.
        /// Example path: \\?\HID#VID_046D&PID_C21D&MI_00#...
        /// </summary>
        private static string BuildNameFromPath(string path, string typeLabel)
        {
            var upper = path.ToUpperInvariant();
            string vid = "", pid = "";

            var vi = upper.IndexOf("VID_", StringComparison.Ordinal);
            if (vi >= 0 && vi + 8 <= upper.Length) vid = upper.Substring(vi + 4, 4);

            var pi = upper.IndexOf("PID_", StringComparison.Ordinal);
            if (pi >= 0 && pi + 8 <= upper.Length) pid = upper.Substring(pi + 4, 4);

            var maker = vid switch
            {
                "046D" => "Logitech",
                "045E" => "Microsoft",
                "1532" => "Razer",
                "1B1C" => "Corsair",
                "0B05" => "ASUS",
                "1E7D" => "ROCCAT",
                "1038" => "SteelSeries",
                "03F0" => "HP",
                "413C" => "Dell",
                "04F2" => "Chicony",
                "04B3" => "IBM/Lenovo",
                "258A" => "SINOWEALTH",
                _      => vid.Length > 0 ? $"VID:{vid}" : "Generic"
            };

            return pid.Length > 0
                ? $"{typeLabel} [{maker} PID:{pid}]"
                : $"{typeLabel} [{maker}]";
        }

        // ── Registration ─────────────────────────────────────────────────────

        /// <summary>
        /// Registers this service to receive WM_INPUT messages for all keyboard
        /// devices, even when the application window is not in focus (INPUTSINK).
        /// Call this once after the main window handle is available.
        /// </summary>
        public void Register(IntPtr hwnd)
        {
            var devices = new[]
            {
                new RAWINPUTDEVICE
                {
                    usUsagePage = HID_USAGE_PAGE_GENERIC,
                    usUsage     = HID_USAGE_KEYBOARD,
                    dwFlags     = RIDEV_INPUTSINK,
                    hwndTarget  = hwnd
                },
                new RAWINPUTDEVICE
                {
                    usUsagePage = HID_USAGE_PAGE_GENERIC,
                    usUsage     = HID_USAGE_MOUSE,
                    dwFlags     = RIDEV_INPUTSINK,
                    hwndTarget  = hwnd
                }
            };
            RegisterRawInputDevices(devices, 2, (uint)Marshal.SizeOf<RAWINPUTDEVICE>());
        }

        // ── WM_INPUT processing ──────────────────────────────────────────────

        /// <summary>
        /// Call this from the WPF window's WndProc hook whenever msg == WM_INPUT.
        /// </summary>
        public void ProcessRawInput(IntPtr lParam)
        {
            uint headerSize = (uint)Marshal.SizeOf<RAWINPUTHEADER>();
            uint size = 0;
            GetRawInputData(lParam, RID_INPUT, IntPtr.Zero, ref size, headerSize);
            if (size == 0) return;

            IntPtr buf = Marshal.AllocHGlobal((int)size);
            try
            {
                if (GetRawInputData(lParam, RID_INPUT, buf, ref size, headerSize) == uint.MaxValue)
                    return;

                var header = Marshal.PtrToStructure<RAWINPUTHEADER>(buf);

                // ── Resolve device handle → path ──────────────────────────────
                if (!_handleToPath.TryGetValue(header.hDevice, out var path))
                {
                    path = GetDevicePath(header.hDevice)
                           ?? $"RAWDEV_{header.hDevice:X}";
                    _handleToPath[header.hDevice] = path;
                }

                IntPtr dataPtr = IntPtr.Add(buf, (int)headerSize);

                if (header.dwType == RIM_TYPEKEYBOARD)
                {
                    var kb = Marshal.PtrToStructure<RAWKEYBOARD>(dataPtr);
                    bool isDown = (kb.Flags & RI_KEY_BREAK) == 0;

                    var keyName = Enum.IsDefined(typeof(VirtualKeyCode), (int)kb.VKey)
                        ? ((VirtualKeyCode)kb.VKey).ToString()
                        : $"VK_{kb.VKey:X2}";

                    RawKeyEvent?.Invoke(path, keyName, isDown);
                }
                else if (header.dwType == RIM_TYPEMOUSE)
                {
                    ProcessMouseData(path, Marshal.PtrToStructure<RAWMOUSE>(dataPtr));
                }
            }
            finally
            {
                Marshal.FreeHGlobal(buf);
            }
        }

        private void ProcessMouseData(string path, RAWMOUSE m)
        {
            var bf = m.ButtonFlags;

            // ── Buttons ────────────────────────────────────────────────────────
            FireMouse(path, "Mouse.Left",     bf, RI_MOUSE_LEFT_BUTTON_DOWN,   RI_MOUSE_LEFT_BUTTON_UP);
            FireMouse(path, "Mouse.Right",    bf, RI_MOUSE_RIGHT_BUTTON_DOWN,  RI_MOUSE_RIGHT_BUTTON_UP);
            FireMouse(path, "Mouse.Middle",   bf, RI_MOUSE_MIDDLE_BUTTON_DOWN, RI_MOUSE_MIDDLE_BUTTON_UP);
            FireMouse(path, "Mouse.XButton1", bf, RI_MOUSE_BUTTON_4_DOWN,      RI_MOUSE_BUTTON_4_UP);
            FireMouse(path, "Mouse.XButton2", bf, RI_MOUSE_BUTTON_5_DOWN,      RI_MOUSE_BUTTON_5_UP);

            // ── Scroll wheels (axis events with real delta) ────────────────────
            // Vertical scroll: positive ButtonData = up, negative = down.
            if ((bf & RI_MOUSE_WHEEL) != 0)
            {
                double delta = m.ButtonData / (double)WHEEL_DELTA;
                MouseAxisEvent?.Invoke(path, "Mouse.ScrollV", delta);
            }
            // Horizontal scroll: positive ButtonData = right, negative = left.
            if ((bf & RI_MOUSE_HWHEEL) != 0)
            {
                double delta = m.ButtonData / (double)WHEEL_DELTA;
                MouseAxisEvent?.Invoke(path, "Mouse.ScrollH", delta);
            }

            // ── Relative movement ──────────────────────────────────────────────
            // Only fire when movement exceeds a minimum threshold to avoid noise.
            const int moveThreshold = 2;
            if (Math.Abs(m.LastX) >= moveThreshold)
                MouseRawEvent?.Invoke(path, m.LastX > 0 ? "Mouse.X+" : "Mouse.X-", true);
            if (Math.Abs(m.LastY) >= moveThreshold)
                MouseRawEvent?.Invoke(path, m.LastY > 0 ? "Mouse.Y+" : "Mouse.Y-", true);
        }

        private void FireMouse(string path, string name, ushort bf, ushort downFlag, ushort upFlag)
        {
            if ((bf & downFlag) != 0) MouseRawEvent?.Invoke(path, name, true);
            if ((bf & upFlag)   != 0) MouseRawEvent?.Invoke(path, name, false);
        }

        public void Dispose() { }
    }
}

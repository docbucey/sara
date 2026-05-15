using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;

namespace DisabilityMapper.Services
{
    /// <summary>
    /// Uses the Windows SetupAPI to enumerate input-class HID devices that report
    /// the CM_DEVCAP_WAKEUP capability (i.e., they can wake the machine from sleep).
    /// Results are surfaced in the device list so users can see which attached
    /// peripherals are wake-capable; no kernel driver is required.
    /// </summary>
    public sealed class WakeDeviceService
    {
        // ── SetupAPI constants ────────────────────────────────────────────────
        private const uint DIGCF_PRESENT    = 0x00000002;
        private const uint DIGCF_ALLCLASSES = 0x00000004;

        private const uint SPDRP_DEVICEDESC   = 0x00000000;
        private const uint SPDRP_CLASS        = 0x00000007;
        private const uint SPDRP_CAPABILITIES = 0x0000000F;

        /// <summary>Device can wake the system from a low-power state.</summary>
        private const uint CM_DEVCAP_WAKEUP = 0x00000080;

        // ── Structs ───────────────────────────────────────────────────────────

        [StructLayout(LayoutKind.Sequential)]
        private struct SP_DEVINFO_DATA
        {
            public uint   cbSize;
            public Guid   ClassGuid;
            public uint   DevInst;
            public IntPtr Reserved;
        }

        // ── P/Invoke ──────────────────────────────────────────────────────────

        [DllImport("setupapi.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        private static extern IntPtr SetupDiGetClassDevs(
            IntPtr ClassGuid, IntPtr Enumerator, IntPtr hwndParent, uint Flags);

        [DllImport("setupapi.dll", SetLastError = true)]
        private static extern bool SetupDiEnumDeviceInfo(
            IntPtr DeviceInfoSet, uint MemberIndex, ref SP_DEVINFO_DATA DeviceInfoData);

        [DllImport("setupapi.dll", SetLastError = true)]
        private static extern bool SetupDiDestroyDeviceInfoList(IntPtr DeviceInfoSet);

        [DllImport("setupapi.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        private static extern bool SetupDiGetDeviceRegistryProperty(
            IntPtr DeviceInfoSet,
            ref SP_DEVINFO_DATA DeviceInfoData,
            uint Property,
            out uint PropertyRegDataType,
            IntPtr PropertyBuffer,
            uint PropertyBufferSize,
            out uint RequiredSize);

        // ── Public API ────────────────────────────────────────────────────────

        /// <summary>
        /// Enumerates input-class devices on the system that are wake-capable.
        /// Returns (DeviceId, FriendlyName, DeviceClass) for each.
        /// DeviceId is stable for the session and used as DeviceProfile.DeviceGuid.
        /// DeviceClass is the Windows Setup class name: "HIDClass", "Keyboard", "Mouse", etc.
        /// </summary>
        public IEnumerable<(string DeviceId, string Name, string DeviceClass)> EnumerateWakeCapableDevices()
        {
            var hDevs = SetupDiGetClassDevs(IntPtr.Zero, IntPtr.Zero, IntPtr.Zero,
                DIGCF_PRESENT | DIGCF_ALLCLASSES);

            if (hDevs == new IntPtr(-1))
                yield break;

            try
            {
                uint i = 0;
                while (true)
                {
                    var devData = new SP_DEVINFO_DATA
                    {
                        cbSize = (uint)Marshal.SizeOf<SP_DEVINFO_DATA>()
                    };

                    if (!SetupDiEnumDeviceInfo(hDevs, i++, ref devData))
                        break;

                    // Only devices with the WAKEUP capability bit set.
                    uint caps = GetDword(hDevs, ref devData, SPDRP_CAPABILITIES);
                    if ((caps & CM_DEVCAP_WAKEUP) == 0)
                        continue;

                    // Filter to input-class devices only (ignore storage, net, etc.)
                    string cls = GetString(hDevs, ref devData, SPDRP_CLASS) ?? string.Empty;
                    if (!IsInputClass(cls))
                        continue;

                    string name = GetString(hDevs, ref devData, SPDRP_DEVICEDESC) ?? "Unknown Wake Device";
                    yield return ($"WAKE_{devData.DevInst}", name, cls);
                }
            }
            finally
            {
                SetupDiDestroyDeviceInfoList(hDevs);
            }
        }

        // ── Helpers ───────────────────────────────────────────────────────────

        private static bool IsInputClass(string cls) =>
            cls.Equals("HIDClass",  StringComparison.OrdinalIgnoreCase) ||
            cls.Equals("Keyboard",  StringComparison.OrdinalIgnoreCase) ||
            cls.Equals("Mouse",     StringComparison.OrdinalIgnoreCase) ||
            cls.Equals("Bluetooth", StringComparison.OrdinalIgnoreCase) ||
            cls.Equals("USB",       StringComparison.OrdinalIgnoreCase);

        private static uint GetDword(IntPtr hDevs, ref SP_DEVINFO_DATA devData, uint prop)
        {
            IntPtr buf = Marshal.AllocHGlobal(4);
            try
            {
                return SetupDiGetDeviceRegistryProperty(hDevs, ref devData, prop,
                    out _, buf, 4, out _)
                    ? (uint)Marshal.ReadInt32(buf)
                    : 0u;
            }
            finally { Marshal.FreeHGlobal(buf); }
        }

        private static string? GetString(IntPtr hDevs, ref SP_DEVINFO_DATA devData, uint prop)
        {
            SetupDiGetDeviceRegistryProperty(hDevs, ref devData, prop,
                out _, IntPtr.Zero, 0, out uint needed);
            if (needed == 0) return null;

            IntPtr buf = Marshal.AllocHGlobal((int)needed);
            try
            {
                return SetupDiGetDeviceRegistryProperty(hDevs, ref devData, prop,
                    out _, buf, needed, out _)
                    ? Marshal.PtrToStringUni(buf)?.TrimEnd('\0')
                    : null;
            }
            finally { Marshal.FreeHGlobal(buf); }
        }
    }
}

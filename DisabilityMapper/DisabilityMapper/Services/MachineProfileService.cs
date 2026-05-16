using System;
using System.Collections.Generic;
using System.IO;
using System.Threading.Tasks;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using SharpDX.DirectInput;

namespace DisabilityMapper.Services
{
    /// <summary>
    /// Scans every HID device connected to this machine, writes machine_profile.json
    /// to the SARA root, and sends the profile to SARA CONTROL via BuceyShunt so it
    /// flows into the NBS narrative system.
    ///
    /// SARA uses this to know what's available for mapping — "you have a G13 and a
    /// HOTAS, here's what I mapped by default, say something to change it."
    /// </summary>
    public static class MachineProfileService
    {
        public static string ProfilePath(string saraRoot)
            => Path.Combine(saraRoot, "machine_profile.json");

        public static async Task ScanAndReportAsync(string saraRoot)
        {
            var profile = BuildProfile();
            var path = ProfilePath(saraRoot);

            // Write locally — always, even if CONTROL is offline
            File.WriteAllText(path, JsonConvert.SerializeObject(profile, Formatting.Indented));

            // Send to SARA CONTROL → routes to NBS narrative
            if (await BuceyShunt.IsAlive())
            {
                await BuceyShunt.Dispatch(
                    intent:  "input_device_profile",
                    act:     "00",
                    payload: JObject.FromObject(profile),
                    source:  "MAMA",
                    target:  "CONTROL"
                );
            }
        }

        private static object BuildProfile()
        {
            var devices = new List<object>();

            try
            {
                using var di = new DirectInput();

                // Game controllers, joysticks, HOTAS, gamepads
                foreach (var info in di.GetDevices(DeviceClass.GameControl, DeviceEnumerationFlags.AllDevices))
                    devices.Add(DeviceEntry(info));

                // Keyboards (includes G13, macro boards presenting as keyboards)
                foreach (var info in di.GetDevices(DeviceClass.Keyboard, DeviceEnumerationFlags.AllDevices))
                    devices.Add(DeviceEntry(info));

                // Pointer devices
                foreach (var info in di.GetDevices(DeviceClass.Pointer, DeviceEnumerationFlags.AllDevices))
                    devices.Add(DeviceEntry(info));
            }
            catch { /* DirectInput unavailable — profile will have empty devices list */ }

            return new
            {
                machine_id  = Environment.MachineName,
                os          = Environment.OSVersion.ToString(),
                scan_time   = DateTime.UtcNow.ToString("o"),
                device_count = devices.Count,
                devices
            };
        }

        private static object DeviceEntry(DeviceInstance info) => new
        {
            id       = info.InstanceGuid.ToString(),
            name     = info.ProductName?.Trim() ?? "Unknown",
            type     = info.Type.ToString().ToLowerInvariant(),
            subtype  = info.Subtype.ToString(),
            instance = info.InstanceName?.Trim() ?? ""
        };
    }
}

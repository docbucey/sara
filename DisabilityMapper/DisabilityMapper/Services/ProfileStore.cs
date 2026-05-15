using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Newtonsoft.Json;
using DisabilityMapper.Models;

namespace DisabilityMapper.Services
{
    /// <summary>
    /// Saves and loads DeviceProfile objects as JSON under
    /// %AppData%\DisabilityMapper\profiles\
    /// </summary>
    public class ProfileStore
    {
        private static readonly string ProfileDir = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
            "DisabilityMapper", "profiles");

        private readonly JsonSerializerSettings _settings = new()
        {
            Formatting = Formatting.Indented,
            NullValueHandling = NullValueHandling.Ignore
        };

        public ProfileStore()
        {
            Directory.CreateDirectory(ProfileDir);
        }

        public void Save(DeviceProfile profile)
        {
            var path = GetPath(profile.DeviceGuid, profile.ProfileName);
            File.WriteAllText(path, JsonConvert.SerializeObject(profile, _settings));
        }

        public DeviceProfile? Load(string deviceGuid)
        {
            var defaultPath = GetPath(deviceGuid, "Default");
            if (File.Exists(defaultPath))
                return JsonConvert.DeserializeObject<DeviceProfile>(File.ReadAllText(defaultPath), _settings);

            // Backward compatibility with old single-profile filename.
            var legacyPath = Path.Combine(ProfileDir, Uri.EscapeDataString(deviceGuid) + ".json");
            if (File.Exists(legacyPath))
            {
                var legacy = JsonConvert.DeserializeObject<DeviceProfile>(File.ReadAllText(legacyPath), _settings);
                if (legacy is not null && string.IsNullOrWhiteSpace(legacy.ProfileName))
                    legacy.ProfileName = "Default";
                return legacy;
            }

            return LoadAllForDevice(deviceGuid).FirstOrDefault();
        }

        public IEnumerable<DeviceProfile> LoadAll()
        {
            foreach (var file in Directory.EnumerateFiles(ProfileDir, "*.json"))
            {
                DeviceProfile? p = null;
                try
                {
                    p = JsonConvert.DeserializeObject<DeviceProfile>(
                            File.ReadAllText(file), _settings);
                }
                catch { /* skip corrupt files */ }

                if (p is not null)
                {
                    if (string.IsNullOrWhiteSpace(p.ProfileName))
                        p.ProfileName = "Default";
                    yield return p;
                }
            }
        }

        public IEnumerable<DeviceProfile> LoadAllForDevice(string deviceGuid)
        {
            var safeGuid = Uri.EscapeDataString(deviceGuid);
            var prefix = safeGuid + "__";

            foreach (var file in Directory.EnumerateFiles(ProfileDir, safeGuid + "*.json"))
            {
                var name = Path.GetFileName(file);
                if (!name.Equals(safeGuid + ".json", StringComparison.OrdinalIgnoreCase) &&
                    !name.StartsWith(prefix, StringComparison.OrdinalIgnoreCase))
                    continue;

                DeviceProfile? p = null;
                try
                {
                    p = JsonConvert.DeserializeObject<DeviceProfile>(File.ReadAllText(file), _settings);
                }
                catch { }

                if (p is not null)
                {
                    if (string.IsNullOrWhiteSpace(p.ProfileName))
                        p.ProfileName = "Default";
                    yield return p;
                }
            }
        }

        public void Delete(string deviceGuid)
        {
            var path = GetPath(deviceGuid, "Default");
            if (File.Exists(path)) File.Delete(path);

            var legacy = Path.Combine(ProfileDir, Uri.EscapeDataString(deviceGuid) + ".json");
            if (File.Exists(legacy)) File.Delete(legacy);
        }

        public void Delete(string deviceGuid, string profileName)
        {
            var path = GetPath(deviceGuid, profileName);
            if (File.Exists(path)) File.Delete(path);
        }

        private static string GetPath(string deviceGuid, string profileName)
        {
            var safeGuid = Uri.EscapeDataString(deviceGuid);
            var normalized = string.IsNullOrWhiteSpace(profileName) ? "Default" : profileName.Trim();

            // Keep default profile filename backward-compatible.
            if (normalized.Equals("Default", StringComparison.OrdinalIgnoreCase))
                return Path.Combine(ProfileDir, safeGuid + ".json");

            var safeProfile = Uri.EscapeDataString(normalized);
            return Path.Combine(ProfileDir, safeGuid + "__" + safeProfile + ".json");
        }
    }
}

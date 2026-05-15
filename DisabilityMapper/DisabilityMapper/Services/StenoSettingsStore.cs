using System;
using System.IO;
using Newtonsoft.Json;
using DisabilityMapper.Models;

namespace DisabilityMapper.Services
{
    /// <summary>
    /// Persists StenoSettings to %AppData%\DisabilityMapper\steno.json.
    /// </summary>
    public class StenoSettingsStore
    {
        private static readonly string FilePath = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
            "DisabilityMapper", "steno.json");

        private static readonly JsonSerializerSettings _json = new()
        {
            Formatting        = Formatting.Indented,
            NullValueHandling = NullValueHandling.Ignore
        };

        public StenoSettingsStore()
        {
            Directory.CreateDirectory(Path.GetDirectoryName(FilePath)!);
        }

        public StenoSettings Load()
        {
            if (!File.Exists(FilePath)) return new StenoSettings();
            try
            {
                return JsonConvert.DeserializeObject<StenoSettings>(
                           File.ReadAllText(FilePath), _json)
                       ?? new StenoSettings();
            }
            catch
            {
                return new StenoSettings();
            }
        }

        public void Save(StenoSettings settings)
        {
            File.WriteAllText(FilePath, JsonConvert.SerializeObject(settings, _json));
        }
    }
}

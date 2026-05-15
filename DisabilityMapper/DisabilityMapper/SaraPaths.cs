using System;
using System.IO;

namespace DisabilityMapper;

/// <summary>Resolves the SARA Python repo root (same rules as App startup).</summary>
public static class SaraPaths
{
    public static string ResolveSaraRoot()
    {
        return Environment.GetEnvironmentVariable("SARA_ROOT")
               ?? Path.Combine(
                   Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments),
                   "coding projects", "SARA");
    }

    public static string AssetsMetaPath => Path.Combine(ResolveSaraRoot(), "assets", "meta", "assets_meta.json");

    public static string AssetsPngDir => Path.Combine(ResolveSaraRoot(), "assets", "png");

    public static string IcoPath => Path.Combine(ResolveSaraRoot(), "assets", "ico", "sara.ico");
}

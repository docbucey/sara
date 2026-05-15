using System.Windows.Media;

namespace DisabilityMapper.Spec;

/// <summary>
/// PopCap-ish casual 2006 palette (no PNGs): distinct surfaces so controls are never same-on-same.
/// </summary>
public static class SaraCartoonTheme
{
    public static readonly SolidColorBrush Surface = Create("#FFF4F6FA");
    public static readonly SolidColorBrush SurfaceElevated = Create("#FFFFFFFF");
    public static readonly SolidColorBrush SurfaceMenu = Create("#FFEEF1F7");
    public static readonly SolidColorBrush SurfaceInput = Create("#FFFFFFFF");
    public static readonly SolidColorBrush Border = Create("#FFC9D1E0");
    public static readonly SolidColorBrush BorderStrong = Create("#FF9AA7BC");
    public static readonly SolidColorBrush TextPrimary = Create("#FF1B2433");
    public static readonly SolidColorBrush TextSecondary = Create("#FF4B5A73");
    public static readonly SolidColorBrush Accent = Create("#FF2F6FED");
    public static readonly SolidColorBrush AccentMuted = Create("#FFE8EFFF");
    public static readonly SolidColorBrush Outline = Create("#FF1B2433");
    public static readonly SolidColorBrush FieldGrass = Create("#FF6BCB59");
    public static readonly SolidColorBrush FieldLine = Create("#FFFFFFFF");
    public static readonly SolidColorBrush TargetRing = Create("#FFFFD54A");
    public static readonly SolidColorBrush PlasticBase = Create("#FFB0B7C4");

    private static SolidColorBrush Create(string hex)
    {
        var b = (SolidColorBrush)new BrushConverter().ConvertFromString(hex)!;
        b.Freeze();
        return b;
    }
}

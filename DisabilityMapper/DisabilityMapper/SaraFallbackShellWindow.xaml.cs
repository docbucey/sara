using System.Windows;

namespace DisabilityMapper;

/// <summary>
/// Vector fallback for MAMA / Mapper PNG spec (4:3, cartoon chrome, logical 0–10 layout).
/// No raster assets required. Wire ImageBrush later when PNGs exist.
/// </summary>
public partial class SaraFallbackShellWindow : Window
{
    private static SaraFallbackShellWindow? _instance;

    public SaraFallbackShellWindow()
    {
        InitializeComponent();
        Closed += (_, _) => _instance = null;
    }

    public static void Toggle()
    {
        if (_instance is { IsVisible: true })
        {
            _instance.Hide();
        }
        else
        {
            _instance ??= new SaraFallbackShellWindow();
            _instance.Show();
            _instance.Activate();
        }
    }
}

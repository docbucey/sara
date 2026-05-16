using System;
using System.Collections.ObjectModel;
using System.Diagnostics;
using System.IO;
using System.Net.Http;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using DisabilityMapper.Services;
using Newtonsoft.Json.Linq;

namespace DisabilityMapper;

public class AssetThumbItem
{
    public string FileName { get; }
    public string FullPath { get; }
    public bool Missing { get; private set; }
    public ImageSource? Preview { get; private set; }

    public Visibility ImageVisibility => Missing || Preview == null ? Visibility.Collapsed : Visibility.Visible;

    public Visibility MissingVisibility => Missing || Preview == null ? Visibility.Visible : Visibility.Collapsed;

    public AssetThumbItem(string fileName, string fullPath, bool missing)
    {
        FileName = fileName;
        FullPath = fullPath;
        Missing = missing;
        if (missing || !File.Exists(fullPath))
            return;
        try
        {
            var bi = new BitmapImage();
            bi.BeginInit();
            bi.CacheOption = BitmapCacheOption.OnLoad;
            bi.UriSource = new Uri(fullPath, UriKind.Absolute);
            bi.EndInit();
            bi.Freeze();
            Preview = bi;
        }
        catch
        {
            Missing = true;
        }
    }
}

public partial class AssetDeckWindow : Window
{
    private static readonly HttpClient Http = new() { Timeout = TimeSpan.FromSeconds(5) };

    private readonly ObservableCollection<AssetThumbItem> _thumbs = new();

    public AssetDeckWindow()
    {
        InitializeComponent();
        ThumbsList.ItemsSource = _thumbs;
        Loaded += async (_, _) =>
        {
            SaraRootText.Text = "SARA_ROOT: " + SaraPaths.ResolveSaraRoot();
            await RefreshHealthAsync();
            LoadThumbnails();
            CountText.Text = $"Items: {_thumbs.Count}";
            _ = PollHealthLoop();
        };
    }

    private async Task PollHealthLoop()
    {
        while (IsVisible)
        {
            await Task.Delay(3000);
            try
            {
                await Dispatcher.InvokeAsync(RefreshHealthAsync);
            }
            catch
            {
                break;
            }
        }
    }

    private async Task RefreshHealthAsync()
    {
        string msg;
        try
        {
            var r = await Http.GetAsync($"{BuceyShunt.BaseUrl}/health");
            var j = JObject.Parse(await r.Content.ReadAsStringAsync());
            var loaded = j.Value<bool?>("control_loaded") == true;
            if (loaded)
            {
                msg = "CONTROL HTTP: online (control_loaded=true)";
            }
            else
            {
                var err = j.Value<string>("control_load_error");
                msg = "CONTROL HTTP: UP but control_loaded=false.\n";
                if (!string.IsNullOrWhiteSpace(err))
                {
                    var clip = err.Length > 1200 ? err.Substring(0, 1200) + "..." : err;
                    msg += clip;
                }
                else
                {
                    msg += "No control_load_error in /health — see Python window running run_sara.";
                }
            }
        }
        catch (Exception ex)
        {
            msg = "CONTROL HTTP: offline — " + ex.Message;
        }

        await Dispatcher.InvokeAsync(() => { HealthText.Text = msg; });
    }

    private void LoadThumbnails()
    {
        _thumbs.Clear();
        var root = SaraPaths.ResolveSaraRoot();
        var metaPath = SaraPaths.AssetsMetaPath;
        if (!File.Exists(metaPath))
        {
            _thumbs.Add(new AssetThumbItem("assets_meta.json missing", metaPath, true));
            return;
        }

        try
        {
            var doc = JObject.Parse(File.ReadAllText(metaPath));
            var arr = doc["assets"] as JArray;
            if (arr == null)
            {
                _thumbs.Add(new AssetThumbItem("no assets[] in JSON", metaPath, true));
                return;
            }

            foreach (var row in arr)
            {
                var rel = row?["file"]?.ToString();
                if (string.IsNullOrWhiteSpace(rel))
                    continue;
                var full = Path.GetFullPath(Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar)));
                var name = Path.GetFileName(full);
                _thumbs.Add(new AssetThumbItem(name, full, !File.Exists(full)));
            }
        }
        catch (Exception ex)
        {
            _thumbs.Add(new AssetThumbItem("JSON error: " + ex.Message, metaPath, true));
        }
    }

    private void BtnMapper_OnClick(object sender, RoutedEventArgs e)
    {
        var mw = new MainWindow();
        mw.Show();
        mw.Activate();
    }

    private void BtnSpec_OnClick(object sender, RoutedEventArgs e) => SaraFallbackShellWindow.Toggle();

    private void BtnFolder_OnClick(object sender, RoutedEventArgs e)
    {
        var dir = SaraPaths.AssetsPngDir;
        if (Directory.Exists(dir))
        {
            Process.Start(new ProcessStartInfo { FileName = dir, UseShellExecute = true });
        }
        else
        {
            MessageBox.Show("Folder not found:\n" + dir, "SARA assets", MessageBoxButton.OK, MessageBoxImage.Information);
        }
    }

    private async void BtnRefresh_OnClick(object sender, RoutedEventArgs e)
    {
        await RefreshHealthAsync();
        LoadThumbnails();
        CountText.Text = $"Items: {_thumbs.Count}";
    }
}

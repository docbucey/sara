using System;
using System.Diagnostics;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Threading;
using DisabilityMapper.Services;

namespace DisabilityMapper;

public partial class App : Application
{
    private Process? _saraBackend;

    protected override void OnStartup(StartupEventArgs e)
    {
        base.OnStartup(e);
        StartSaraBackend();

        // Wait for CONTROL to be ready before opening any windows.
        // Poll /health until control_loaded == true (up to 15 seconds).
        Dispatcher.InvokeAsync(async () =>
        {
            bool ready = await WaitForControlAsync(timeoutSeconds: 15);
            if (!ready)
            {
                MessageBox.Show(
                    "SARA CONTROL did not start in time.\nCheck that Python is installed and the SARA folder is accessible.",
                    "SARA — Startup Error", MessageBoxButton.OK, MessageBoxImage.Warning);
            }
            new MainWindow().Show();
        });
    }

    protected override void OnExit(ExitEventArgs e)
    {
        StopSaraBackend();
        base.OnExit(e);
    }

    private void StartSaraBackend()
    {
        string saraRoot = SaraPaths.ResolveSaraRoot();
        string script = Path.Combine(saraRoot, "sara_control", "server_con.py");
        if (!File.Exists(script))
            return;

        string venvPython = Path.Combine(saraRoot, "venv", "Scripts", "python.exe");
        string python = File.Exists(venvPython) ? venvPython : "python";

        try
        {
            Process proc = Process.Start(new ProcessStartInfo
            {
                FileName = python,
                Arguments = $"\"{script}\" --http --host 127.0.0.1 --port 5050",
                WorkingDirectory = saraRoot,
                CreateNoWindow = true,
                UseShellExecute = false,
            }) ?? throw new InvalidOperationException("Process.Start returned null.");

            _saraBackend = proc;
        }
        catch
        {
        }
    }

    private static async Task<bool> WaitForControlAsync(int timeoutSeconds)
    {
        var deadline = DateTime.UtcNow.AddSeconds(timeoutSeconds);
        while (DateTime.UtcNow < deadline)
        {
            if (await BuceyShunt.IsAlive())
                return true;
            await Task.Delay(300);
        }
        return false;
    }

    private void StopSaraBackend()
    {
        if (_saraBackend is { HasExited: false })
        {
            try { _saraBackend.Kill(entireProcessTree: true); } catch { }
        }

        _saraBackend?.Dispose();
    }
}

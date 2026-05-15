using System;
using System.Diagnostics;
using System.IO;
using System.Windows;

namespace DisabilityMapper;

public partial class App : Application
{
    private Process? _saraBackend;

    protected override void OnStartup(StartupEventArgs e)
    {
        base.OnStartup(e);
        StartSaraBackend();
        new AssetDeckWindow().Show();
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

    private void StopSaraBackend()
    {
        if (_saraBackend is { HasExited: false })
        {
            try { _saraBackend.Kill(entireProcessTree: true); } catch { }
        }

        _saraBackend?.Dispose();
    }
}

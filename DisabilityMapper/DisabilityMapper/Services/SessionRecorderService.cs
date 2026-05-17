using System;
using System.Collections.Generic;
using System.IO;
using Newtonsoft.Json;

namespace DisabilityMapper.Services
{
    /// <summary>
    /// Records HID session telemetry as JSONL files under %AppData%\DisabilityMapper\sessions\.
    /// Each line written when a filtered event fires: { t, device, input, raw, filtered }.
    /// Thread-safe — raw and filtered callbacks may arrive from background poll threads.
    /// </summary>
    public sealed class SessionRecorderService : IDisposable
    {
        public static readonly string SessionDir = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
            "DisabilityMapper", "sessions");

        private StreamWriter?                    _writer;
        private readonly object                  _lock    = new();
        private readonly Dictionary<string, double> _lastRaw = new();
        private bool                             _recording;

        /// <summary>Full path of the active session file, or null when idle.</summary>
        public string? CurrentSessionPath { get; private set; }

        public SessionRecorderService()
        {
            Directory.CreateDirectory(SessionDir);
        }

        // ── Lifecycle ────────────────────────────────────────────────────────

        public void StartSession()
        {
            lock (_lock)
            {
                if (_recording) StopLocked();
                var fileName = $"session_{DateTime.Now:yyyyMMdd_HHmmss}.jsonl";
                CurrentSessionPath = Path.Combine(SessionDir, fileName);
                _writer = new StreamWriter(CurrentSessionPath, append: false) { AutoFlush = true };
                _lastRaw.Clear();
                _recording = true;
            }
        }

        public void StopSession()
        {
            lock (_lock) StopLocked();
        }

        private void StopLocked()
        {
            _recording = false;
            _writer?.Dispose();
            _writer = null;
        }

        // ── Event receivers ──────────────────────────────────────────────────

        /// <summary>Call on every raw HidEvent — caches last raw value per input.</summary>
        public void OnRawEvent(HidEvent e)
        {
            lock (_lock)
                _lastRaw[e.InputName] = e.Value;
        }

        /// <summary>
        /// Call on every filtered HidEvent — writes one JSONL line pairing
        /// the filtered value with the last-known raw value for the same input.
        /// </summary>
        public void OnFilteredEvent(HidEvent e)
        {
            lock (_lock)
            {
                if (!_recording || _writer is null) return;
                var rawVal = _lastRaw.TryGetValue(e.InputName, out var r) ? r : e.Value;
                _writer.WriteLine(JsonConvert.SerializeObject(new
                {
                    t        = e.Timestamp.ToString("O"),
                    device   = e.DeviceId,
                    role     = e.Role.ToString(),
                    input    = e.InputName,
                    raw      = Math.Round(rawVal,    4),
                    filtered = Math.Round(e.Value,   4)
                }));
            }
        }

        public void Dispose() => StopSession();
    }
}

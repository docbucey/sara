using System;
using System.Collections.ObjectModel;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using DisabilityMapper.Models;
using DisabilityMapper.Services;

namespace DisabilityMapper.ViewModels
{
    public partial class MainViewModel : ObservableObject
    {
        private readonly ProfileStore           _store;
        private readonly HidService              _hid;
        private readonly VirtualDeviceService    _vds = new();
        private readonly SessionRecorderService  _recorder = new();
        private readonly GlobalHookService       _hook = new();

        [ObservableProperty] private DeviceProfileViewModel? _selectedDevice;
        [ObservableProperty] private bool _isPolling;
        [ObservableProperty] private string _statusText = "Starting up…";
        [ObservableProperty] private bool _saraConnected;
        [ObservableProperty] private bool _isConsoleBridgeActive;
        [ObservableProperty] private string _consoleBridgeStatus = "Console Bridge: off";

        // Signal monitor — raw vs filtered live display
        [ObservableProperty] private string _signalInputName = "—";
        [ObservableProperty] private double _rawSignalValue;
        [ObservableProperty] private double _filteredSignalValue;

        // Session recorder
        [ObservableProperty] private bool   _isSessionRecording;
        [ObservableProperty] private string _sessionFilePath = string.Empty;

        // WFH global tremor filter
        [ObservableProperty] private bool   _isWfhFilterActive;
        [ObservableProperty] private string _wfhFilterStatus = "WFH Filter: off";

        // PT/OT prescription + session history
        [ObservableProperty] private string _prescribedSport = string.Empty;
        public ObservableCollection<string> SessionFiles { get; } = new();

        // Raised when PT/OT changes the prescribed sport so MainWindow can push it to Patient Console
        public event Action<string>? PrescribedSportChanged;

        partial void OnPrescribedSportChanged(string value) =>
            PrescribedSportChanged?.Invoke(value);

        public ObservableCollection<DeviceProfileViewModel> Devices { get; } = new();

        // ── Steno keyboard ────────────────────────────────────────────────────

        public StenoKeyboardViewModel StenoVm { get; } = new();

        /// <summary>
        /// Raised (on the UI thread) when a StenoToggle mapping fires.
        /// MainWindow subscribes and calls StenoKeyboardWindow.Toggle().
        /// </summary>
        public event Action? StenoToggleRequested;

        public MainViewModel()
        {
            _store = new ProfileStore();
            _hid   = new HidService(_store);

            _ = CheckSaraAsync();

            _hid.DeviceConnected += (g, n) =>
                System.Windows.Application.Current.Dispatcher.Invoke(() =>
                {
                    var d = Devices.FirstOrDefault(x =>
                        x.Guid.Equals(g, System.StringComparison.OrdinalIgnoreCase));
                    if (d is not null)
                    {
                        d.IsConnected = true;
                        StatusText = $"✓ Reconnected: {n}";
                    }
                    else
                    {
                        // Auto-register virtual devices (Touchscreen, Pen) that appear at runtime.
                        var type = g.StartsWith("VIRTUAL_") ? g.Replace("VIRTUAL_", string.Empty)
                                 : g.StartsWith("WAKE_")    ? "Wake"
                                 : string.Empty;
                        if (!string.IsNullOrEmpty(type))
                        {
                            var profile = _store.Load(g) ?? new DeviceProfile
                            {
                                DeviceGuid = g,
                                DeviceName = n,
                                DeviceType = type,
                                CanWake    = type == "Wake"
                            };
                            Devices.Add(new DeviceProfileViewModel(profile, _store));
                        }
                        StatusText = $"Connected: {n}";
                    }
                });
            _hid.DeviceDisconnected += g =>
                System.Windows.Application.Current.Dispatcher.Invoke(() =>
                {
                    var d = Devices.FirstOrDefault(x =>
                        x.Guid.Equals(g, System.StringComparison.OrdinalIgnoreCase));
                    if (d is not null) { d.IsConnected = false; StatusText = $"⚠ Disconnected: {d.DeviceName}"; }
                });

            // Wire StenoToggle from any HID mapping → raise event for MainWindow
            _hid.StenoToggleCallback = () =>
                System.Windows.Application.Current.Dispatcher.Invoke(
                    () => StenoToggleRequested?.Invoke());

            // Wire steno chord output → inject keystrokes into the OS focused window
            StenoVm.TextReady += text => _hid.InjectRaw(text);

            // Route raw input events to device live monitors and Learn mode
            _hid.RawInputDetected += (deviceId, inputLabel) =>
                System.Windows.Application.Current.Dispatcher.Invoke(() =>
                {
                    // Universal learn: the first active learner on ANY device captures this input.
                    // This lets the user press a button on any device to fill a mapping,
                    // regardless of which device's profile panel is open.
                    foreach (var d in Devices)
                    {
                        if (d.ActiveLearnerRow != null)
                        {
                            d.FillAndClearLearner(inputLabel);
                            break; // only one learner at a time
                        }
                    }

                    // Per-device last-input monitor
                    foreach (var d in Devices)
                    {
                        if (d.Guid.Equals(deviceId, System.StringComparison.OrdinalIgnoreCase))
                        {
                            d.OnRawInput(inputLabel);
                            break;
                        }
                    }
                });

            _hid.RawHidEvent += e =>
                System.Windows.Application.Current.Dispatcher.Invoke(() =>
                {
                    SignalInputName = e.InputName;
                    RawSignalValue  = Math.Abs(e.Value);
                });

            _hid.FilteredHidEvent += e =>
                System.Windows.Application.Current.Dispatcher.Invoke(() =>
                    FilteredSignalValue = Math.Abs(e.Value));

            // Session telemetry — background thread safe, no dispatcher needed
            _hid.RawHidEvent      += e => _recorder.OnRawEvent(e);
            _hid.FilteredHidEvent += e => _recorder.OnFilteredEvent(e);

            LoadSavedProfiles();
        }

        // ── Commands ─────────────────────────────────────────────────────────

        [RelayCommand]
        private void RefreshDevices()
        {
            var live = _hid.EnumerateDevices().ToList();

            // Add newly found devices
            foreach (var (guid, name, type) in live)
            {
                if (Devices.Any(d => d.Guid == guid)) continue;
                var profile = _store.Load(guid) ?? new DeviceProfile
                {
                    DeviceGuid = guid,
                    DeviceName = name,
                    DeviceType = type,
                    ProfileName = "Default"
                };
                Devices.Add(new DeviceProfileViewModel(profile, _store));

                // If mapping is already active, wire the new device immediately
                // (guards inside StartDevice prevent duplicate watchers)
                if (IsPolling && profile.IsEnabled)
                    _hid.StartDevice(profile);
            }

            StatusText = live.Count == 0
                ? "No HID devices found."
                : $"Found {live.Count} device(s).";
        }

        [RelayCommand]
        private void TogglePolling()
        {
            if (IsPolling)
            {
                _hid.StopPolling();
                _recorder.StopSession();
                IsPolling          = false;
                IsSessionRecording = false;
                SessionFilePath    = string.Empty;
                StatusText         = "Mapping stopped.";
            }
            else
            {
                _hid.StartPolling();
                _recorder.StartSession();
                IsPolling          = true;
                IsSessionRecording = true;
                SessionFilePath    = _recorder.CurrentSessionPath ?? string.Empty;
                StatusText         = "Mapping active.";
            }
        }

        [RelayCommand]
        private void SaveAll()
        {
            foreach (var d in Devices)
                d.Save();
            StatusText = "All profiles saved.";
        }

        [RelayCommand]
        private void ToggleConsoleBridge()
        {
            if (IsConsoleBridgeActive)
            {
                _vds.Disconnect();
                _hid.SetVirtualDevice(null);
                IsConsoleBridgeActive = false;
                ConsoleBridgeStatus   = "Console Bridge: off";
                StatusText            = "Console Bridge stopped.";
            }
            else
            {
                if (_vds.TryConnect(out var msg))
                {
                    _hid.SetVirtualDevice(_vds);
                    IsConsoleBridgeActive = true;
                    ConsoleBridgeStatus   = msg;
                    StatusText            = "Console Bridge active — device appears as Xbox 360 controller";
                }
                else
                {
                    ConsoleBridgeStatus = msg;
                    StatusText          = $"⚠ {msg}";
                }
            }
        }

        [RelayCommand]
        private void ToggleWfhFilter()
        {
            if (IsWfhFilterActive)
            {
                _hook.Stop();
                IsWfhFilterActive = false;
                WfhFilterStatus   = "WFH Filter: off";
                StatusText        = "WFH tremor filter stopped.";
            }
            else
            {
                _hook.Start();
                IsWfhFilterActive = true;
                WfhFilterStatus   = $"KB debounce {_hook.DebounceMs} ms  ·  Mouse dead-zone {_hook.MouseDeadZone} px";
                StatusText        = $"WFH tremor filter active — KB {_hook.DebounceMs} ms · Mouse ±{_hook.MouseDeadZone} px";
            }
        }

        // ── PT/OT session management ───────────────────────────────────────

        /// <summary>Activate Console Bridge + session recording for a patient game session.</summary>
        public void StartPatientSession(string sport, string team, string opp)
        {
            // Ensure Console Bridge is on
            if (!IsConsoleBridgeActive)
                ToggleConsoleBridgeCommand.Execute(null);

            // Ensure mapping is running
            if (!IsPolling)
                TogglePollingCommand.Execute(null);

            StatusText = $"Session: {sport.Trim()} — {team} vs {opp}";
        }

        /// <summary>Stop the patient session (Console Bridge + recording).</summary>
        public void StopPatientSession()
        {
            if (IsConsoleBridgeActive)
                ToggleConsoleBridgeCommand.Execute(null);

            if (IsPolling)
                TogglePollingCommand.Execute(null);

            StatusText = "Session ended.";
            RefreshSessionFilesCommand.Execute(null);
        }

        [RelayCommand]
        private void RefreshSessionFiles()
        {
            SessionFiles.Clear();
            var dir = SessionRecorderService.SessionDir;
            if (!Directory.Exists(dir)) return;

            foreach (var f in Directory.GetFiles(dir, "*.jsonl")
                                       .OrderByDescending(x => x))
            {
                SessionFiles.Add(Path.GetFileName(f));
            }
        }
        // ── Raw Input bridge (called from MainWindow WndProc hook) ─────────────

        public void OnWindowLoaded(IntPtr hwnd) => _hid.RegisterRawInput(hwnd);
        public void OnRawInput(IntPtr lParam)   => _hid.ProcessRawInput(lParam);

        /// <summary>Called by MainWindow.Closed — unhooks global hooks cleanly.</summary>
        public void Shutdown()
        {
            _hook.Dispose();
            _recorder.Dispose();
        }
        /// <summary>
        /// Forward WM_POINTER*, WM_POINTERDOWN, WM_POINTERUP from the WndProc hook
        /// so touch/pen contacts reach the mapping pipeline.
        /// </summary>
        public void OnPointerInput(int msg, IntPtr wParam)
        {
            _hid.ProcessPointerMessage(msg, wParam);
        }        // ── SARA — raw Bucey Shunt ───────────────────────────────────────────

        private async Task CheckSaraAsync()
        {
            SaraConnected = await BuceyShunt.IsAlive();
            StatusText = SaraConnected ? "SARA ready." : "SARA offline — run launch_sara.bat";
        }

        // ── Init ─────────────────────────────────────────────────────────────

        private void LoadSavedProfiles()
        {
            foreach (var profile in _store.LoadAll()
                         .GroupBy(p => p.DeviceGuid, StringComparer.OrdinalIgnoreCase)
                         .Select(g => g.First()))
            {
                Devices.Add(new DeviceProfileViewModel(profile, _store));
            }
        }

    }
}

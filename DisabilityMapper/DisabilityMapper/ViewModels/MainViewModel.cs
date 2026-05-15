using System;
using System.Collections.ObjectModel;
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
        private readonly ProfileStore _store;
        private readonly HidService   _hid;

        [ObservableProperty] private DeviceProfileViewModel? _selectedDevice;
        [ObservableProperty] private bool _isPolling;
        [ObservableProperty] private string _statusText = "Starting up…";
        [ObservableProperty] private bool _saraConnected;

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
                IsPolling  = false;
                StatusText = "Mapping stopped.";
            }
            else
            {
                _hid.StartPolling();
                IsPolling  = true;
                StatusText = "Mapping active.";
            }
        }

        [RelayCommand]
        private void SaveAll()
        {
            foreach (var d in Devices)
                d.Save();
            StatusText = "All profiles saved.";
        }
        // ── Raw Input bridge (called from MainWindow WndProc hook) ─────────────

        public void OnWindowLoaded(IntPtr hwnd) => _hid.RegisterRawInput(hwnd);
        public void OnRawInput(IntPtr lParam)   => _hid.ProcessRawInput(lParam);
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

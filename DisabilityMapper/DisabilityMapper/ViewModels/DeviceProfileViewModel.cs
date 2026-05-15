using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using DisabilityMapper.Models;
using DisabilityMapper.Services;
using InputSimulatorStandard.Native;

namespace DisabilityMapper.ViewModels
{
    public partial class DeviceProfileViewModel : ObservableObject
    {
        private readonly ProfileStore _store;
        private readonly Dictionary<string, DeviceProfile> _profilesByName =
            new(StringComparer.OrdinalIgnoreCase);

        private DeviceProfile _model;
        private InputMappingRowViewModel? _learningRow;

        public string Guid => _model.DeviceGuid;
        public string DeviceType => _model.DeviceType;
        public bool   CanWake    => _model.CanWake;

        [ObservableProperty] private string _deviceName = string.Empty;
        [ObservableProperty] private bool _isEnabled;

        [ObservableProperty] private bool _tremorEnabled;
        [ObservableProperty] private int _debounceMs;
        [ObservableProperty] private double _axisDeadZone;
        [ObservableProperty] private double _axisSmoothAlpha;

        [ObservableProperty] private string _lastInput = "-";
        [ObservableProperty] private bool _isConnected = true;

        [ObservableProperty] private string _selectedProfileName = "Default";
        [ObservableProperty] private InputMappingRowViewModel? _selectedMappingRow;

        public ObservableCollection<string> ProfileNames { get; } = new();
        public ObservableCollection<InputMappingRowViewModel> MappingRows { get; } = new();

        public DeviceProfileViewModel(DeviceProfile model, ProfileStore store)
        {
            _store = store;
            _model = model;

            LoadProfiles(model);
            ApplyModelToEditableState(_model);
            RebuildMappingRows();
        }

        private void LoadProfiles(DeviceProfile bootstrap)
        {
            _profilesByName.Clear();
            ProfileNames.Clear();

            var all = _store.LoadAllForDevice(bootstrap.DeviceGuid).ToList();
            if (all.Count == 0)
                all.Add(bootstrap);

            foreach (var p in all)
            {
                if (string.IsNullOrWhiteSpace(p.ProfileName))
                    p.ProfileName = "Default";

                _profilesByName[p.ProfileName] = p;
            }

            foreach (var name in _profilesByName.Keys.OrderBy(x => x))
                ProfileNames.Add(name);

            if (!_profilesByName.ContainsKey(bootstrap.ProfileName))
                bootstrap.ProfileName = "Default";

            SelectedProfileName = bootstrap.ProfileName;
            _model = _profilesByName[SelectedProfileName];
        }

        partial void OnSelectedProfileNameChanged(string value)
        {
            if (!_profilesByName.TryGetValue(value, out var p)) return;
            _model = p;
            ApplyModelToEditableState(p);
            RebuildMappingRows();
        }

        [RelayCommand]
        private void AddProfile()
        {
            var baseName = "Profile";
            var index = 1;
            var name = baseName + index;
            while (_profilesByName.ContainsKey(name))
            {
                index++;
                name = baseName + index;
            }

            var clone = new DeviceProfile
            {
                DeviceGuid = Guid,
                DeviceName = DeviceName,
                DeviceType = DeviceType,
                ProfileName = name,
                IsEnabled = IsEnabled,
                TremorFilter = new TremorFilterSettings
                {
                    IsEnabled = TremorEnabled,
                    DebounceMs = DebounceMs,
                    AxisDeadZone = AxisDeadZone,
                    AxisSmoothAlpha = AxisSmoothAlpha
                },
                Mappings = MappingRows
                    .Where(r => r.HasMapping())
                    .Select(r => r.ToModel())
                    .ToList()
            };

            _profilesByName[name] = clone;
            ProfileNames.Add(name);
            SelectedProfileName = name;
        }

        [RelayCommand]
        private void RemoveCurrentProfile()
        {
            if (ProfileNames.Count <= 1) return;
            var toRemove = SelectedProfileName;
            if (toRemove.Equals("Default", StringComparison.OrdinalIgnoreCase)) return;

            _profilesByName.Remove(toRemove);
            ProfileNames.Remove(toRemove);
            _store.Delete(Guid, toRemove);

            SelectedProfileName = ProfileNames.FirstOrDefault() ?? "Default";
        }

        private void ApplyModelToEditableState(DeviceProfile p)
        {
            DeviceName = p.DeviceName;
            IsEnabled = p.IsEnabled;
            TremorEnabled = p.TremorFilter.IsEnabled;
            DebounceMs = p.TremorFilter.DebounceMs;
            AxisDeadZone = p.TremorFilter.AxisDeadZone;
            AxisSmoothAlpha = p.TremorFilter.AxisSmoothAlpha;
        }

        private void RebuildMappingRows()
        {
            MappingRows.Clear();

            var bySource = _model.Mappings
                .Where(m => !string.IsNullOrWhiteSpace(m.SourceInput))
                .ToDictionary(m => m.SourceInput, StringComparer.OrdinalIgnoreCase);

            // Build a full, stable list of inputs for this device type.
            foreach (var input in BuildKnownInputs(DeviceType))
            {
                var row = new InputMappingRowViewModel(input)
                {
                    LearnRequested  = StartLearnForRow,
                    DeleteRequested = RemoveMappingRow,
                    EditRequested   = SelectMappingRow
                };

                if (bySource.TryGetValue(input, out var mapping))
                    row.Apply(mapping);

                MappingRows.Add(row);
            }

            if (CanWake)
            {
                foreach (var wakeInput in new[] { "Wake.PowerButton", "Wake.Keyboard", "Wake.Mouse" })
                {
                    if (MappingRows.Any(r => r.InputName.Equals(wakeInput, StringComparison.OrdinalIgnoreCase)))
                        continue;

                    var row = new InputMappingRowViewModel(wakeInput)
                    {
                        LearnRequested  = StartLearnForRow,
                        DeleteRequested = RemoveMappingRow,
                        EditRequested   = SelectMappingRow
                    };
                    if (bySource.TryGetValue(wakeInput, out var wakeMapping))
                        row.Apply(wakeMapping);

                    MappingRows.Add(row);
                }
            }

            // Keep custom/legacy mappings visible even if not in the current catalog.
            foreach (var mapping in _model.Mappings)
            {
                if (string.IsNullOrWhiteSpace(mapping.SourceInput)) continue;
                if (MappingRows.Any(r => r.InputName.Equals(mapping.SourceInput, StringComparison.OrdinalIgnoreCase)))
                    continue;

                var row = new InputMappingRowViewModel(mapping.SourceInput)
                {
                    LearnRequested  = StartLearnForRow,
                    DeleteRequested = RemoveMappingRow,
                    EditRequested   = SelectMappingRow
                };
                row.Apply(mapping);
                MappingRows.Add(row);
            }

            SelectedMappingRow = MappingRows.FirstOrDefault();
        }

        private void RemoveMappingRow(InputMappingRowViewModel row)
        {
            row.ClearMappingCommand.Execute(null);
        }

        private void SelectMappingRow(InputMappingRowViewModel row)
        {
            SelectedMappingRow = row;
        }

        /// <summary>
        /// Adds a blank row and immediately arms it for Learn so the user can
        /// press / move any input to capture it, then fill in the action.
        /// </summary>
        [RelayCommand]
        private void AddMapping()
        {
            // Static table mode: there is always a full list of rows.
            // Keep command as a no-op for compatibility with existing bindings.
            if (SelectedMappingRow is not null)
                StartLearnForRow(SelectedMappingRow);
        }

        private void StartLearnForRow(InputMappingRowViewModel row)
        {
            if (_learningRow is not null)
                _learningRow.StopLearning();

            _learningRow = row;
        }

        public InputMappingRowViewModel? ActiveLearnerRow => _learningRow;

        public void FillAndClearLearner(string inputLabel)
        {
            if (_learningRow is null) return;

            // In static-table mode we never rewrite the table shape or row identity.
            // Learn only marks completion on the row that was armed.
            if (string.IsNullOrWhiteSpace(_learningRow.Label))
                _learningRow.Label = _learningRow.InputName;

            _learningRow.StopLearning();
            _learningRow = null;
        }

        public void OnRawInput(string inputLabel)
        {
            LastInput = inputLabel;

            foreach (var row in MappingRows)
                row.IsActiveNow = row.InputName.Equals(inputLabel, StringComparison.OrdinalIgnoreCase);

            if (_learningRow is not null)
                FillAndClearLearner(inputLabel);
        }

        private static IEnumerable<string> BuildKnownInputs(string deviceType)
        {
            if (deviceType.Equals("Keyboard", StringComparison.OrdinalIgnoreCase))
            {
                foreach (VirtualKeyCode vk in Enum.GetValues(typeof(VirtualKeyCode)))
                    yield return $"Key_{vk}";
                yield break;
            }

            if (deviceType.Equals("Mouse", StringComparison.OrdinalIgnoreCase))
            {
                yield return "Mouse.Left";
                yield return "Mouse.Right";
                yield return "Mouse.Middle";
                yield return "Mouse.XButton1";
                yield return "Mouse.XButton2";

                yield return "Mouse.X";
                yield return "Mouse.X+";
                yield return "Mouse.X-";
                yield return "Mouse.Y";
                yield return "Mouse.Y+";
                yield return "Mouse.Y-";

                yield return "Mouse.ScrollV";
                yield return "Mouse.ScrollV+";
                yield return "Mouse.ScrollV-";
                yield return "Mouse.ScrollH";
                yield return "Mouse.ScrollH+";
                yield return "Mouse.ScrollH-";
                yield break;
            }

            if (deviceType.Equals("Touchscreen", StringComparison.OrdinalIgnoreCase) ||
                deviceType.Equals("Pen", StringComparison.OrdinalIgnoreCase))
            {
                for (int i = 1; i <= 10; i++)
                {
                    yield return $"Contact{i}_Down";
                    yield return $"Contact{i}_Up";
                }

                yield return "Gesture_Tap";
                yield return "Gesture_Hold";
                yield return "Gesture_Swipe_North";
                yield return "Gesture_Swipe_South";
                yield return "Gesture_Swipe_East";
                yield return "Gesture_Swipe_West";
                yield break;
            }

            if (deviceType.Equals("Wake", StringComparison.OrdinalIgnoreCase))
            {
                yield return "Wake.PowerButton";
                yield return "Wake.Keyboard";
                yield return "Wake.Mouse";
                yield break;
            }

            // Gamepads / joysticks / throttles / HOTAS
            for (int i = 0; i < 128; i++)
                yield return $"Button{i}";

            foreach (var axis in new[] { "Axis_X", "Axis_Y", "Axis_Z", "Axis_RX", "Axis_RY", "Axis_RZ" })
            {
                yield return axis;
                yield return axis + "+";
                yield return axis + "-";
            }

            for (int i = 0; i < 2; i++)
            {
                yield return $"Slider{i}";
                yield return $"Slider{i}+";
                yield return $"Slider{i}-";
            }

            for (int hat = 0; hat < 4; hat++)
            {
                yield return $"Hat{hat}_Up";
                yield return $"Hat{hat}_Right";
                yield return $"Hat{hat}_Down";
                yield return $"Hat{hat}_Left";
            }
        }

        public void Save()
        {
            _model.DeviceName = DeviceName;
            _model.IsEnabled = IsEnabled;
            _model.ProfileName = SelectedProfileName;
            _model.TremorFilter.IsEnabled = TremorEnabled;
            _model.TremorFilter.DebounceMs = DebounceMs;
            _model.TremorFilter.AxisDeadZone = AxisDeadZone;
            _model.TremorFilter.AxisSmoothAlpha = AxisSmoothAlpha;

            _model.Mappings = MappingRows
                .Where(r => r.HasMapping())
                .Select(r => r.ToModel())
                .ToList();

            _profilesByName[SelectedProfileName] = _model;

            foreach (var p in _profilesByName.Values)
                _store.Save(p);
        }
    }
}

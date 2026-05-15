using System;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using InputSimulatorStandard.Native;
using DisabilityMapper.Models;

namespace DisabilityMapper.ViewModels
{
    public partial class ButtonMappingViewModel : ObservableObject
    {
        public string Id { get; }

        [ObservableProperty] private string _label;
        [ObservableProperty] private string _sourceInput;

        // Action
        [ObservableProperty] private string _actionType;
        [ObservableProperty] private string _actionValue;
        [ObservableProperty] private string _macroText;
        [ObservableProperty] private int    _macroDelayMs;
        [ObservableProperty] private int    _macroJitterMs;
        [ObservableProperty] private bool   _holdMode;
        [ObservableProperty] private bool   _isLearning;

        /// <summary>Non-empty when this mapping has a configuration problem; bound to the red error banner.</summary>
        [ObservableProperty] private string _validationError = string.Empty;

        /// <summary>
        /// Set by DeviceProfileViewModel so StartLearnCommand can delegate
        /// coordination without ButtonMappingViewModel knowing about HID services.
        /// </summary>
        public Action? LearnRequested { get; set; }

        public string[] ActionTypes { get; } =
            { "KeyPress", "MouseClick", "MouseMove", "MacroText", "Command", "StenoToggle" };

        [RelayCommand]
        private void StartLearn()
        {
            IsLearning = true;
            LearnRequested?.Invoke();
        }

        /// <summary>Called by DeviceProfileViewModel once a raw input is captured.</summary>
        public void StopLearning() => IsLearning = false;

        // ── Validation ────────────────────────────────────────────────────────

        partial void OnSourceInputChanged(string value)  => Revalidate();
        partial void OnActionTypeChanged(string value)   => Revalidate();
        partial void OnActionValueChanged(string value)  => Revalidate();

        private void Revalidate()
        {
            if (string.IsNullOrWhiteSpace(SourceInput))
            {
                ValidationError = "⚠  Source Input is required — use the Learn button or type a label (e.g. Button0, Axis_X+).";
                return;
            }

            if (ActionType == "KeyPress")
            {
                if (string.IsNullOrWhiteSpace(ActionValue))
                {
                    ValidationError = "⚠  Key name is required for KeyPress (e.g. VK_A, SPACE, RETURN).";
                    return;
                }
                if (!Enum.TryParse<VirtualKeyCode>(ActionValue, ignoreCase: true, out _))
                {
                    ValidationError = $"⚠  \"{ActionValue}\" is not a recognised VirtualKeyCode. Check spelling (e.g. VK_A, SPACE, RETURN, LCONTROL).";
                    return;
                }
            }

            if (ActionType == "MouseClick")
            {
                var v = ActionValue?.Trim() ?? string.Empty;
                if (!v.Equals("Left",   StringComparison.OrdinalIgnoreCase) &&
                    !v.Equals("Right",  StringComparison.OrdinalIgnoreCase) &&
                    !v.Equals("Middle", StringComparison.OrdinalIgnoreCase))
                {
                    ValidationError = "⚠  Mouse button value must be Left, Right, or Middle.";
                    return;
                }
            }

            ValidationError = string.Empty;
        }

        public ButtonMappingViewModel(ButtonMapping model)
        {
            Id             = model.Id;
            _label         = model.Label;
            _sourceInput   = model.SourceInput;
            _actionType    = model.Action.Type;
            _actionValue   = model.Action.Value;
            _macroText     = model.Action.MacroText;
            _macroDelayMs  = model.Action.MacroDelayMs;
            _macroJitterMs = model.Action.MacroJitterMs;
            _holdMode      = model.Action.HoldMode;

            Revalidate();
        }

        public ButtonMapping ToModel() => new()
        {
            Id          = Id,
            Label       = Label,
            SourceInput = SourceInput,
            Action      = new MappingAction
            {
                Type          = ActionType,
                Value         = ActionValue,
                MacroText     = MacroText,
                MacroDelayMs  = MacroDelayMs,
                MacroJitterMs = MacroJitterMs,
                HoldMode      = HoldMode
            }
        };
    }
}

using System;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using DisabilityMapper.Models;

namespace DisabilityMapper.ViewModels
{
    public partial class InputMappingRowViewModel : ObservableObject
    {
        [ObservableProperty] private string _inputName;
        [ObservableProperty] private string _label;

        [ObservableProperty] private string _actionType;
        [ObservableProperty] private string _actionValue;
        [ObservableProperty] private string _macroText;
        [ObservableProperty] private int _macroDelayMs;
        [ObservableProperty] private int _macroJitterMs;
        [ObservableProperty] private bool _holdMode;

        [ObservableProperty] private bool _isLearning;
        [ObservableProperty] private bool _isActiveNow;

        public Action<InputMappingRowViewModel>? LearnRequested  { get; set; }
        public Action<InputMappingRowViewModel>? DeleteRequested { get; set; }
        public Action<InputMappingRowViewModel>? EditRequested   { get; set; }

        public string[] ActionTypes { get; } =
            { "KeyPress", "MouseClick", "MouseMove", "MacroText", "Command", "StenoToggle" };

        public InputMappingRowViewModel(string inputName)
        {
            _inputName  = inputName;
            _label      = inputName;
            _actionType = "KeyPress";
            _actionValue   = string.Empty;
            _macroText     = string.Empty;
            _macroDelayMs  = 0;
            _macroJitterMs = 0;
            _holdMode      = false;
        }

        public string CurrentMapping
        {
            get
            {
                if (!HasMapping()) return "Not Set";

                if (ActionType == "MacroText")
                {
                    var text = string.IsNullOrWhiteSpace(MacroText) ? "(empty)" : MacroText;
                    return $"Type text: {text}";
                }

                var value = string.IsNullOrWhiteSpace(ActionValue) ? "(none)" : ActionValue;
                var hold = HoldMode ? " [Hold]" : string.Empty;
                return $"{ActionType}: {value}{hold}";
            }
        }

        partial void OnActionTypeChanged(string value) { OnPropertyChanged(nameof(CurrentMapping)); OnPropertyChanged(nameof(IsMapped)); }
        partial void OnActionValueChanged(string value) { OnPropertyChanged(nameof(CurrentMapping)); OnPropertyChanged(nameof(IsMapped)); }
        partial void OnMacroTextChanged(string value) { OnPropertyChanged(nameof(CurrentMapping)); OnPropertyChanged(nameof(IsMapped)); }
        partial void OnHoldModeChanged(bool value) => OnPropertyChanged(nameof(CurrentMapping));

        /// <summary>Used by VALANCE tile template to color-code mapped vs unmapped buttons.</summary>
        public bool IsMapped => HasMapping();

        public void Apply(ButtonMapping mapping)
        {
            Label         = string.IsNullOrWhiteSpace(mapping.Label) ? InputName : mapping.Label;
            ActionType    = mapping.Action.Type;
            ActionValue   = mapping.Action.Value;
            MacroText     = mapping.Action.MacroText;
            MacroDelayMs  = mapping.Action.MacroDelayMs;
            MacroJitterMs = mapping.Action.MacroJitterMs;
            HoldMode      = mapping.Action.HoldMode;
        }

        public bool HasMapping()
        {
            return !string.IsNullOrWhiteSpace(ActionType) &&
                   (!string.IsNullOrWhiteSpace(ActionValue) ||
                    !string.IsNullOrWhiteSpace(MacroText)   ||
                    ActionType == "StenoToggle");
        }

        public ButtonMapping ToModel()
        {
            return new ButtonMapping
            {
                Label       = string.IsNullOrWhiteSpace(Label) ? InputName : Label,
                SourceInput = InputName,
                Action = new MappingAction
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

        [RelayCommand]
        private void LearnInput()
        {
            IsLearning = true;
            LearnRequested?.Invoke(this);
        }

        [RelayCommand]
        private void DeleteMapping() => DeleteRequested?.Invoke(this);

        [RelayCommand]
        private void EditMapping() => EditRequested?.Invoke(this);

        [RelayCommand]
        private void ClearMapping()
        {
            ActionType    = "KeyPress";
            ActionValue   = string.Empty;
            MacroText     = string.Empty;
            MacroDelayMs  = 0;
            MacroJitterMs = 0;
            HoldMode      = false;
            Label         = InputName;
            OnPropertyChanged(nameof(CurrentMapping));
        }

        public void StopLearning() => IsLearning = false;
    }
}

using System;
using System.Collections.ObjectModel;
using System.IO;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using DisabilityMapper.Services;

namespace DisabilityMapper.ViewModels
{
    public partial class StenoKeyboardViewModel : ObservableObject
    {
        private readonly StenoChordEngine _engine = new();

        [ObservableProperty] private string _chordPreview  = string.Empty;
        [ObservableProperty] private string _outputBuffer  = string.Empty;
        [ObservableProperty] private bool   _isAlwaysOnTop = true;
        [ObservableProperty] private int    _autoFireMs    = 0;

        /// <summary>
        /// Raised whenever text should be injected into the OS focus window.
        /// MacroEngine handles the actual keystrokes; wired externally.
        /// </summary>
        public event Action<string>? TextReady;

        /// <summary>Raised by Fire() so code-behind can un-check all ToggleButtons.</summary>
        public event Action? AllKeysReleased;

        public StenoKeyboardViewModel()
        {
            _engine.ChordChanged += chord => ChordPreview = chord;
            _engine.TextReady    += OnTextReady;
        }

        // ── Key state ─────────────────────────────────────────────────────────

        public bool IsKeyLatched(string keyId) => _engine.IsLatched(keyId);

        public void ToggleKey(string keyId) => _engine.ToggleKey(keyId);

        // ── Commands ──────────────────────────────────────────────────────────

        [RelayCommand]
        private void FireChord()
        {
            _engine.Fire();
            AllKeysReleased?.Invoke();
        }

        [RelayCommand]
        private void Backspace()
        {
            _engine.ClearLatch();
            AllKeysReleased?.Invoke();

            if (OutputBuffer.Length == 0) return;

            // Remove last space-delimited word from the display buffer
            var buf = OutputBuffer.TrimEnd();
            var lastSpace = buf.LastIndexOf(' ');
            OutputBuffer = lastSpace >= 0 ? buf[..(lastSpace + 1)] : string.Empty;

            TextReady?.Invoke("\b \b");
        }

        [RelayCommand]
        private void ClearOutput()
        {
            _engine.ClearLatch();
            AllKeysReleased?.Invoke();
            OutputBuffer = string.Empty;
        }

        [RelayCommand]
        private void ToggleAlwaysOnTop() => IsAlwaysOnTop = !IsAlwaysOnTop;

        // ── Direct Type commands ───────────────────────────────────────────

        /// <summary>Inject a single printable character directly (Direct Type mode).</summary>
        [RelayCommand]
        private void TypeChar(string? ch)
        {
            if (string.IsNullOrEmpty(ch)) return;
            OutputBuffer += ch;
            TextReady?.Invoke(ch);
        }

        [RelayCommand] private void TypeSpace()     { OutputBuffer += ' '; TextReady?.Invoke(" "); }
        [RelayCommand] private void TypeTab()        => TextReady?.Invoke("\t");
        [RelayCommand] private void TypeEnter()      => TextReady?.Invoke("\n");
        [RelayCommand] private void DirectBackspace()
        {
            if (OutputBuffer.Length > 0)
                OutputBuffer = OutputBuffer[..^1];
            TextReady?.Invoke("\b");
        }

        partial void OnAutoFireMsChanged(int value) => _engine.SetAutoFire(value);

        // ── Dictionary import ─────────────────────────────────────────────────

        [ObservableProperty] private string _dictionaryPath   = string.Empty;
        [ObservableProperty] private string _dictionaryStatus = "No dictionary loaded — using built-in briefs.";

        [RelayCommand]
        private void ImportDictionary()
        {
            var dlg = new Microsoft.Win32.OpenFileDialog
            {
                Title            = "Open Plover Dictionary",
                Filter           = "Plover JSON (*.json)|*.json|All files (*.*)|*.*",
                DefaultExt       = ".json",
                CheckFileExists  = true,
            };

            if (dlg.ShowDialog() != true) return;

            DictionaryPath = dlg.FileName;
            try
            {
                var count = _engine.LoadDictionary(DictionaryPath);
                DictionaryStatus = $"✓ Loaded {count:N0} entries from {Path.GetFileName(DictionaryPath)}";
            }
            catch (Exception ex)
            {
                DictionaryStatus = $"⚠ Failed: {ex.Message}";
            }
        }

        // ── Internal ─────────────────────────────────────────────────────────

        private void OnTextReady(string text)
        {
            OutputBuffer += text;
            TextReady?.Invoke(text);
        }
    }
}

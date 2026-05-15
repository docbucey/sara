using System;
using System.Collections.Generic;
using System.Linq;
using System.Windows;
using System.Windows.Controls.Primitives;
using DisabilityMapper.Services;
using DisabilityMapper.Models;
using DisabilityMapper.ViewModels;

namespace DisabilityMapper
{
    public partial class StenoKeyboardWindow : Window
    {
        private readonly StenoKeyboardViewModel _vm;
        private readonly StenoSettingsStore _store = new();

        // All ToggleButtons in the steno grid, grouped by key tag for sync
        private List<ToggleButton> _allKeys = new();
        private bool _suppressSync;

        // ── Singleton instance management ────────────────────────────────────

        private static StenoKeyboardWindow? _instance;

        public static StenoKeyboardWindow GetOrCreate(StenoKeyboardViewModel vm)
        {
            if (_instance is null || !_instance.IsLoaded)
                _instance = new StenoKeyboardWindow(vm);
            return _instance;
        }

        public static void Toggle(StenoKeyboardViewModel vm)
        {
            var w = GetOrCreate(vm);
            if (w.IsVisible) w.Hide();
            else             w.Show();
        }

        // ── Constructor ───────────────────────────────────────────────────────

        public StenoKeyboardWindow(StenoKeyboardViewModel vm)
        {
            InitializeComponent();
            _vm = vm;
            DataContext = vm;

            // Apply persisted settings
            var s = _store.Load();
            vm.IsAlwaysOnTop = s.AlwaysOnTop;
            vm.AutoFireMs    = s.AutoFireMs;
            if (!double.IsNaN(s.WindowLeft) && !double.IsNaN(s.WindowTop))
            {
                WindowStartupLocation = WindowStartupLocation.Manual;
                Left = s.WindowLeft;
                Top  = s.WindowTop;
            }

            // Subscribe to AllKeysReleased so all ToggleButtons are visually cleared
            vm.AllKeysReleased += UncheckAll;

            // Collect all ToggleButtons after XAML is inflated
            Loaded += (_, _) => CollectKeys();

            // Enter fires chord (keyboard shortcut)
            KeyDown += (_, e) =>
            {
                if (e.Key == System.Windows.Input.Key.Return)
                    vm.FireChordCommand.Execute(null);
            };

            // Close hides, does not destroy — save settings first
            Closing += (_, e) =>
            {
                SaveSettings();
                e.Cancel = true;
                Hide();
            };
        }

        private void SaveSettings()
        {
            _store.Save(new StenoSettings
            {
                AlwaysOnTop = _vm.IsAlwaysOnTop,
                AutoFireMs  = _vm.AutoFireMs,
                WindowLeft  = Left,
                WindowTop   = Top
            });
        }

        // ── Toggle button events ──────────────────────────────────────────────

        private void StenoKey_Checked(object sender, RoutedEventArgs e)
        {
            if (_suppressSync) return;
            var tb  = (ToggleButton)sender;
            var key = (string)tb.Tag;

            _vm.ToggleKey(key);

            // Sync all buttons that share the same key tag (e.g. both S keys)
            SyncSiblings(key, true);
        }

        private void StenoKey_Unchecked(object sender, RoutedEventArgs e)
        {
            if (_suppressSync) return;
            var tb  = (ToggleButton)sender;
            var key = (string)tb.Tag;

            _vm.ToggleKey(key);   // ToggleKey toggles; since we just unchecked, toggle back to off
            // Re-read the engine's actual state and sync visuals
            SyncSiblings(key, _vm.IsKeyLatched(key));
        }

        // ── Helpers ───────────────────────────────────────────────────────────

        private void CollectKeys()
        {
            _allKeys = FindVisualChildren<ToggleButton>(this).ToList();
        }

        private void SyncSiblings(string keyTag, bool isChecked)
        {
            _suppressSync = true;
            foreach (var tb in _allKeys.Where(t => (string)t.Tag == keyTag))
                tb.IsChecked = isChecked;
            _suppressSync = false;
        }

        private void UncheckAll()
        {
            _suppressSync = true;
            foreach (var tb in _allKeys)
                tb.IsChecked = false;
            _suppressSync = false;
        }

        private static IEnumerable<T> FindVisualChildren<T>(DependencyObject parent)
            where T : DependencyObject
        {
            if (parent is null) yield break;
            for (int i = 0; i < System.Windows.Media.VisualTreeHelper.GetChildrenCount(parent); i++)
            {
                var child = System.Windows.Media.VisualTreeHelper.GetChild(parent, i);
                if (child is T t) yield return t;
                foreach (var d in FindVisualChildren<T>(child))
                    yield return d;
            }
        }
    }
}

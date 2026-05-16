using System;
using System.Windows;
using System.Windows.Interop;
using DisabilityMapper.Services;
using DisabilityMapper.ViewModels;

namespace DisabilityMapper;

public partial class MainWindow : Window
{
    public MainWindow()
    {
        InitializeComponent();
        var vm = new MainViewModel();
        DataContext = vm;

        // Show/hide steno window whenever a StenoToggle mapping fires
        vm.StenoToggleRequested += () =>
            StenoKeyboardWindow.Toggle(vm.StenoVm);

        // Push prescribed sport changes to the Patient Console if it's open
        vm.PrescribedSportChanged += sport =>
            _patientConsole?.UpdatePrescribedSport(sport);

        Closed += (_, _) => vm.Shutdown();

        Loaded += OnWindowLoaded;
    }

    private void OnWindowLoaded(object sender, RoutedEventArgs e)
    {
        var vm   = (MainViewModel)DataContext;
        var hwnd = new WindowInteropHelper(this).Handle;

        // Register Raw Input (keyboard + mouse) and hook into WPF message pump
        vm.OnWindowLoaded(hwnd);
        HwndSource.FromHwnd(hwnd)?.AddHook(WndProc);

        // Auto-discover all attached devices and start input monitoring immediately
        vm.RefreshDevicesCommand.Execute(null);
        if (!vm.IsPolling)
            vm.TogglePollingCommand.Execute(null);
    }

    private IntPtr WndProc(IntPtr hwnd, int msg, IntPtr wParam, IntPtr lParam, ref bool handled)
    {
        var vm = (MainViewModel)DataContext;

        if (msg == RawInputService.WM_INPUT)
            vm.OnRawInput(lParam);
        else if (msg is TouchService.WM_POINTERDOWN
                     or TouchService.WM_POINTERUP
                     or TouchService.WM_POINTERUPDATE)
            vm.OnPointerInput(msg, wParam);

        return IntPtr.Zero;
    }

    private void OpenOffice_Click(object sender, RoutedEventArgs e)
    {
        OfficeSuiteWindow.Toggle();
    }

    private PatientConsoleWindow? _patientConsole;

    private void OpenPatientConsole_Click(object sender, RoutedEventArgs e)
    {
        var vm = (MainViewModel)DataContext;

        if (_patientConsole is { IsVisible: true })
        {
            _patientConsole.Activate();
            return;
        }

        _patientConsole = new PatientConsoleWindow(vm, vm.PrescribedSport);
        _patientConsole.Closed += (_, _) => _patientConsole = null;
        _patientConsole.Show();
    }

    /// <summary>
    /// Called when the PT/OT changes PrescribedSport in VALANCE while the
    /// Patient Console is already open.
    /// </summary>
    internal void UpdatePatientConsoleSport(string sport)
    {
        _patientConsole?.UpdatePrescribedSport(sport);
    }

    private void OpenSaraFallbackUi_Click(object sender, RoutedEventArgs e)
    {
        SaraFallbackShellWindow.Toggle();
    }
}
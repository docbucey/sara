using System.Windows;
using DisabilityMapper.ViewModels;

namespace DisabilityMapper;

public partial class PatientConsoleWindow : Window
{
    private readonly PatientConsoleViewModel _vm;
    private WindowState _prevState = WindowState.Normal;
    private WindowStyle _prevStyle = WindowStyle.SingleBorderWindow;

    public PatientConsoleWindow(MainViewModel mainVm, string? prescribedSport = null)
    {
        InitializeComponent();

        _vm = new PatientConsoleViewModel();
        DataContext = _vm;

        // Pre-select sport if PT/OT has prescribed one
        if (!string.IsNullOrWhiteSpace(prescribedSport))
            _vm.PrescribeSport(prescribedSport);

        // Wire patient events → MainViewModel actions
        _vm.PlayRequested += (sport, team, opp) =>
        {
            mainVm.StartPatientSession(sport, team, opp);
        };

        _vm.StopRequested += () =>
        {
            mainVm.StopPatientSession();
        };
    }

    /// <summary>Update the prescribed sport while the window is open (PT/OT changes it).</summary>
    public void UpdatePrescribedSport(string sport) => _vm.PrescribeSport(sport);

    private void ToggleFullscreen_Click(object sender, RoutedEventArgs e)
    {
        if (WindowStyle == WindowStyle.None)
        {
            WindowStyle = _prevStyle;
            WindowState = _prevState;
            BtnFullscreen.Content = "⤢  Full Screen";
        }
        else
        {
            _prevStyle = WindowStyle;
            _prevState = WindowState;
            WindowStyle = WindowStyle.None;
            WindowState = WindowState.Maximized;
            BtnFullscreen.Content = "⤡  Exit Full Screen";
        }
    }
}

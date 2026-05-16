using System;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;

namespace DisabilityMapper.ViewModels
{
    public partial class PatientConsoleViewModel : ObservableObject
    {
        // ── Catalogs ──────────────────────────────────────────────────────────
        // Instance properties for XAML {Binding} — backed by private static arrays.

        private static readonly string[] s_sports =
        {
            "🏈  Football",            "🏀  Basketball",
            "⚾  Baseball / Softball",  "⚽  Soccer",
            "🎾  Tennis",               "⛳  Golf",
            "🏃  Track & Field",        "🏊  Swimming",
            "🏐  Volleyball"
        };

        private static readonly string[] s_teams =
        {
            "Alabama",          "Arkansas",        "Auburn",          "Austin Peay",
            "Florida",          "Georgia",         "Kentucky",        "LSU",
            "Mississippi State","Missouri",        "Murray State",    "Oklahoma",
            "Ole Miss",         "South Carolina",  "Tennessee",       "Texas",
            "Texas A&M",        "Vanderbilt"
        };

        public string[] Sports => s_sports;
        public string[] Teams  => s_teams;

        // ── Observable state ──────────────────────────────────────────────────

        [ObservableProperty] private string? _selectedSport;
        [ObservableProperty] private string? _patientTeam;
        [ObservableProperty] private string? _opponentTeam;
        [ObservableProperty] private bool    _isPlaying;

        /// <summary>Inverse of IsPlaying — bound in XAML for visibility switching.</summary>
        public bool IsNotPlaying          => !IsPlaying;
        public bool IsPatientTeamSelected => PatientTeam  is not null;
        public bool IsOpponentTeamSelected => OpponentTeam is not null;

        partial void OnSelectedSportChanged(string? value)  => PlayCommand.NotifyCanExecuteChanged();
        partial void OnPatientTeamChanged(string? value)
        {
            PlayCommand.NotifyCanExecuteChanged();
            OnPropertyChanged(nameof(IsPatientTeamSelected));
        }
        partial void OnOpponentTeamChanged(string? value)
        {
            PlayCommand.NotifyCanExecuteChanged();
            OnPropertyChanged(nameof(IsOpponentTeamSelected));
        }
        partial void OnIsPlayingChanged(bool value)
        {
            OnPropertyChanged(nameof(IsNotPlaying));
            PlayCommand.NotifyCanExecuteChanged();
        }

        // ── Events ────────────────────────────────────────────────────────────

        /// <summary>Fired when the patient hits Play. Args: sport, patientTeam, opponentTeam.</summary>
        public event Action<string, string, string>? PlayRequested;

        /// <summary>Fired when the session is stopped.</summary>
        public event Action? StopRequested;

        // ── Commands ──────────────────────────────────────────────────────────

        private bool CanPlay() =>
            SelectedSport is not null &&
            PatientTeam   is not null &&
            OpponentTeam  is not null &&
            !IsPlaying;

        [RelayCommand(CanExecute = nameof(CanPlay))]
        private void Play()
        {
            IsPlaying = true;
            PlayRequested?.Invoke(SelectedSport!, PatientTeam!, OpponentTeam!);
        }

        [RelayCommand]
        private void Stop()
        {
            IsPlaying = false;
            StopRequested?.Invoke();
        }

        // ── PT/OT prescription ────────────────────────────────────────────────

        /// <summary>
        /// Called by VALANCE PT/OT panel to pre-select a sport.
        /// Matches by substring so "Football" matches "🏈  Football".
        /// </summary>
        public void PrescribeSport(string sport)
        {
            if (string.IsNullOrWhiteSpace(sport)) return;
            var match = Array.Find(s_sports,
                s => s.Contains(sport, StringComparison.OrdinalIgnoreCase));
            if (match is not null) SelectedSport = match;
        }
    }
}

namespace DisabilityMapper.Models
{
    /// <summary>
    /// Global settings for the stenography virtual keyboard.
    /// Stored alongside profiles in %AppData%\DisabilityMapper\settings.json
    /// </summary>
    public class StenoSettings
    {
        public bool   IsEnabled      { get; set; } = false;
        public bool   AlwaysOnTop    { get; set; } = true;
        /// <summary>
        /// Source input ID (e.g. "Button3") on ANY device that has a mapping
        /// with Action.Type == "StenoToggle".  Kept here for reference display.
        /// The actual binding lives in the device's ButtonMapping list.
        /// </summary>
        public string PttSourceLabel { get; set; } = "Not assigned";
        /// <summary>Saved window position. NaN = centre on primary screen.</summary>
        public double WindowLeft     { get; set; } = double.NaN;
        public double WindowTop      { get; set; } = double.NaN;
        /// <summary>
        /// Auto-fire the chord after this many ms with no new key activity.
        /// 0 = manual fire only (user presses ⏎ Send).
        /// </summary>
        public int    AutoFireMs     { get; set; } = 0;
    }
}

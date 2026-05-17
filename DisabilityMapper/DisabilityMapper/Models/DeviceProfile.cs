using System.Collections.Generic;

namespace DisabilityMapper.Models
{
    /// <summary>
    /// Role assigned to a physical device for a session.
    /// Patient  — the person receiving therapy; input drives virtual controller output.
    /// Operator — PT/OT team member; input feeds the prescription/assist pipeline.
    /// Personal — developer / WFH user device (never travels to field).
    /// </summary>
    public enum DeviceRole
    {
        Unassigned,
        Patient,
        Operator,
        Personal
    }

    /// <summary>
    /// Top-level profile stored per physical device.
    /// Persisted to %AppData%\DisabilityMapper\profiles\{DeviceGuid}.json
    /// </summary>
    public class DeviceProfile
    {
        public string DeviceGuid     { get; set; } = string.Empty;
        public string DeviceName     { get; set; } = string.Empty;
        /// <summary>Gamepad | Joystick | Mouse | Keyboard | Touchscreen | Pen | Wake</summary>
        public string DeviceType     { get; set; } = "Unknown";
        public string ProfileName    { get; set; } = "Default";
        public bool   IsEnabled      { get; set; } = true;
        /// <summary>True when SetupAPI reports CM_DEVCAP_WAKEUP for this device.</summary>
        public bool   CanWake        { get; set; } = false;
        /// <summary>
        /// Who is using this device.  Persisted so the same stick is remembered
        /// across sessions (e.g. the patient stick is always Patient on the field RPi).
        /// </summary>
        public DeviceRole Role       { get; set; } = DeviceRole.Unassigned;

        // ── DirectInput capability snapshot (populated on first connect) ──────
        /// <summary>Actual button count reported by DirectInput. 0 = not yet detected (falls back to 128).</summary>
        public int    JoystickButtonCount { get; set; } = 0;
        /// <summary>Actual POV hat count reported by DirectInput. 0 = not yet detected (falls back to 4).</summary>
        public int    JoystickPovCount    { get; set; } = 0;
        /// <summary>Comma-separated axis names actually present (e.g. "X,Y,Z,RZ,Slider0"). Empty = use all defaults.</summary>
        public string JoystickAxes        { get; set; } = string.Empty;

        public TremorFilterSettings  TremorFilter { get; set; } = new();
        public List<ButtonMapping>   Mappings     { get; set; } = new();
    }

    public class TremorFilterSettings
    {
        public bool   IsEnabled         { get; set; } = false;
        /// <summary>Minimum milliseconds a button/axis must be held before it is accepted.</summary>
        public int    DebounceMs        { get; set; } = 80;
        /// <summary>Dead-zone radius for axes (0-1.0). Axis values inside this radius are zeroed.</summary>
        public double AxisDeadZone      { get; set; } = 0.12;
        /// <summary>Low-pass smoothing factor α for axis values (0-1.0, lower = more smoothing).</summary>
        public double AxisSmoothAlpha   { get; set; } = 0.25;
    }

    public class ButtonMapping
    {
        public string Id            { get; set; } = System.Guid.NewGuid().ToString();
        public string Label         { get; set; } = string.Empty;
        /// <summary>Source: "Button0", "Axis_X+", "Axis_X-", "Hat0_Up", "Key_A", etc.</summary>
        public string SourceInput   { get; set; } = string.Empty;
        public MappingAction Action { get; set; } = new();
    }

    public class MappingAction
    {
        /// <summary>KeyPress | MacroText | MouseClick | MouseMove | Command</summary>
        public string Type          { get; set; } = "KeyPress";
        /// <summary>Key name (e.g. "LeftControl") or mouse button ("Left","Right","Middle").</summary>
        public string Value         { get; set; } = string.Empty;
        /// <summary>For MacroText: the full text block to type out.</summary>
        public string MacroText     { get; set; } = string.Empty;
        /// <summary>Delay in ms between each character/key in a macro. 0 = no delay (natural typing adds jitter).</summary>
        public int    MacroDelayMs  { get; set; } = 0;
        /// <summary>Natural jitter ± added to MacroDelayMs to simulate realistic typing rhythm.</summary>
        public int    MacroJitterMs { get; set; } = 0;
        /// <summary>Whether to hold the mapped key/button while the source is held.</summary>
        public bool   HoldMode      { get; set; } = false;
    }
}

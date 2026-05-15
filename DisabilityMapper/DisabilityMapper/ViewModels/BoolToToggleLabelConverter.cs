using System;
using System.Globalization;
using System.Windows.Data;

namespace DisabilityMapper.ViewModels
{
    /// <summary>
    /// Converts bool IsPolling → toolbar button label.
    /// </summary>
    [ValueConversion(typeof(bool), typeof(string))]
    public class BoolToToggleLabelConverter : IValueConverter
    {
        public static readonly BoolToToggleLabelConverter Instance = new();

        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
            => value is true ? "⏹  Stop Mapping" : "▶  Start Mapping";

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
            => throw new NotSupportedException();
    }
}

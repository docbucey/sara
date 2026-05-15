using System;
using System.Globalization;
using System.Windows.Data;

namespace DisabilityMapper.ViewModels
{
    /// <summary>Returns true when the bound string is non-null and non-empty.</summary>
    [ValueConversion(typeof(string), typeof(bool))]
    public sealed class StringNotEmptyConverter : IValueConverter
    {
        public static readonly StringNotEmptyConverter Instance = new();

        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
            => value is string s && s.Length > 0;

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
            => throw new NotSupportedException();
    }
}

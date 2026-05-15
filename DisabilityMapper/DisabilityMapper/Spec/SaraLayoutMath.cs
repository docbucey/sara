using System;
using System.Windows;

namespace DisabilityMapper.Spec;

/// <summary>
/// Per-asset logical space 0..10 on X and Y (step 0.01 in authoring).
/// Pixel mapping: px = x/10*W, py = y/10*H for that asset's master W×H.
/// </summary>
public static class SaraLayoutMath
{
    public static double Lx(double x, double totalW) => Clamp10(x) / 10.0 * totalW;

    public static double Ly(double y, double totalH) => Clamp10(y) / 10.0 * totalH;

    public static Rect ToRect(double x0, double y0, double x1, double y1, double w, double h)
    {
        var left = Lx(Math.Min(x0, x1), w);
        var top = Ly(Math.Min(y0, y1), h);
        var right = Lx(Math.Max(x0, x1), w);
        var bottom = Ly(Math.Max(y0, y1), h);
        return new Rect(left, top, Math.Max(0, right - left), Math.Max(0, bottom - top));
    }

    public static Thickness MarginFromSafeRect(double x0, double y0, double x1, double y1, double w, double h)
    {
        var left = Lx(x0, w);
        var top = Ly(y0, h);
        var right = w - Lx(x1, w);
        var bottom = h - Ly(y1, h);
        return new Thickness(left, top, right, bottom);
    }

    private static double Clamp10(double v) => Math.Clamp(v, 0.0, 10.0);
}

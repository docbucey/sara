"""
Layer 1: Power & Roots
"""

def pow(self, x, y):
    """
    Compute x raised to the power of y.
    Uses the formula: x^y = exp(y * ln(x)).
    """
    if x <= 0:
        if x == 0 and y > 0:
            return 0.0
        return None
    ln_x = self.ln(x)
    if ln_x is None:
        return None
    return self.exp(y * ln_x)

def sqrt(self, x, iterations=10):
    """
    Compute the square root of x using the Newton-Raphson method.
    """
    if x < 0:
        return None
    if x == 0:
        return 0.0
    guess = x / 2.0
    for _ in range(iterations):
        if guess == 0:
            break
        guess = 0.5 * (guess + x / guess)
    return guess

def nth_root(self, x, n, iterations=20):
    """
    Compute the nth root of x using the Newton-Raphson method.
    """
    if n == 0:
        return None
    if x < 0 and n % 2 == 0:
        return None
    y = x / n if x != 0 else 0.0
    if y == 0:
        y = 1.0
    for _ in range(iterations):
        if y == 0:
            break
        y = ((n - 1) * y + x / (y ** (n - 1))) / n
    return y

def poly_eval(self, coeffs, x):
    """
    Evaluate polynomial with coefficients [a0, a1, ..., an] at x:
    P(x) = a0 + a1*x + a2*x^2 + ...
    Uses Horner's method.
    """
    result = 0.0
    for c in reversed(coeffs):
        result = self.add(self.mul(result, x), c)
    return result
"""
Layer 2: Calculus Operations
"""

def second_derivative(self, f, x, h=1e-5):
    """
    Approximate f''(x) using central finite differences:
    f''(x) ≈ (f(x+h) - 2f(x) + f(x-h)) / h^2
    """
    fxh = f(self.add(x, h))
    fx = f(x)
    fxmh = f(self.sub(x, h))

    num = self.add(self.sub(fxh, self.mul(2.0, fx)), fxmh)
    den = self.mul(h, h)
    return self.div(num, den)

def gradient(self, f, point, h=1e-5):
    """
    Compute gradient of f at a point (vector).
    f: function that takes a vector and returns scalar.
    """
    grad = []
    for i in range(len(point)):
        p_plus = point[:]
        p_minus = point[:]
        p_plus[i] = self.add(p_plus[i], h)
        p_minus[i] = self.sub(p_minus[i], h)

        diff = self.sub(f(p_plus), f(p_minus))
        grad.append(self.div(diff, self.mul(2.0, h)))
    return grad

def divergence(self, F, point, h=1e-5):
    """
    Compute the divergence of a vector field F at a given point.
    F: vector field function returning [Fx, Fy, Fz] (or higher dimensions).
    point: the point (vector) at which to compute the divergence.
    h: step size for finite differences.
    """
    div = 0.0
    for i in range(len(point)):
        def Fi_plus(p):
            return F(p)[i]

        p_plus = point[:]
        p_minus = point[:]
        p_plus[i] = self.add(p_plus[i], h)
        p_minus[i] = self.sub(p_minus[i], h)

        diff = self.sub(Fi_plus(p_plus), Fi_plus(p_minus))
        div = self.add(div, self.div(diff, self.mul(2.0, h)))
    return div

def curl(self, F, point, h=1e-5):
    """
    Compute the curl of a 3D vector field F at a given point.
    F: vector field function returning [Fx, Fy, Fz].
    point: the point (vector) at which to compute the curl.
    h: step size for finite differences.
    """
    def partial(f_i, var_index):
        p_plus = point[:]
        p_minus = point[:]
        p_plus[var_index] = self.add(p_plus[var_index], h)
        p_minus[var_index] = self.sub(p_minus[var_index], h)
        return self.div(self.sub(f_i(p_plus), f_i(p_minus)), self.mul(2.0, h))

    Fx = lambda p: F(p)[0]
    Fy = lambda p: F(p)[1]
    Fz = lambda p: F(p)[2]

    curl_x = self.sub(partial(Fz, 1), partial(Fy, 2))
    curl_y = self.sub(partial(Fx, 2), partial(Fz, 0))
    curl_z = self.sub(partial(Fy, 0), partial(Fx, 1))

    return [curl_x, curl_y, curl_z]

def laplacian(self, f, point, h=1e-5):
    """
    Compute the Laplacian of a scalar function f at a given point.
    ∇²f = sum of second partial derivatives.
    f: scalar function that takes a vector and returns a scalar.
    point: the point (vector) at which to compute the Laplacian.
    h: step size for finite differences.
    """
    lap = 0.0
    for i in range(len(point)):
        p_plus = point[:]
        p_minus = point[:]
        p_plus[i] = self.add(p_plus[i], h)
        p_minus[i] = self.sub(p_minus[i], h)

        f_plus = f(p_plus)
        f_minus = f(p_minus)
        f_center = f(point)

        num = self.add(self.sub(f_plus, self.mul(2.0, f_center)), f_minus)
        lap = self.add(lap, self.div(num, self.mul(h, h)))
    return lap

def integrate_simpson(self, f, a, b, steps=1000):
    """
    Approximate the integral of f(x) from a to b using Simpson's Rule.
    f: function to integrate.
    a: lower limit of integration.
    b: upper limit of integration.
    steps: number of intervals (must be even; adjusted if odd).
    """
    if steps % 2 == 1:
        steps += 1  # Simpson's Rule requires an even number of intervals

    h = self.div(self.sub(b, a), steps)
    total = self.add(f(a), f(b))

    for i in range(1, steps):
        x = self.add(a, self.mul(i, h))
        weight = 4 if i % 2 == 1 else 2
        total = self.add(total, self.mul(weight, f(x)))

    return self.mul(total, self.div(h, 3.0))

def ode_euler(self, f, y0, t0, t1, steps=1000):
    """
    Solve an ordinary differential equation (ODE) using the Euler method.
    f: function representing dy/dt = f(t, y).
    y0: initial value of y at t = t0.
    t0: initial time.
    t1: final time.
    steps: number of steps to divide the interval [t0, t1].
    """
    h = self.div(self.sub(t1, t0), steps)
    y = y0
    t = t0
    for _ in range(steps):
        y = self.add(y, self.mul(h, f(t, y)))
        t = self.add(t, h)
    return y

def ode_rk2(self, f, y0, t0, t1, steps=1000):
    """
    Solve an ordinary differential equation (ODE) using the RK2 (midpoint) method.
    f: function representing dy/dt = f(t, y).
    y0: initial value of y at t = t0.
    t0: initial time.
    t1: final time.
    steps: number of steps to divide the interval [t0, t1].
    """
    h = self.div(self.sub(t1, t0), steps)
    y = y0
    t = t0
    for _ in range(steps):
        k1 = f(t, y)
        k2 = f(self.add(t, self.div(h, 2)), self.add(y, self.mul(self.div(h, 2), k1)))
        y = self.add(y, self.mul(h, k2))
        t = self.add(t, h)
    return y

def ode_rk4(self, f, y0, t0, t1, steps=1000):
    """
    Solve an ordinary differential equation (ODE) using the RK4 (Runge-Kutta 4th order) method.
    f: function representing dy/dt = f(t, y).
    y0: initial value of y at t = t0.
    t0: initial time.
    t1: final time.
    steps: number of steps to divide the interval [t0, t1].
    """
    h = self.div(self.sub(t1, t0), steps)
    y = y0
    t = t0
    for _ in range(steps):
        k1 = f(t, y)
        k2 = f(self.add(t, self.div(h, 2)), self.add(y, self.mul(self.div(h, 2), k1)))
        k3 = f(self.add(t, self.div(h, 2)), self.add(y, self.mul(self.div(h, 2), k2)))
        k4 = f(self.add(t, h), self.add(y, self.mul(h, k3)))

        incr = self.mul(self.div(h, 6), self.add(self.add(k1, self.mul(2, k2)), self.add(self.mul(2, k3), k4)))
        y = self.add(y, incr)
        t = self.add(t, h)
    return y
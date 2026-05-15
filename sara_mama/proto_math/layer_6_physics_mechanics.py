"""
Layer 6: Physics & Mechanics
"""

# =============================
# Layer 6: Kinematics
# =============================
def kin_position(self, x0, v0, a, t):
    """
    Compute the position of an object under constant acceleration.
    Formula: x = x0 + v0*t + 0.5*a*t^2
    """
    return self.add(
        self.add(x0, self.mul(v0, t)),
        self.mul(0.5 * a, self.mul(t, t))
    )

def kin_velocity(self, v0, a, t):
    """
    Compute the velocity of an object under constant acceleration.
    Formula: v = v0 + a*t
    """
    return self.add(v0, self.mul(a, t))

def kin_position_vec(self, x0, v0, a, t):
    """
    Compute the position of an object under constant acceleration (vector version).
    Formula: x = x0 + v0*t + 0.5*a*t^2
    """
    term1 = self.vec_add(x0, self.vec_scale(v0, t))
    term2 = self.vec_scale(a, 0.5 * t * t)
    return self.vec_add(term1, term2)

def kin_velocity_vec(self, v0, a, t):
    """
    Compute the velocity of an object under constant acceleration (vector version).
    Formula: v = v0 + a*t
    """
    return self.vec_add(v0, self.vec_scale(a, t))

# =============================
# Layer 6: Newton's Second Law
# =============================
def force(self, mass, acceleration):
    """
    Compute the force acting on an object using Newton's Second Law.
    Formula: F = m * a
    """
    return self.mul(mass, acceleration)

def force_vec(self, mass, acceleration_vec):
    """
    Compute the force acting on an object using Newton's Second Law (vector version).
    Formula: F = m * a
    """
    return self.vec_scale(acceleration_vec, mass)

# =============================
# Layer 6: Energy
# =============================
def kinetic_energy(self, mass, velocity):
    """
    Compute the kinetic energy of an object.
    Formula: KE = 0.5 * m * v^2
    """
    return self.mul(0.5, self.mul(mass, self.mul(velocity, velocity)))

def kinetic_energy_vec(self, mass, velocity_vec):
    """
    Compute the kinetic energy of an object (vector version).
    Formula: KE = 0.5 * m * |v|^2
    """
    v2 = self.vec_length_sq(velocity_vec)
    return self.mul(0.5, self.mul(mass, v2))

def potential_energy(self, mass, g, height):
    """
    Compute the gravitational potential energy of an object.
    Formula: PE = m * g * h
    """
    return self.mul(mass, self.mul(g, height))

def mechanical_energy(self, KE, PE):
    """
    Compute the total mechanical energy of an object.
    Formula: ME = KE + PE
    """
    return self.add(KE, PE)

# =============================
# Layer 6: Harmonic Oscillator
# =============================
def spring_force(self, k, x):
    """
    Compute the spring force using Hooke's law.
    Formula: F = -k * x
    """
    return self.mul(-k, x)

def spring_force_vec(self, k, x_vec):
    """
    Compute the spring force using Hooke's law (vector version).
    Formula: F = -k * x
    """
    return self.vec_scale(x_vec, -k)

def oscillator_position(self, A, omega, t, phase=0.0):
    """
    Compute the position of a harmonic oscillator at time t.
    Formula: x(t) = A * cos(ωt + φ)
    """
    return self.mul(A, self.cos(self.add(self.mul(omega, t), phase)))

def oscillator_velocity(self, A, omega, t, phase=0.0):
    """
    Compute the velocity of a harmonic oscillator at time t.
    Formula: v(t) = -A * ω * sin(ωt + φ)
    """
    return self.mul(-self.mul(A, omega), self.sin(self.add(self.mul(omega, t), phase)))

# =============================
# Layer 6: Waves
# =============================
def wave_displacement(self, A, k, omega, x, t, phase=0.0):
    """
    Compute the displacement of a wave at position x and time t.
    Formula: y(x, t) = A * sin(kx - ωt + φ)
    """
    arg = self.add(self.sub(self.mul(k, x), self.mul(omega, t)), phase)
    return self.mul(A, self.sin(arg))

# =============================
# Layer 6: Thermodynamics
# =============================
def ideal_gas_pressure(self, n, R, T, V):
    """
    Compute the pressure of an ideal gas using the ideal gas law.
    Formula: P = nRT / V
    """
    if V == 0:
        return None
    return self.div(self.mul(self.mul(n, R), T), V)

def ideal_gas_temperature(self, P, V, n, R):
    """
    Compute the temperature of an ideal gas using the ideal gas law.
    Formula: T = PV / (nR)
    """
    if self.mul(n, R) == 0:
        return None
    return self.div(self.mul(P, V), self.mul(n, R))

def ideal_gas_volume(self, n, R, T, P):
    """
    Compute the volume of an ideal gas using the ideal gas law.
    Formula: V = nRT / P
    """
    if P == 0:
        return None
    return self.div(self.mul(self.mul(n, R), T), P)
"""
Layer 9: Astrophysics
"""

# =============================
# Layer 9: Newtonian Gravity
# =============================
def gravitational_force(self, G, m1, m2, r):
    """
    Compute the gravitational force between two masses using Newton's law of universal gravitation.
    Formula: F = G * (m1 * m2) / r^2
    """
    if r == 0:
        return None
    return self.div(self.mul(G, self.mul(m1, m2)), self.mul(r, r))

def gravitational_force_vec(self, G, m1, m2, r_vec):
    """
    Compute the gravitational force vector between two masses using Newton's law of universal gravitation.
    Formula: F_vec = -G * (m1 * m2) / |r_vec|^2 * (r_vec / |r_vec|)
    """
    r = self.vec_length(r_vec)
    if r == 0:
        return [0.0, 0.0, 0.0]
    mag = self.div(self.mul(G, self.mul(m1, m2)), self.mul(r, r))
    direction = self.vec_normalize(r_vec)
    return self.vec_scale(direction, -mag)

# =============================
# Layer 9: Orbital Mechanics
# =============================
def orbital_velocity(self, G, M, r):
    """
    Compute the orbital velocity of an object in a circular orbit.
    Formula: v = sqrt(GM / r)
    """
    if r == 0:
        return None
    return self.sqrt(self.div(self.mul(G, M), r))

def escape_velocity(self, G, M, r):
    """
    Compute the escape velocity of an object from a celestial body.
    Formula: v = sqrt(2GM / r)
    """
    if r == 0:
        return None
    return self.sqrt(self.div(self.mul(2 * G, M), r))

def orbital_period(self, G, M, r):
    """
    Compute the orbital period of an object in a circular orbit.
    Formula: T = 2π sqrt(r^3 / GM)
    """
    pi = 3.141592653589793
    if M == 0:
        return None
    inside = self.div(r * r * r, self.mul(G, M))
    return self.mul(2 * pi, self.sqrt(inside))

def kepler_third(self, a, M):
    """
    Compute the proportionality in Kepler's third law.
    Formula: T^2 ∝ a^3 / M
    """
    if M == 0:
        return None
    return self.div(a * a * a, M)

# =============================
# Layer 9: Cosmology
# =============================
def redshift(self, observed, emitted):
    """
    Compute the redshift (z) based on observed and emitted wavelengths.
    Formula: z = (observed - emitted) / emitted
    """
    if emitted == 0:
        return None
    return self.div(self.sub(observed, emitted), emitted)

def hubble_velocity(self, H0, distance):
    """
    Compute the velocity of a galaxy due to the Hubble flow.
    Formula: v = H0 * d
    """
    return self.mul(H0, distance)

# =============================
# Layer 9: Luminosity & Brightness
# =============================
def luminosity(self, flux, distance):
    """
    Compute the luminosity of an object.
    Formula: L = 4π d^2 F
    """
    pi = 3.141592653589793
    return self.mul(4 * pi * distance * distance, flux)

def brightness(self, luminosity, distance):
    """
    Compute the brightness (flux) of an object.
    Formula: F = L / (4π d^2)
    """
    pi = 3.141592653589793
    denom = 4 * pi * distance * distance
    if denom == 0:
        return None
    return self.div(luminosity, denom)

# =============================
# Layer 9: Blackbody Radiation
# =============================
def blackbody_intensity(self, T, wavelength):
    """
    Compute the intensity of blackbody radiation at a given temperature and wavelength.
    Formula: I ∝ 1 / (λ^5 * (e^(c / (λT)) - 1))
    """
    if wavelength == 0 or T == 0:
        return None
    c = 1.4388e-2  # constant (m*K)
    exp_term = self.exp(c / (wavelength * T))
    denom = (wavelength**5) * (exp_term - 1)
    if denom == 0:
        return None
    return 1.0 / denom

# =============================
# Layer 9: Stellar Evolution
# =============================
def stellar_lifetime(self, mass_solar):
    """
    Compute the approximate stellar lifetime based on its mass.
    Formula: τ ∝ 1 / mass^(2.5)
    """
    if mass_solar <= 0:
        return None
    return self.div(1.0, mass_solar ** 2.5)

# =============================
# Layer 9: Gravitational Potential Energy
# =============================
def gravitational_potential(self, G, M, m, r):
    """
    Compute the gravitational potential energy between two masses.
    Formula: U = -G * (M * m) / r
    """
    if r == 0:
        return None
    return -self.div(self.mul(G, self.mul(M, m)), r)
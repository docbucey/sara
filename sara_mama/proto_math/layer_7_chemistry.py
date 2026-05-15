"""
Layer 7: Chemistry
"""

# =============================
# Layer 7: Moles & Mass
# =============================
def moles(self, mass, molar_mass):
    """
    Compute the number of moles of a substance.
    Formula: n = mass / molar_mass
    """
    if molar_mass == 0:
        return None
    return self.div(mass, molar_mass)

def mass_from_moles(self, moles, molar_mass):
    """
    Compute the mass of a substance given the number of moles.
    Formula: mass = moles * molar_mass
    """
    return self.mul(moles, molar_mass)

def concentration_molarity(self, moles, volume_liters):
    """
    Compute the molarity (concentration) of a solution.
    Formula: M = moles / volume
    """
    if volume_liters == 0:
        return None
    return self.div(moles, volume_liters)

# =============================
# Layer 7: Reaction Rates
# =============================
def rate_zero_order(self, k, t, A0):
    """
    Compute the concentration of a reactant for a zero-order reaction.
    Formula: [A] = [A]0 - kt
    """
    return self.sub(A0, self.mul(k, t))

def rate_first_order(self, k, t, A0):
    """
    Compute the concentration of a reactant for a first-order reaction.
    Formula: [A] = [A]0 * e^(-kt)
    """
    return self.mul(A0, self.exp(self.mul(-k, t)))

def rate_second_order(self, k, t, A0):
    """
    Compute the concentration of a reactant for a second-order reaction.
    Formula: 1/[A] = 1/[A]0 + kt
    """
    denom = self.add(self.div(1.0, A0), self.mul(k, t))
    if denom == 0:
        return None
    return self.div(1.0, denom)

# =============================
# Layer 7: Radioactive Decay
# =============================
def decay_amount(self, N0, k, t):
    """
    Compute the remaining amount of a substance after radioactive decay.
    Formula: N = N0 * e^(-kt)
    """
    return self.mul(N0, self.exp(self.mul(-k, t)))

def half_life(self, k):
    """
    Compute the half-life of a substance based on its decay constant.
    Formula: t1/2 = ln(2) / k
    """
    if k == 0:
        return None
    return self.div(self.ln(2.0), k)
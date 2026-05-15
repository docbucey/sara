"""
Layer 8: Biology & Ecology
"""

# =============================
# Layer 8: Enthalpy
# =============================

def reaction_enthalpy(self, products, reactants):
    """
    Compute the enthalpy change of a reaction.
    Formula: ΔH = Σ(H_products * coeff_products) - Σ(H_reactants * coeff_reactants)
    """
    total_products = 0.0
    total_reactants = 0.0

    for H, coeff in products:
        total_products = self.add(total_products, H * coeff)

    for H, coeff in reactants:
        total_reactants = self.add(total_reactants, H * coeff)

    return self.sub(total_products, total_reactants)

# =============================
# Layer 8: Exponential Growth/Decay
# =============================

def bio_exp_growth(self, N0, r, t):
    """
    Compute the population size at time t under exponential growth.
    Formula: N(t) = N0 * e^(r * t)
    """
    return self.mul(N0, self.exp(self.mul(r, t)))

def bio_exp_decay(self, N0, r, t):
    """
    Compute the population size at time t under exponential decay.
    Formula: N(t) = N0 * e^(-r * t)
    """
    return self.mul(N0, self.exp(self.mul(-r, t)))

# =============================
# Layer 8: Logistic Growth
# =============================

def logistic_growth(self, N0, r, K, t):
    """
    Compute the population size at time t under logistic growth.
    Formula: N(t) = K / (1 + ((K - N0)/N0) * e^(-r * t))
    """
    if N0 == 0:
        return None
    A = self.div(self.sub(K, N0), N0)
    denom = self.add(1.0, self.mul(A, self.exp(self.mul(-r, t))))
    if denom == 0:
        return None
    return self.div(K, denom)

def logistic_step(self, N, r, K, dt):
    """
    Compute the next population size using the logistic growth differential equation.
    Formula: dN/dt = rN(1 - N/K), N_next = N + dN/dt * dt
    """
    growth = self.mul(self.mul(r, N), self.sub(1, self.div(N, K)))
    return self.add(N, self.mul(growth, dt))

# =============================
# Layer 8: Michaelis-Menten Kinetics
# =============================

def michaelis_menten(self, Vmax, Km, S):
    """
    Compute the reaction velocity using the Michaelis-Menten equation.
    Formula: v = (Vmax * [S]) / (Km + [S])
    """
    denom = self.add(Km, S)
    if denom == 0:
        return None
    return self.mul(Vmax, self.div(S, denom))

# =============================
# Layer 8: Hill Equation
# =============================

def hill_equation(self, Vmax, K, n, S):
    """
    Compute the reaction velocity using the Hill equation.
    Formula: v = Vmax * S^n / (K^n + S^n)
    """
    Sn = S ** n
    Kn = K ** n
    denom = Kn + Sn
    if denom == 0:
        return None
    return self.mul(Vmax, self.div(Sn, denom))

# =============================
# Layer 8: Diffusion (Fick's Law)
# =============================

def diffusion_flux(self, D, dC, dx):
    """
    Compute the diffusion flux using Fick's first law.
    Formula: J = -D * (dC/dx)
    """
    if dx == 0:
        return None
    return self.mul(-D, self.div(dC, dx))

def diffusion_step(self, C, D, dx, dt):
    """
    Compute the next concentration profile using the diffusion equation.
    """
    newC = C[:]
    for i in range(1, len(C) - 1):
        lap = self.div(self.sub(self.sub(C[i + 1], self.mul(2, C[i])), C[i - 1]), self.mul(dx, dx))
        newC[i] = self.add(C[i], self.mul(self.mul(D, lap), dt))
    return newC

# =============================
# Layer 8: Predator-Prey (Lotka-Volterra)
# =============================

def lotka_volterra_step(self, prey, predator, a, b, c, d, dt):
    """
    Compute the next population sizes for prey and predator using the Lotka-Volterra equations.
    Formula: prey' = a * prey - b * prey * predator, pred' = d * prey * predator - c * predator
    """
    prey_growth = self.sub(self.mul(a, prey), self.mul(b, self.mul(prey, predator)))
    pred_growth = self.sub(self.mul(d, self.mul(prey, predator)), self.mul(c, predator))

    prey_next = self.add(prey, self.mul(prey_growth, dt))
    pred_next = self.add(predator, self.mul(pred_growth, dt))

    return prey_next, pred_next

# =============================
# Layer 8: Biological Half-Life
# =============================

def bio_half_life(self, k):
    """
    Compute the biological half-life of a substance.
    Formula: t1/2 = ln(2) / k
    """
    if k == 0:
        return None
    return self.div(self.ln(2.0), k)

# =============================
# Layer 8: Carrying Capacity Adjustment
# =============================

def adjust_carrying_capacity(self, K, resource_factor):
    """
    Adjust the carrying capacity based on a resource factor.
    Formula: K_adjusted = K * resource_factor
    """
    return self.mul(K, resource_factor)

# =============================
# Layer 8: SIR Model Step
# =============================

def sir_step(self, S, I, R, beta, gamma, dt):
    """
    Compute the next step in the SIR model for infectious disease spread.
    Formula: S' = -β S I, I' = β S I - γ I, R' = γ I
    """
    dS = self.mul(-beta, self.mul(S, I))
    dI = self.sub(self.mul(beta, self.mul(S, I)), self.mul(gamma, I))
    dR = self.mul(gamma, I)

    S_next = self.add(S, self.mul(dS, dt))
    I_next = self.add(I, self.mul(dI, dt))
    R_next = self.add(R, self.mul(dR, dt))

    return S_next, I_next, R_next
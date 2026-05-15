"""
Layer 4: Random Generators
"""

_rand_seed = 123456789

def srand(self, seed):
    """
    Set the seed for the pseudo-random number generator.
    seed: Integer seed value.
    """
    self._rand_seed = int(seed)

def rand(self):
    """
    Generate a pseudo-random float in the range [0, 1).
    Returns:
        A float in the range [0, 1).
    """
    # Linear Congruential Generator (LCG) parameters (Numerical Recipes)
    self._rand_seed = (1664525 * self._rand_seed + 1013904223) % (2**32)
    return self._rand_seed / float(2**32)

def uniform(self, a=0.0, b=1.0):
    """
    Generate a random float uniformly distributed in the range [a, b).
    a: Lower bound of the range (inclusive).
    b: Upper bound of the range (exclusive).
    Returns:
        A float in the range [a, b).
    """
    r = self.rand()  # Generate a random float in [0, 1)
    return self.add(a, self.mul(r, self.sub(b, a)))  # Scale and shift to [a, b)

def normal(self, mean=0.0, std=1.0):
    """
    Generate a random float following a normal (Gaussian) distribution.
    mean: The mean (center) of the distribution.
    std: The standard deviation (spread) of the distribution.
    Returns:
        A float sampled from the normal distribution.
    """
    u1 = self.rand()
    u2 = self.rand()
    # Avoid log(0) by ensuring u1 > 0
    if u1 <= 0:
        u1 = 1e-12
    z0 = self.sqrt(-2.0 * self.ln(u1)) * self.cos(2.0 * 3.141592653589793 * u2)
    return self.add(mean, self.mul(std, z0))  # Scale and shift to the desired mean and std

def exponential(self, lam=1.0):
    """
    Generate a random float following an exponential distribution.
    lam: The rate parameter (lambda), which is the inverse of the mean (1/mean).
    Returns:
        A float sampled from the exponential distribution.
    """
    u = self.rand()
    # Avoid log(0) by ensuring u > 0
    if u <= 0:
        u = 1e-12
    return -self.ln(u) / lam

def pdf_normal(self, x, mean=0.0, std=1.0):
    """
    Compute the probability density function (PDF) of a normal (Gaussian) distribution.
    x: The value at which to evaluate the PDF.
    mean: The mean (center) of the distribution.
    std: The standard deviation (spread) of the distribution.
    Returns:
        The PDF value at x.
    """
    var = self.mul(std, std)  # Variance = std^2
    denom = self.sqrt(self.mul(2.0 * 3.141592653589793, var))  # sqrt(2 * pi * variance)
    num = self.exp(-self.div(self.mul((x - mean), (x - mean)), self.mul(2.0, var)))  # exp(-((x - mean)^2) / (2 * variance))
    return self.div(num, denom)  # PDF = num / denom

def pdf_exponential(self, x, lam=1.0):
    """
    Compute the probability density function (PDF) of an exponential distribution.
    x: The value at which to evaluate the PDF.
    lam: The rate parameter (lambda), which is the inverse of the mean (1/mean).
    Returns:
        The PDF value at x.
    """
    if x < 0:
        return 0.0  # PDF is 0 for x < 0 in an exponential distribution
    return self.mul(lam, self.exp(self.mul(-lam, x)))  # PDF = λ * exp(-λ * x)

def cdf_normal(self, x, mean=0.0, std=1.0):
    """
    Compute the cumulative distribution function (CDF) of a normal (Gaussian) distribution.
    This uses an approximation of the error function (erf).
    x: The value at which to evaluate the CDF.
    mean: The mean (center) of the distribution.
    std: The standard deviation (spread) of the distribution.
    Returns:
        The CDF value at x.
    """
    # Standardize x to z-score
    z = self.div(self.sub(x, mean), self.mul(std, self.sqrt(2.0)))
    t = self.div(1.0, self.add(1.0, self.mul(0.3275911, abs(z))))

    # Approximation of the error function (erf)
    erf_approx = self.sub(1.0, self.mul(
        (((((1.061405429 * t - 1.453152027) * t)
           + 1.421413741) * t - 0.284496736) * t
           + 0.254829592) * t,
        self.exp(self.mul(-z, z))
    ))

    # Adjust for negative z
    if z < 0:
        erf_approx = -erf_approx

    # Compute the CDF
    return self.mul(0.5, self.add(1.0, erf_approx))

def cdf_exponential(self, x, lam=1.0):
    """
    Compute the cumulative distribution function (CDF) of an exponential distribution.
    x: The value at which to evaluate the CDF.
    lam: The rate parameter (lambda), which is the inverse of the mean (1/mean).
    Returns:
        The CDF value at x.
    """
    if x < 0:
        return 0.0  # CDF is 0 for x < 0 in an exponential distribution
    return self.sub(1.0, self.exp(self.mul(-lam, x)))  # CDF = 1 - exp(-λ * x)

def monte_carlo(self, f, samples=1000):
    """
    Perform Monte-Carlo sampling to estimate the expected value of a function.
    f: A callable that generates random samples (e.g., a probability distribution).
    samples: The number of samples to draw.
    Returns:
        The estimated expected value of f.
    """
    total = 0.0
    for _ in range(samples):
        total = self.add(total, f())  # Accumulate the function's output
    return self.div(total, samples)  # Average the total over the number of samples

def rand_vec(self, n, a=0.0, b=1.0):
    """
    Generate a random vector of size n with elements uniformly distributed in the range [a, b).
    n: The size of the vector.
    a: Lower bound of the range (inclusive).
    b: Upper bound of the range (exclusive).
    Returns:
        A list of n random floats in the range [a, b).
    """
    return [self.uniform(a, b) for _ in range(n)]

def rand_mat(self, rows, cols, a=0.0, b=1.0):
    """
    Generate a random matrix with the specified number of rows and columns.
    Each element is uniformly distributed in the range [a, b).
    rows: Number of rows in the matrix.
    cols: Number of columns in the matrix.
    a: Lower bound of the range (inclusive).
    b: Upper bound of the range (exclusive).
    Returns:
        A 2D list (matrix) with random floats in the range [a, b).
    """
    return [[self.uniform(a, b) for _ in range(cols)] for _ in range(rows)]

def random_walk(self, steps=100):
    """
    Perform a 1D random walk with the specified number of steps.
    steps: The number of steps in the random walk.
    Returns:
        The final position after the random walk.
    """
    x = 0.0
    for _ in range(steps):
        step = self.uniform(-1.0, 1.0)  # Generate a random step in [-1.0, 1.0)
        x = self.add(x, step)  # Update the position
    return x

def evolve_stochastic(self, state, drift, volatility):
    """
    Perform a single step of stochastic evolution.
    The evolution follows the formula:
        state_{t+1} = state_t + drift + volatility * N(0,1)
    where N(0,1) is a standard normal random variable.
    
    state: The current state value.
    drift: The deterministic drift term.
    volatility: The volatility (scale of randomness).
    Returns:
        The evolved state after one step.
    """
    noise = self.normal(0.0, volatility)  # Generate noise from N(0, volatility)
    return self.add(state, self.add(drift, noise))  # Update state
# Copilot: Create and refactor this file so it contains ONLY the mathematics described in the docstring below.
# Do NOT add unrelated algorithms, imports, or helpers.
# Generate only the functions explicitly described in the docstring.

"""
Layer 12: Acoustic Physics & Sound Mathematics

This layer provides mathematical tools for modeling sound, waves, and audio behavior.
It includes:

- frequency, wavelength, and wave speed relationships
- decibel (dB) math and SPL calculations
- inverse-square law for sound attenuation
- Doppler effect (source and observer motion)
- resonance and natural frequency formulas
- basic room acoustics (RT60, absorption)
- simple filter approximations (low-pass, high-pass)

This layer should NOT include optics, mechanics, or unrelated physics.
"""

# -------------------------
# Acoustic Physics & Sound Math
# -------------------------

def wavelength(frequency, speed_of_sound=343):
    """
    Compute the wavelength of a sound wave.
    Formula: λ = v / f
    """
    if frequency == 0:
        return None
    return speed_of_sound / frequency

def decibels(power_ratio):
    """
    Compute the decibel (dB) level from a power ratio.
    Formula: dB = 10 * log10(power_ratio)
    """
    from math import log10
    if power_ratio <= 0:
        return None
    return 10 * log10(power_ratio)

def sound_pressure_level(pressure, reference=20e-6):
    """
    Compute the sound pressure level (SPL) in decibels.
    Formula: SPL = 20 * log10(pressure / reference)
    """
    from math import log10
    if pressure <= 0 or reference <= 0:
        return None
    return 20 * log10(pressure / reference)

def inverse_square_attenuation(distance):
    """
    Compute the attenuation of sound intensity due to the inverse-square law.
    Formula: I ∝ 1 / distance^2
    """
    if distance <= 0:
        return None
    return 1 / (distance ** 2)

def doppler_effect(frequency, source_velocity, observer_velocity, speed_of_sound=343):
    """
    Compute the observed frequency due to the Doppler effect.
    Formula: f' = f * (v + v_obs) / (v - v_src)
    """
    if speed_of_sound - source_velocity == 0:
        return None
    return frequency * (speed_of_sound + observer_velocity) / (speed_of_sound - source_velocity)

def resonance_frequency(stiffness, mass):
    """
    Compute the resonance frequency of a system.
    Formula: f = (1 / 2π) * sqrt(k / m)
    """
    from math import sqrt, pi
    if mass <= 0:
        return None
    return (1 / (2 * pi)) * sqrt(stiffness / mass)

def rt60(volume, absorption_area):
    """
    Compute the reverberation time (RT60) for a room.
    Formula: RT60 = 0.161 * (volume / absorption_area)
    """
    if absorption_area <= 0:
        return None
    return 0.161 * (volume / absorption_area)
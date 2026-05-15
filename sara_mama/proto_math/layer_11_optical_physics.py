"""
Layer 11: Optical Physics & Camera Mathematics

This layer provides mathematical tools for modeling cameras, lenses, and light behavior.
It includes:

- focal length and field of view calculations
- aperture, F-number, and exposure relationships
- sensor size, crop factor, and pixel pitch math
- depth of field (DOF) and hyperfocal distance
- magnification and lens projection formulas
- radiometry/photometry basics (lux, lumens, irradiance)
- simple lens distortion models (barrel/pincushion)

This layer should NOT include acoustics, mechanics, or unrelated physics.
"""

# -------------------------
# Optical Physics & Camera Math
# -------------------------

def focal_length_from_fov(sensor_size, fov):
    """
    Compute the focal length from the field of view (FOV) and sensor size.
    Formula: f = sensor_size / (2 * tan(FOV / 2))
    """
    from math import tan
    return sensor_size / (2 * tan(fov / 2))

def field_of_view(sensor_size, focal_length):
    """
    Compute the field of view (FOV) from the sensor size and focal length.
    Formula: FOV = 2 * atan(sensor_size / (2 * focal_length))
    """
    from math import atan
    return 2 * atan(sensor_size / (2 * focal_length))

def f_number(focal_length, aperture_diameter):
    """
    Compute the F-number (aperture) of a lens.
    Formula: F = focal_length / aperture_diameter
    """
    return focal_length / aperture_diameter

def exposure_value(aperture, shutter_speed, iso):
    """
    Compute the exposure value (EV) for a given aperture, shutter speed, and ISO.
    Formula: EV = log2((aperture^2) / shutter_speed) - log2(ISO / 100)
    """
    from math import log2
    return log2((aperture ** 2) / shutter_speed) - log2(iso / 100)

def depth_of_field(focal_length, aperture, subject_distance, coc):
    """
    Compute the depth of field (DOF) for a given setup.
    Formula:
        H = (subject_distance * hyperfocal_distance) / (hyperfocal_distance + (subject_distance - focal_length))
        DOF = 2 * (H - subject_distance)
    """
    hyperfocal = hyperfocal_distance(focal_length, aperture, coc)
    near_focus = (subject_distance * (hyperfocal - focal_length)) / (hyperfocal + (subject_distance - focal_length))
    far_focus = (subject_distance * (hyperfocal - focal_length)) / (hyperfocal - (subject_distance - focal_length))
    return far_focus - near_focus

def hyperfocal_distance(focal_length, aperture, coc):
    """
    Compute the hyperfocal distance for a given focal length, aperture, and circle of confusion (CoC).
    Formula: H = (focal_length^2) / (aperture * coc)
    """
    return (focal_length ** 2) / (aperture * coc)

def magnification(focal_length, subject_distance):
    """
    Compute the magnification of a lens.
    Formula: M = focal_length / (subject_distance - focal_length)
    """
    if subject_distance == focal_length:
        return None  # Avoid division by zero
    return focal_length / (subject_distance - focal_length)

def pixel_pitch(sensor_width, resolution_width):
    """
    Compute the pixel pitch of a camera sensor.
    Formula: pixel_pitch = sensor_width / resolution_width
    """
    return sensor_width / resolution_width
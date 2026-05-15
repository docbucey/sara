"""
Layer 5: Geometry & Transformations
"""

# =============================
# Layer 5: Distances & Angles
# =============================
def distance(self, a, b):
    """
    Compute the Euclidean distance between two vectors a and b.
    a: First vector.
    b: Second vector.
    Returns:
        The Euclidean distance between a and b.
    """
    diff = self.vec_sub(a, b)  # Subtract vectors
    return self.vec_length(diff)  # Compute the length of the difference

def distance_sq(self, a, b):
    """
    Compute the squared Euclidean distance between two vectors a and b.
    a: First vector.
    b: Second vector.
    Returns:
        The squared Euclidean distance between a and b.
    """
    diff = self.vec_sub(a, b)  # Subtract vectors
    return self.vec_length_sq(diff)  # Compute the squared length of the difference

def angle_between(self, a, b):
    """
    Compute the angle (in radians) between two vectors a and b.
    a: First vector.
    b: Second vector.
    Returns:
        The angle in radians between a and b, or None if one of the vectors is zero.
    """
    dot = self.vec_dot(a, b)  # Compute the dot product
    la = self.vec_length(a)  # Compute the length of vector a
    lb = self.vec_length(b)  # Compute the length of vector b
    if la == 0 or lb == 0:
        return None  # Undefined angle if one of the vectors is zero
    cos_theta = self.div(dot, self.mul(la, lb))  # cos(θ) = dot(a, b) / (|a| * |b|)

    # Clamp cos_theta to the range [-1, 1] to avoid numerical errors
    if cos_theta > 1.0:
        cos_theta = 1.0
    if cos_theta < -1.0:
        cos_theta = -1.0

    # Compute arccos using Newton's method
    y = 0.0
    for _ in range(20):  # Iterate to refine the solution
        cy = self.cos(y)
        sy = self.sin(y)
        y = self.sub(y, self.div(self.sub(cy, cos_theta), self.mul(-sy, 1.0 if sy != 0 else 1e-12)))
    return y

# =============================
# Layer 5: Projections
# =============================
def project_vec(self, a, b):
    """
    Project vector a onto vector b.
    a: The vector to be projected.
    b: The vector onto which a is projected.
    Returns:
        The projection of a onto b as a vector.
    """
    denom = self.vec_dot(b, b)  # Compute the dot product of b with itself
    if denom == 0:
        return [0.0 for _ in b]  # Return a zero vector if b is a zero vector
    scale = self.div(self.vec_dot(a, b), denom)  # Compute the scaling factor
    return self.vec_scale(b, scale)  # Scale vector b by the factor

def reject_vec(self, a, b):
    """
    Compute the component of vector a orthogonal to vector b.
    a: The vector to be deconstructed.
    b: The vector defining the direction of the projection.
    Returns:
        The rejection of a from b as a vector.
    """
    proj = self.project_vec(a, b)  # Compute the projection of a onto b
    return self.vec_sub(a, proj)  # Subtract the projection from a to get the rejection

# =============================
# Layer 5: 2D Transforms
# =============================
def mat2d_translation(self, tx, ty):
    """
    Create a 2D translation matrix.
    tx: Translation along the x-axis.
    ty: Translation along the y-axis.
    Returns:
        A 3x3 translation matrix.
    """
    return [
        [1.0, 0.0, tx],
        [0.0, 1.0, ty],
        [0.0, 0.0, 1.0],
    ]

def mat2d_scale(self, sx, sy):
    """
    Create a 2D scaling matrix.
    sx: Scaling factor along the x-axis.
    sy: Scaling factor along the y-axis.
    Returns:
        A 3x3 scaling matrix.
    """
    return [
        [sx, 0.0, 0.0],
        [0.0, sy, 0.0],
        [0.0, 0.0, 1.0],
    ]

def mat2d_rotation(self, theta):
    """
    Create a 2D rotation matrix.
    theta: Rotation angle in radians.
    Returns:
        A 3x3 rotation matrix.
    """
    c = self.cos(theta)
    s = self.sin(theta)
    return [
        [c, -s, 0.0],
        [s,  c, 0.0],
        [0.0, 0.0, 1.0],
    ]

def apply_mat2d(self, M, p):
    """
    Apply a 2D transformation matrix to a point.
    M: A 3x3 transformation matrix.
    p: A 2D point [x, y].
    Returns:
        The transformed 2D point [x', y'].
    """
    x, y = p
    v = [x, y, 1.0]  # Homogeneous coordinates
    r = self.mat_vec_mul(M, v)  # Multiply the matrix by the vector
    return [r[0], r[1]]  # Return the transformed point

# =============================
# Layer 5: 3D Rotation Matrices
# =============================
def mat3d_rotation_x(self, theta):
    """
    Create a 3D rotation matrix for rotation around the x-axis.
    theta: Rotation angle in radians.
    Returns:
        A 3x3 rotation matrix.
    """
    c = self.cos(theta)
    s = self.sin(theta)
    return [
        [1.0, 0.0, 0.0],
        [0.0, c, -s],
        [0.0, s,  c],
    ]

def mat3d_rotation_y(self, theta):
    """
    Create a 3D rotation matrix for rotation around the y-axis.
    theta: Rotation angle in radians.
    Returns:
        A 3x3 rotation matrix.
    """
    c = self.cos(theta)
    s = self.sin(theta)
    return [
        [ c, 0.0, s],
        [0.0, 1.0, 0.0],
        [-s, 0.0, c],
    ]

def mat3d_rotation_z(self, theta):
    """
    Create a 3D rotation matrix for rotation around the z-axis.
    theta: Rotation angle in radians.
    Returns:
        A 3x3 rotation matrix.
    """
    c = self.cos(theta)
    s = self.sin(theta)
    return [
        [c, -s, 0.0],
        [s,  c, 0.0],
        [0.0, 0.0, 1.0],
    ]

def apply_mat3d(self, M, v):
    """
    Apply a 3D transformation matrix to a vector.
    M: A 3x3 transformation matrix.
    v: A 3D vector [x, y, z].
    Returns:
        The transformed 3D vector [x', y', z'].
    """
    return self.mat_vec_mul(M, v)

# =============================
# Layer 5: Quaternions (Rotation)
# =============================
def quat_from_axis_angle(self, axis, angle):
    """
    Create a quaternion from an axis-angle representation.
    axis: 3D unit vector representing the axis of rotation.
    angle: Rotation angle in radians.
    Returns:
        A quaternion [w, x, y, z].
    """
    ax = self.vec_normalize(axis)  # Ensure the axis is a unit vector
    half = self.div(angle, 2.0)  # Half the angle
    s = self.sin(half)
    w = self.cos(half)
    x = self.mul(ax[0], s)
    y = self.mul(ax[1], s)
    z = self.mul(ax[2], s)
    return [w, x, y, z]

def quat_normalize(self, q):
    """
    Normalize a quaternion.
    q: Quaternion [w, x, y, z].
    Returns:
        A normalized quaternion.
    """
    w, x, y, z = q
    mag = self.sqrt(self.add(self.add(self.add(self.mul(w, w), self.mul(x, x)), self.mul(y, y)), self.mul(z, z)))
    if mag == 0:
        return [1.0, 0.0, 0.0, 0.0]  # Default to identity quaternion
    return [self.div(w, mag), self.div(x, mag), self.div(y, mag), self.div(z, mag)]

def quat_mul(self, q1, q2):
    """
    Multiply two quaternions.
    q1: First quaternion [w1, x1, y1, z1].
    q2: Second quaternion [w2, x2, y2, z2].
    Returns:
        The product quaternion [w, x, y, z].
    """
    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2
    w = self.sub(self.sub(self.sub(self.mul(w1, w2), self.mul(x1, x2)), self.mul(y1, y2)), self.mul(z1, z2))
    x = self.add(self.add(self.sub(self.mul(w1, x2), self.mul(z1, y2)), self.mul(y1, z2)), self.mul(x1, w2))
    y = self.add(self.add(self.sub(self.mul(w1, y2), self.mul(x1, z2)), self.mul(z1, x2)), self.mul(y1, w2))
    z = self.add(self.add(self.sub(self.mul(w1, z2), self.mul(y1, x2)), self.mul(x1, y2)), self.mul(z1, w2))
    return [w, x, y, z]

def quat_conjugate(self, q):
    """
    Compute the conjugate of a quaternion.
    q: Quaternion [w, x, y, z].
    Returns:
        The conjugate quaternion [w, -x, -y, -z].
    """
    w, x, y, z = q
    return [w, self.mul(-1.0, x), self.mul(-1.0, y), self.mul(-1.0, z)]

def quat_rotate_vec(self, q, v):
    """
    Rotate a 3D vector using a quaternion.
    q: Quaternion [w, x, y, z].
    v: 3D vector [vx, vy, vz].
    Returns:
        The rotated vector [vx', vy', vz'].
    """
    q = self.quat_normalize(q)  # Ensure the quaternion is normalized
    # Convert the vector to a pure quaternion
    qv = [0.0, v[0], v[1], v[2]]
    qc = self.quat_conjugate(q)  # Conjugate of the quaternion
    # Perform the rotation: q * qv * q_conjugate
    qvq = self.quat_mul(self.quat_mul(q, qv), qc)
    return [qvq[1], qvq[2], qvq[3]]  # Extract the rotated vector
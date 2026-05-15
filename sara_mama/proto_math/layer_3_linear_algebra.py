"""
Layer 3: Linear Algebra
"""

def mat_transpose(self, A):
    """
    Compute the transpose of a matrix A.
    A: 2D list representing the matrix.
    Returns the transposed matrix.
    """
    rows = len(A)
    cols = len(A[0])
    return [[A[r][c] for r in range(rows)] for c in range(cols)]

def mat_det(self, A):
    """
    Compute the determinant of a square matrix A.
    A: 2D list representing the matrix.
    Returns the determinant as a float.
    """
    n = len(A)
    if n == 1:
        return A[0][0]
    if n == 2:
        return self.sub(self.mul(A[0][0], A[1][1]), self.mul(A[0][1], A[1][0]))

    det = 0.0
    for c in range(n):
        det = self.add(det, self.mul(
            ((-1) ** c) * A[0][c],
            self.mat_det(self.mat_minor(A, 0, c))
        ))
    return det

def mat_minor(self, A, row, col):
    """
    Compute the minor of a matrix A by removing the specified row and column.
    A: 2D list representing the matrix.
    row: Index of the row to remove.
    col: Index of the column to remove.
    Returns the resulting submatrix.
    """
    return [
        [A[r][c] for c in range(len(A)) if c != col]
        for r in range(len(A)) if r != row
    ]

def mat_cofactor(self, A):
    """
    Compute the cofactor matrix of a square matrix A.
    A: 2D list representing the matrix.
    Returns the cofactor matrix as a 2D list.
    """
    n = len(A)
    C = []
    for r in range(n):
        row = []
        for c in range(n):
            minor = self.mat_minor(A, r, c)
            sign = -1 if (r + c) % 2 else 1
            row.append(sign * self.mat_det(minor))
        C.append(row)
    return C

def mat_adjoint(self, A):
    """
    Compute the adjoint (adjugate) matrix of a square matrix A.
    A: 2D list representing the matrix.
    Returns the adjoint matrix as a 2D list.
    """
    return self.mat_transpose(self.mat_cofactor(A))

def mat_inverse(self, A):
    """
    Compute the inverse of a square matrix A.
    A: 2D list representing the matrix.
    Returns the inverse matrix as a 2D list, or None if the matrix is singular.
    """
    det = self.mat_det(A)
    if det == 0:
        return None  # Singular matrix, no inverse exists
    adj = self.mat_adjoint(A)
    return [[self.div(adj[r][c], det) for c in range(len(A))] for r in range(len(A))]

def mat_lu(self, A):
    """
    Perform LU decomposition of a square matrix A.
    A: 2D list representing the matrix.
    Returns two matrices L (lower triangular) and U (upper triangular) such that A = L * U.
    """
    n = len(A)
    L = [[0.0]*n for _ in range(n)]
    U = [[0.0]*n for _ in range(n)]

    for i in range(n):
        # Upper triangular matrix U
        for k in range(i, n):
            total = 0.0
            for j in range(i):
                total = self.add(total, self.mul(L[i][j], U[j][k]))
            U[i][k] = self.sub(A[i][k], total)

        # Lower triangular matrix L
        for k in range(i, n):
            if i == k:
                L[i][i] = 1.0  # Diagonal elements of L are 1
            else:
                total = 0.0
                for j in range(i):
                    total = self.add(total, self.mul(L[k][j], U[j][i]))
                L[k][i] = self.div(self.sub(A[k][i], total), U[i][i])

    return L, U

def mat_qr(self, A):
    """
    Perform QR decomposition of a matrix A using the Gram-Schmidt process.
    A: 2D list representing the matrix.
    Returns two matrices Q (orthogonal) and R (upper triangular) such that A = Q * R.
    """
    import copy
    A = copy.deepcopy(A)
    m = len(A)
    n = len(A[0])

    Q = [[0.0]*n for _ in range(m)]
    R = [[0.0]*n for _ in range(n)]

    for j in range(n):
        v = [A[i][j] for i in range(m)]

        for k in range(j):
            qk = [Q[i][k] for i in range(m)]
            R[k][j] = self.vec_dot(qk, v)
            v = self.vec_sub(v, self.vec_scale(qk, R[k][j]))

        R[j][j] = self.vec_length(v)
        if R[j][j] == 0:
            continue

        qj = self.vec_scale(v, 1.0 / R[j][j])
        for i in range(m):
            Q[i][j] = qj[i]

    return Q, R

def eigenvector_power(self, A, iterations=50):
    """
    Compute the dominant eigenvector of a square matrix A using the power iteration method.
    A: 2D list representing the matrix.
    iterations: Number of iterations to perform.
    Returns the dominant eigenvector as a list.
    """
    n = len(A)
    v = [1.0] * n  # Initial guess for the eigenvector

    for _ in range(iterations):
        v_new = self.mat_vec_mul(A, v)  # Multiply A by the current vector
        length = self.vec_length(v_new)  # Compute the length of the resulting vector
        if length == 0:
            break  # Avoid division by zero
        v = [x / length for x in v_new]  # Normalize the vector

    return v
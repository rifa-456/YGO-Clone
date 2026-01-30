# cython: language_level=3, embedsignature=True
# cython: boundscheck=False
# cython: wraparound=False

from engine.logger import Logger
from engine.math.datatypes.vector2 cimport Vector2

cpdef tuple apply_homography(list h, double x, double y):
    """
    Applies homography to a single point.
    Optimized for single-access events (like mouse input).
    """
    cdef double denom, inv_denom
    cdef double h00 = h[0][0], h01 = h[0][1], h02 = h[0][2]
    cdef double h10 = h[1][0], h11 = h[1][1], h12 = h[1][2]
    cdef double h20 = h[2][0], h21 = h[2][1], h22 = h[2][2]

    denom = h20 * x + h21 * y + h22
    if abs(denom) < 1e-9:
        return x, y

    inv_denom = 1.0 / denom
    cdef double rx = (h00 * x + h01 * y + h02) * inv_denom
    cdef double ry = (h10 * x + h11 * y + h12) * inv_denom
    return rx, ry

def compute_homography(list src, list dst):
    """
    Computes the 3x3 Homography matrix H such that dst = H * src.
    Src and Dst must be lists of Vector2.
    Returns a Python list (3x3) to be cast to a C-array/Memoryview by the caller if needed.
    """
    if len(src) != 4 or len(dst) != 4:
        raise ValueError("Homography requires exactly 4 source and 4 destination points.")

    cdef list matrix = []
    cdef list rhs = []
    cdef Vector2 s, d
    cdef double x, y, u, v
    cdef int i, col, row, n = 8, max_row, j
    cdef double max_val, val, pivot, inv_pivot, factor

    for i in range(4):
        s = <Vector2> src[i]
        d = <Vector2> dst[i]
        x, y = s.x, s.y
        u, v = d.x, d.y
        matrix.append([x, y, 1, 0, 0, 0, -x * u, -y * u])
        rhs.append(u)
        matrix.append([0, 0, 0, x, y, 1, -x * v, -y * v])
        rhs.append(v)

    for col in range(n):
        max_row = col
        max_val = abs(matrix[col][col])
        for row in range(col + 1, n):
            val = abs(matrix[row][col])
            if val > max_val:
                max_val = val
                max_row = row

        if max_row != col:
            matrix[col], matrix[max_row] = matrix[max_row], matrix[col]
            rhs[col], rhs[max_row] = rhs[max_row], rhs[col]

        pivot = matrix[col][col]
        if abs(pivot) < 1e-9:
            Logger.error("Matrix is singular or near-singular.", "Homography")
            return [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]

        inv_pivot = 1.0 / pivot
        for j in range(col, n):
            matrix[col][j] *= inv_pivot
        rhs[col] *= inv_pivot

        for row in range(n):
            if row != col:
                factor = matrix[row][col]
                for j in range(col, n):
                    matrix[row][j] -= factor * matrix[col][j]
                rhs[row] -= factor * rhs[col]

    h = rhs
    return [[h[0], h[1], h[2]], [h[3], h[4], h[5]], [h[6], h[7], 1.0]]

def apply_homography_batch(double[:, :] h, double[:, :] points, double[:, :] out):
    """
    High-performance batch transformation.
    h: 3x3 homography matrix (memoryview)
    points: Nx2 input vertices (memoryview)
    out: Nx2 output buffer (memoryview) - MUST be allocated by caller!
    """
    cdef int i
    cdef int n = <int>points.shape[0]
    cdef double x, y, nx, ny, denom, inv_denom
    cdef double h00 = h[0, 0], h01 = h[0, 1], h02 = h[0, 2]
    cdef double h10 = h[1, 0], h11 = h[1, 1], h12 = h[1, 2]
    cdef double h20 = h[2, 0], h21 = h[2, 1], h22 = h[2, 2]

    for i in range(n):
        x = points[i, 0]
        y = points[i, 1]
        denom = h20 * x + h21 * y + h22
        if abs(denom) < 1e-9:
            out[i, 0] = x
            out[i, 1] = y
        else:
            inv_denom = 1.0 / denom
            out[i, 0] = (h00 * x + h01 * y + h02) * inv_denom
            out[i, 1] = (h10 * x + h11 * y + h12) * inv_denom

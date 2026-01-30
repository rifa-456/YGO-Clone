# cython: language_level=3, embedsignature=True
# cython: boundscheck=False
# cython: wraparound=False

from libc.math cimport sqrt, fabsf
from engine.math.datatypes.vector2 cimport Vector2


class Geometry2D:
    """
    Static helper class for 2D geometric operations.
    High-performance Cython implementation using Typed Memoryviews.
    """

    @staticmethod
    def is_point_in_polygon(Vector2 point, double[:, :] polygon):
        """
        Ray-Casting algorithm to check if a point is inside a polygon.
        Polygon must be a contiguous array of shape (N, 2).
        """
        cdef bint c = False
        cdef int n = <int> polygon.shape[0]
        cdef int i, j
        cdef double px = point.x
        cdef double py = point.y
        cdef double pix, piy, pjx, pjy

        for i in range(n):
            j = n - 1 if i == 0 else i - 1
            pix = polygon[i, 0]
            piy = polygon[i, 1]
            pjx = polygon[j, 0]
            pjy = polygon[j, 1]
            if ((piy > py) != (pjy > py)) and \
                    (px < (pjx - pix) * (py - piy) / (pjy - piy) + pix):
                c = not c
        return c

    @staticmethod
    def segment_intersects_segment(Vector2 from_a, Vector2 to_a, Vector2 from_b, Vector2 to_b):
        cdef Vector2 b = to_a - from_a
        cdef Vector2 d = to_b - from_b
        cdef double b_dot_d_perp = b.x * d.y - b.y * d.x

        if b_dot_d_perp == 0:
            return None

        cdef Vector2 c = from_b - from_a
        cdef double t = (c.x * d.y - c.y * d.x) / b_dot_d_perp
        cdef double u = (c.x * b.y - c.y * b.x) / b_dot_d_perp

        if 0.0 <= t <= 1.0 and 0.0 <= u <= 1.0:
            return Vector2(from_a.x + t * b.x, from_a.y + t * b.y)

        return None

    @staticmethod
    def offset_polygon(list points, double margin):
        """
        Inflates or deflates a polygon by a specific margin.

        Args:
            points: List of Vector2 vertices (ordered CW or CCW).
            margin: Positive to expand (if CW) / shrink (if CCW), or vice versa depending on winding.

        Returns:
            A new list of Vector2.
        """
        cdef int n = len(points)
        if n < 3:
            return []

        cdef list new_points = []
        cdef int i, j, k
        cdef Vector2 p_prev, p_curr, p_next
        cdef double dx1, dy1, len1, nx1, ny1
        cdef double dx2, dy2, len2, nx2, ny2
        cdef double det, t
        cdef double q1x, q1y, q2x, q2y, res_x, res_y

        for i in range(n):
            j = n - 1 if i == 0 else i - 1
            k = 0 if i == n - 1 else i + 1

            p_prev = <Vector2> points[j]
            p_curr = <Vector2> points[i]
            p_next = <Vector2> points[k]

            dx1 = p_curr.x - p_prev.x
            dy1 = p_curr.y - p_prev.y
            len1 = sqrt(dx1 * dx1 + dy1 * dy1)

            dx2 = p_next.x - p_curr.x
            dy2 = p_next.y - p_curr.y
            len2 = sqrt(dx2 * dx2 + dy2 * dy2)

            if len1 < 1e-6 or len2 < 1e-6:
                new_points.append(Vector2(p_curr.x, p_curr.y))
                continue

            dx1 /= len1
            dy1 /= len1
            dx2 /= len2
            dy2 /= len2

            # Normals (-dy, dx)
            nx1 = -dy1
            ny1 = dx1
            nx2 = -dy2
            ny2 = dx2

            # Determinant for line intersection
            det = dx1 * dy2 - dy1 * dx2

            # Offset points
            q1x = p_prev.x + nx1 * margin
            q1y = p_prev.y + ny1 * margin

            q2x = p_curr.x + nx2 * margin
            q2y = p_curr.y + ny2 * margin

            if fabsf(det) < 1e-9:
                # Parallel edges (collinear)
                new_points.append(Vector2(p_curr.x + nx1 * margin, p_curr.y + ny1 * margin))
            else:
                # Intersect offset lines
                t = ((q2x - q1x) * dy2 - (q2y - q1y) * dx2) / det
                res_x = q1x + t * dx1
                res_y = q1y + t * dy1
                new_points.append(Vector2(res_x, res_y))

        return new_points
# cython: language_level=3, embedsignature=True
# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True

from libc.stdlib cimport malloc, free
from engine.math.datatypes.vector2 cimport Vector2
import numpy as np
cimport numpy as cnp

cdef class Clipper:
    """
    Clipping algorithms:
    1. Sutherland-Hodgman for Polygons (preserves closed loops).
    2. Cohen-Sutherland for Lines (fast rejection).
    """

    def __cinit__(self):
        self.INSIDE = 0
        self.LEFT = 1
        self.RIGHT = 2
        self.BOTTOM = 4
        self.TOP = 8

    @staticmethod
    cdef int _compute_outcode(double x, double y, double min_x, double min_y, double max_x, double max_y) nogil:
        cdef int code = 0
        if x < min_x:
            code |= 1
        elif x > max_x:
            code |= 2
        if y < min_y:
            code |= 4
        elif y > max_y:
            code |= 8
        return code

    cpdef tuple clip_line(self, double x1, double y1, double x2, double y2, double min_x, double min_y, double max_x,
                          double max_y):
        """
        Cohen-Sutherland Line Clipping.
        Returns ((x1, y1, x2, y2), accepted) or (None, False).
        """
        cdef int outcode0 = Clipper._compute_outcode(x1, y1, min_x, min_y, max_x, max_y)
        cdef int outcode1 = Clipper._compute_outcode(x2, y2, min_x, min_y, max_x, max_y)
        cdef int outcode_out
        cdef bint accept = False
        cdef double x, y

        while True:
            if not (outcode0 | outcode1):
                accept = True
                break
            elif outcode0 & outcode1:
                break
            else:
                x = 0.0
                y = 0.0
                outcode_out = outcode0 if outcode0 else outcode1

                if outcode_out & 8:  # TOP
                    x = x1 + (x2 - x1) * (max_y - y1) / (y2 - y1)
                    y = max_y
                elif outcode_out & 4:  # BOTTOM
                    x = x1 + (x2 - x1) * (min_y - y1) / (y2 - y1)
                    y = min_y
                elif outcode_out & 2:  # RIGHT
                    y = y1 + (y2 - y1) * (max_x - x1) / (x2 - x1)
                    x = max_x
                elif outcode_out & 1:  # LEFT
                    y = y1 + (y2 - y1) * (min_x - x1) / (x2 - x1)
                    x = min_x

                if outcode_out == outcode0:
                    x1 = x
                    y1 = y
                    outcode0 = Clipper._compute_outcode(x1, y1, min_x, min_y, max_x, max_y)
                else:
                    x2 = x
                    y2 = y
                    outcode1 = Clipper._compute_outcode(x2, y2, min_x, min_y, max_x, max_y)

        if accept:
            return (x1, y1, x2, y2), True
        return None, False

    cpdef tuple clip_polygon(self, list input_points, list input_uvs, double min_x, double min_y, double max_x,
                             double max_y):
        """
        Sutherland-Hodgman Polygon Clipping.
        Returns (vertices_array, uvs_array).
        """
        cdef int input_count = len(input_points)
        cdef bint has_uvs = (input_uvs is not None) and (len(input_uvs) == input_count)

        if input_count == 0:
            return np.zeros((0, 2), dtype=np.float64), np.zeros((0, 2), dtype=np.float64)

        cdef int capacity = input_count * 2 + 16
        cdef Vertex * buffer_a = <Vertex *> malloc(capacity * sizeof(Vertex))
        cdef Vertex * buffer_b = <Vertex *> malloc(capacity * sizeof(Vertex))

        if buffer_a == NULL or buffer_b == NULL:
            if buffer_a != NULL: free(buffer_a)
            if buffer_b != NULL: free(buffer_b)
            raise MemoryError("Failed to allocate clipper buffers")

        cdef int i
        cdef Vector2 v_pos, v_uv

        cdef double[:, :] view_verts
        cdef double[:, :] view_uvs

        for i in range(input_count):
            v_pos = <Vector2> input_points[i]
            buffer_a[i].x = v_pos.x
            buffer_a[i].y = v_pos.y

            if has_uvs:
                v_uv = <Vector2> input_uvs[i]
                buffer_a[i].u = v_uv.x
                buffer_a[i].v = v_uv.y
            else:
                buffer_a[i].u = 0.0
                buffer_a[i].v = 0.0

        cdef int count = input_count

        try:
            count = Clipper._clip_axis(buffer_a, count, buffer_b, &capacity, min_x, 0, 1.0)
            count = Clipper._clip_axis(buffer_b, count, buffer_a, &capacity, max_x, 0, -1.0)
            count = Clipper._clip_axis(buffer_a, count, buffer_b, &capacity, min_y, 1, 1.0)
            count = Clipper._clip_axis(buffer_b, count, buffer_a, &capacity, max_y, 1, -1.0)

            if count < 3:
                return np.zeros((0, 2), dtype=np.float64), np.zeros((0, 2), dtype=np.float64)

            result_verts = np.zeros((count, 2), dtype=np.float64)
            result_uvs = np.zeros((count, 2), dtype=np.float64)

            view_verts = result_verts
            view_uvs = result_uvs

            for i in range(count):
                view_verts[i, 0] = buffer_a[i].x
                view_verts[i, 1] = buffer_a[i].y
                view_uvs[i, 0] = buffer_a[i].u
                view_uvs[i, 1] = buffer_a[i].v

            return result_verts, result_uvs

        finally:
            free(buffer_a)
            free(buffer_b)

    @staticmethod
    cdef int _clip_axis(Vertex * input_pts, int input_len, Vertex * output_pts, int * capacity,
                        double boundary, int axis_idx, double sign) nogil:
        if input_len == 0:
            return 0

        cdef int output_len = 0
        cdef Vertex p1 = input_pts[input_len - 1]
        cdef Vertex p2
        cdef double val_p1, val_p2
        cdef bint is_p1_in, is_p2_in
        cdef int i

        for i in range(input_len):
            p2 = input_pts[i]

            val_p1 = p1.x if axis_idx == 0 else p1.y
            val_p2 = p2.x if axis_idx == 0 else p2.y

            is_p1_in = (val_p1 * sign) >= (boundary * sign)
            is_p2_in = (val_p2 * sign) >= (boundary * sign)

            if is_p1_in and is_p2_in:
                output_pts[output_len] = p2
                output_len += 1
            elif is_p1_in and not is_p2_in:
                output_pts[output_len] = Clipper._intersect(p1, p2, boundary, axis_idx)
                output_len += 1
            elif not is_p1_in and is_p2_in:
                output_pts[output_len] = Clipper._intersect(p1, p2, boundary, axis_idx)
                output_len += 1
                output_pts[output_len] = p2
                output_len += 1

            p1 = p2

        return output_len

    @staticmethod
    cdef Vertex _intersect(Vertex p1, Vertex p2, double clip_val, int axis_idx) noexcept nogil:
        cdef double val_p1 = p1.x if axis_idx == 0 else p1.y
        cdef double val_p2 = p2.x if axis_idx == 0 else p2.y
        cdef Vertex res

        cdef double diff = val_p2 - val_p1
        if diff == 0:
            return p1

        cdef double t = (clip_val - val_p1) / diff

        res.x = p1.x + (p2.x - p1.x) * t
        res.y = p1.y + (p2.y - p1.y) * t

        res.u = p1.u + (p2.u - p1.u) * t
        res.v = p1.v + (p2.v - p1.v) * t

        return res
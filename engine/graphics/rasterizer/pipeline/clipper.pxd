# cython: language_level=3, embedsignature=True

cdef struct Vertex:
    double x
    double y
    double u
    double v

cdef class Clipper:
    cdef int INSIDE
    cdef int LEFT
    cdef int RIGHT
    cdef int BOTTOM
    cdef int TOP

    @staticmethod
    cdef int _compute_outcode(double x, double y, double min_x, double min_y, double max_x, double max_y) nogil

    cpdef tuple clip_polygon(self, list input_points, list input_uvs, double min_x, double min_y, double max_x, double max_y)

    cpdef tuple clip_line(self, double x1, double y1, double x2, double y2, double min_x, double min_y, double max_x,
                          double max_y)

    @staticmethod
    cdef int _clip_axis(Vertex * input_pts, int input_len, Vertex * output_pts, int * capacity, double boundary,
                        int axis_idx, double sign) nogil

    @staticmethod
    cdef Vertex _intersect(Vertex p1, Vertex p2, double clip_val, int axis_idx) noexcept nogil
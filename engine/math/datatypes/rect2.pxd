# cython: language_level=3, embedsignature=True

from engine.math.datatypes.vector2 cimport Vector2

cdef class Rect2:
    cdef public Vector2 position
    cdef public Vector2 size

    cpdef bint has_point(self, Vector2 point)
    cpdef bint intersects(self, Rect2 other, bint include_borders=*)
    cpdef bint encloses(self, Rect2 other)
    cpdef Rect2 intersection(self, Rect2 other)
    cpdef Rect2 merge(self, Rect2 other)
    cpdef Rect2 expand(self, Vector2 vector)
    cpdef Rect2 grow(self, double amount)
    cpdef Rect2 grow_side(self, int side, double amount)
    cpdef double get_area(self)
    cpdef Vector2 get_center(self)
    cpdef Vector2 get_end(self)
    cpdef bint is_equal_approx(self, Rect2 other)
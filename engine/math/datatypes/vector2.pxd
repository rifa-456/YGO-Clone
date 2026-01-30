# cython: language_level=3, embedsignature=True

cdef class Vector2:
    cdef public double x
    cdef public double y

    cdef double length_c(self) nogil
    cdef double length_squared_c(self) nogil
    cdef double dot_c(self, Vector2 other) nogil
    cdef double cross_c(self, Vector2 other) nogil

    cdef Vector2 normalized_c(self)
    cdef Vector2 rotated_c(self, double phi)
    cdef Vector2 lerp_c(self, Vector2 to, double weight)

    cpdef double length(self)
    cpdef double length_squared(self)
    cpdef double angle(self)
    cpdef double dot(self, Vector2 other)
    cpdef double cross(self, Vector2 other)
    cpdef Vector2 normalized(self)
    cpdef Vector2 rotated(self, double phi)
    cpdef Vector2 orthogonal(self)
    cpdef Vector2 lerp(self, Vector2 to, double weight)
    cpdef Vector2 direction_to(self, Vector2 other)
    cpdef double distance_to(self, Vector2 other)
    cpdef double distance_squared_to(self, Vector2 other)
    cpdef bint is_equal_approx(self, Vector2 other)
# cython: language_level=3, embedsignature=True

cdef class Color:
    cdef public double r
    cdef public double g
    cdef public double b
    cdef public double a

    cpdef tuple to_u8(self)
    cpdef Color lerp(self, Color to, double weight)
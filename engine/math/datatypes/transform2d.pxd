# cython: language_level=3, embedsignature=True
from engine.math.datatypes.vector2 cimport Vector2

cdef class Transform2D:
    cdef public Vector2 x
    cdef public Vector2 y
    cdef public Vector2 origin

    cdef Vector2 basis_xform_c(self, Vector2 v)
    cdef Vector2 basis_xform_inv_c(self, Vector2 v)
    cdef Vector2 xform_c(self, Vector2 v)
    cdef Vector2 xform_inv_c(self, Vector2 v)

    cpdef Vector2 xform(self, Vector2 v)
    cpdef Vector2 xform_inv(self, Vector2 v)

    cpdef double tdotx(self, Vector2 v)
    cpdef double tdoty(self, Vector2 v)
    cpdef Vector2 basis_xform(self, Vector2 v)
    cpdef Vector2 basis_xform_inv(self, Vector2 v)
    cpdef Transform2D inverse(self)
    cpdef Transform2D affine_inverse(self)

    cpdef Transform2D translated(self, Vector2 offset)
    cpdef Transform2D scaled(self, Vector2 scale)
    cpdef Transform2D rotated(self, double phi)

    cpdef double get_rotation(self)
    cpdef Vector2 get_scale(self)
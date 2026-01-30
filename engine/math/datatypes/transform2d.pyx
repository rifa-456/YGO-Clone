# cython: language_level=3, embedsignature=True
from libc.math cimport sin, cos, atan2
from engine.math.datatypes.vector2 cimport Vector2

cdef class Transform2D:
    """
      [ x.x  y.x  origin.x ]
      [ x.y  y.y  origin.y ]
      [  0    0       1    ]
    """

    def __cinit__(self, p1=0.0, p2=0.0, p3=None):
        cdef double rotation
        cdef double c
        cdef double s

        if isinstance(p1, Transform2D):
            self.x = (<Transform2D>p1).x
            self.y = (<Transform2D>p1).y
            self.origin = (<Transform2D>p1).origin

        elif isinstance(p1, Vector2) and isinstance(p2, Vector2) and isinstance(p3, Vector2):
            self.x = <Vector2>p1
            self.y = <Vector2>p2
            self.origin = <Vector2>p3

        else:
            try:
                rotation = float(p1)
            except (ValueError, TypeError):
                rotation = 0.0

            if isinstance(p2, Vector2):
                self.origin = <Vector2>p2
            else:
                self.origin = Vector2(0, 0)

            c = cos(rotation)
            s = sin(rotation)

            self.x = Vector2(c, s)
            self.y = Vector2(-s, c)

    @staticmethod
    def identity():
        cdef Transform2D t = Transform2D.__new__(Transform2D)
        t.x = Vector2(1, 0)
        t.y = Vector2(0, 1)
        t.origin = Vector2(0, 0)
        return t

    @staticmethod
    def from_basis(Vector2 x_axis, Vector2 y_axis, Vector2 origin):
        cdef Transform2D t = Transform2D.__new__(Transform2D)
        t.x = x_axis
        t.y = y_axis
        t.origin = origin
        return t

    def __repr__(self):
        return f"Transform2D(X={self.x}, Y={self.y}, O={self.origin})"

    def __mul__(self, object other):
        cdef Transform2D t_other
        cdef Vector2 new_x, new_y, new_origin

        if isinstance(other, Transform2D):
            t_other = <Transform2D> other

            new_x = Vector2(
                self.x.x * t_other.x.x + self.y.x * t_other.x.y,
                self.x.y * t_other.x.x + self.y.y * t_other.x.y
            )

            new_y = Vector2(
                self.x.x * t_other.y.x + self.y.x * t_other.y.y,
                self.x.y * t_other.y.x + self.y.y * t_other.y.y
            )

            new_origin = self.xform_c(t_other.origin)

            return Transform2D.from_basis(new_x, new_y, new_origin)

        elif isinstance(other, Vector2):
            return self.xform_c(<Vector2> other)

        return NotImplemented

    def __matmul__(self, object other):
        """
        Python matrix multiplication operator (@).
        Aliases to __mul__ behavior for compatibility.
        """
        return self.__mul__(other)

    cdef Vector2 basis_xform_c(self, Vector2 v):
        return Vector2(
            self.x.x * v.x + self.y.x * v.y,
            self.x.y * v.x + self.y.y * v.y
        )

    cdef Vector2 basis_xform_inv_c(self, Vector2 v):
        return Vector2(self.x.dot_c(v), self.y.dot_c(v))

    cdef Vector2 xform_c(self, Vector2 v):
        return Vector2(
            self.x.x * v.x + self.y.x * v.y + self.origin.x,
            self.x.y * v.x + self.y.y * v.y + self.origin.y
        )

    cdef Vector2 xform_inv_c(self, Vector2 v):
        cdef Vector2 v_offset
        v_offset = Vector2(v.x - self.origin.x, v.y - self.origin.y)
        return Vector2(self.x.dot_c(v_offset), self.y.dot_c(v_offset))

    cpdef Vector2 xform(self, Vector2 v):
        """
        Transforms the vector v by this transform.
        Logic: M * v
        """
        return self.xform_c(v)

    cpdef Vector2 xform_inv(self, Vector2 v):
        """
        Inverse transforms the vector v by this transform.
        Logic: inv(M) * v
        """
        return self.xform_inv_c(v)

    cpdef double tdotx(self, Vector2 v):
        return self.x.x * v.x + self.x.y * v.y

    cpdef double tdoty(self, Vector2 v):
        return self.y.x * v.x + self.y.y * v.y

    cpdef Vector2 basis_xform(self, Vector2 v):
        return self.basis_xform_c(v)

    cpdef Vector2 basis_xform_inv(self, Vector2 v):
        return self.basis_xform_inv_c(v)

    cpdef Transform2D inverse(self):
        cdef double det = self.x.x * self.y.y - self.x.y * self.y.x
        if det == 0:
            raise ValueError("Transform2D determinant is zero.")

        cdef double idet = 1.0 / det

        cdef Vector2 inv_x = Vector2(self.y.y * idet, -self.y.x * idet)
        cdef Vector2 inv_y = Vector2(-self.x.y * idet, self.x.x * idet)

        cdef double ox = self.origin.x
        cdef double oy = self.origin.y

        cdef Vector2 new_origin = Vector2(
            -(inv_x.x * ox + inv_y.x * oy),
            -(inv_x.y * ox + inv_y.y * oy)
        )

        return Transform2D.from_basis(inv_x, inv_y, new_origin)

    cpdef Transform2D affine_inverse(self):
        return self.inverse()

    cpdef Transform2D translated(self, Vector2 offset):
        return Transform2D.from_basis(self.x, self.y, self.origin + offset)

    cpdef Transform2D scaled(self, Vector2 scale):
        return Transform2D.from_basis(self.x * scale.x, self.y * scale.y, self.origin)

    cpdef Transform2D rotated(self, double phi):
        cdef Transform2D rot = Transform2D(phi, Vector2(0, 0))
        return self.__mul__(rot)

    cpdef double get_rotation(self):
        return atan2(self.x.y, self.x.x)

    cpdef Vector2 get_scale(self):
        return Vector2(self.x.length(), self.y.length())
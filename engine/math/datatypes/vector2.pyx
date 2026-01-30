# cython: language_level=3, embedsignature=True

from libc.math cimport sqrt, sin, cos, atan2

cdef class Vector2:
    """
    High-performance 2D Vector type.
    """

    def __cinit__(self, p1=0.0, p2=0.0):
        if isinstance(p1, Vector2):
            self.x = (<Vector2>p1).x
            self.y = (<Vector2>p1).y

        else:
            self.x = float(p1)
            self.y = float(p2)

    def __repr__(self):
        return f"Vector2({self.x:.3f}, {self.y:.3f})"

    def __add__(self, object other):
        if isinstance(other, Vector2):
            return Vector2(self.x + (<Vector2> other).x, self.y + (<Vector2> other).y)
        return NotImplemented

    def __sub__(self, object other):
        if isinstance(other, Vector2):
            return Vector2(self.x - (<Vector2> other).x, self.y - (<Vector2> other).y)
        return NotImplemented

    def __neg__(self):
        return Vector2(-self.x, -self.y)

    def __mul__(self, object other):
        cdef double scalar
        if isinstance(other, (int, float)):
            scalar = <double> other
            return Vector2(self.x * scalar, self.y * scalar)
        elif isinstance(other, Vector2):
            return Vector2(self.x * (<Vector2> other).x, self.y * (<Vector2> other).y)
        return NotImplemented

    def __truediv__(self, object other):
        cdef double scalar
        cdef Vector2 v_other

        if isinstance(other, (int, float)):
            scalar = <double> other
            if scalar == 0:
                raise ZeroDivisionError("Vector2 division by zero")
            return Vector2(self.x / scalar, self.y / scalar)
        elif isinstance(other, Vector2):
            v_other = <Vector2> other
            if v_other.x == 0 or v_other.y == 0:
                raise ZeroDivisionError("Vector2 division by zero")
            return Vector2(self.x / v_other.x, self.y / v_other.y)
        return NotImplemented

    def __eq__(self, object other):
        if not isinstance(other, Vector2):
            return False
        return self.x == (<Vector2> other).x and self.y == (<Vector2> other).y

    cdef double length_c(self) nogil:
        return sqrt(self.x * self.x + self.y * self.y)

    cdef double length_squared_c(self) nogil:
        return self.x * self.x + self.y * self.y

    cdef double dot_c(self, Vector2 other) nogil:
        return self.x * other.x + self.y * other.y

    cdef double cross_c(self, Vector2 other) nogil:
        return self.x * other.y - self.y * other.x

    cdef Vector2 normalized_c(self):
        cdef double l = self.length_c()
        if l == 0:
            return Vector2(0, 0)
        return Vector2(self.x / l, self.y / l)

    cdef Vector2 rotated_c(self, double phi):
        cdef double c = cos(phi)
        cdef double s = sin(phi)
        return Vector2(self.x * c - self.y * s, self.x * s + self.y * c)

    cdef Vector2 lerp_c(self, Vector2 to, double weight):
        return Vector2(
            self.x + (to.x - self.x) * weight,
            self.y + (to.y - self.y) * weight
        )

    cpdef double length(self):
        return self.length_c()

    cpdef double length_squared(self):
        return self.length_squared_c()

    cpdef double angle(self):
        return atan2(self.y, self.x)

    cpdef double dot(self, Vector2 other):
        return self.dot_c(other)

    cpdef double cross(self, Vector2 other):
        return self.cross_c(other)

    cpdef Vector2 normalized(self):
        return self.normalized_c()

    cpdef Vector2 rotated(self, double phi):
        return self.rotated_c(phi)

    cpdef Vector2 orthogonal(self):
        return Vector2(self.y, -self.x)

    cpdef Vector2 lerp(self, Vector2 to, double weight):
        return self.lerp_c(to, weight)

    cpdef Vector2 direction_to(self, Vector2 other):
        cdef Vector2 ret = Vector2(other.x - self.x, other.y - self.y)
        return ret.normalized()

    cpdef double distance_to(self, Vector2 other):
        return sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)

    cpdef double distance_squared_to(self, Vector2 other):
        return (self.x - other.x) ** 2 + (self.y - other.y) ** 2

    def to_tuple(self):
        return self.x, self.y

    cpdef bint is_equal_approx(self, Vector2 other):
        cdef double epsilon = 0.00001
        return abs(self.x - other.x) < epsilon and abs(self.y - other.y) < epsilon
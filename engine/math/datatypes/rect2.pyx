# cython: language_level=3, embedsignature=True
# cython: boundscheck=False
# cython: wraparound=False

from engine.math.datatypes.vector2 cimport Vector2

cdef class Rect2:
    """
    2D Axis-Aligned Bounding Box.
    Supports initialization via:
    - Rect2(x, y, width, height)
    - Rect2(position: Vector2, size: Vector2)
    - Rect2(other: Rect2)
    """

    def __cinit__(self, p1=0, p2=0, p3=0, p4=0):
        if isinstance(p1, Vector2) and isinstance(p2, Vector2):
            self.position = <Vector2> p1
            self.size = <Vector2> p2

        elif isinstance(p1, Rect2):
            self.position = (<Rect2> p1).position
            self.size = (<Rect2> p1).size

        else:
            self.position = Vector2(float(p1), float(p2))
            self.size = Vector2(float(p3), float(p4))

    def __init__(self, *args, **kwargs):
        pass

    def __repr__(self):
        return f"Rect2(P={self.position}, S={self.size})"

    def __eq__(self, object other):
        if not isinstance(other, Rect2):
            return False
        cdef Rect2 o = <Rect2> other
        return self.position == o.position and self.size == o.size

    @property
    def end(self):
        return self.get_end()

    @property
    def center(self):
        return self.get_center()

    cpdef Vector2 get_end(self):
        return Vector2(self.position.x + self.size.x, self.position.y + self.size.y)

    cpdef Vector2 get_center(self):
        return Vector2(self.position.x + self.size.x * 0.5, self.position.y + self.size.y * 0.5)

    cpdef double get_area(self):
        return self.size.x * self.size.y

    cpdef bint has_point(self, Vector2 point):
        if point.x < self.position.x: return False
        if point.y < self.position.y: return False
        if point.x >= (self.position.x + self.size.x): return False
        if point.y >= (self.position.y + self.size.y): return False
        return True

    cpdef bint intersects(self, Rect2 other, bint include_borders=False):
        if include_borders:
            if self.position.x > (other.position.x + other.size.x): return False
            if (self.position.x + self.size.x) < other.position.x: return False
            if self.position.y > (other.position.y + other.size.y): return False
            if (self.position.y + self.size.y) < other.position.y: return False
            return True
        else:
            if self.position.x >= (other.position.x + other.size.x): return False
            if (self.position.x + self.size.x) <= other.position.x: return False
            if self.position.y >= (other.position.y + other.size.y): return False
            if (self.position.y + self.size.y) <= other.position.y: return False
            return True

    cpdef bint encloses(self, Rect2 other):
        return (other.position.x >= self.position.x) and \
            (other.position.y >= self.position.y) and \
            ((other.position.x + other.size.x) <= (self.position.x + self.size.x)) and \
            ((other.position.y + other.size.y) <= (self.position.y + self.size.y))

    cpdef Rect2 intersection(self, Rect2 other):
        cdef Rect2 new_rect = Rect2(0, 0, 0, 0)

        if not self.intersects(other):
            return new_rect

        cdef double new_x = max(self.position.x, other.position.x)
        cdef double new_y = max(self.position.y, other.position.y)

        cdef double self_end_x = self.position.x + self.size.x
        cdef double other_end_x = other.position.x + other.size.x
        cdef double new_end_x = min(self_end_x, other_end_x)

        cdef double self_end_y = self.position.y + self.size.y
        cdef double other_end_y = other.position.y + other.size.y
        cdef double new_end_y = min(self_end_y, other_end_y)

        new_rect.position = Vector2(new_x, new_y)
        new_rect.size = Vector2(new_end_x - new_x, new_end_y - new_y)

        return new_rect

    cpdef Rect2 merge(self, Rect2 other):
        cdef double min_x = min(self.position.x, other.position.x)
        cdef double min_y = min(self.position.y, other.position.y)

        cdef double max_x = max(self.position.x + self.size.x, other.position.x + other.size.x)
        cdef double max_y = max(self.position.y + self.size.y, other.position.y + other.size.y)

        return Rect2(min_x, min_y, max_x - min_x, max_y - min_y)

    cpdef Rect2 expand(self, Vector2 vector):
        cdef Rect2 r = Rect2(self.position.x, self.position.y, self.size.x, self.size.y)

        if vector.x < r.position.x:
            r.position.x = vector.x
            r.size.x += (self.position.x - vector.x)
        elif vector.x > (r.position.x + r.size.x):
            r.size.x = vector.x - r.position.x

        if vector.y < r.position.y:
            r.position.y = vector.y
            r.size.y += (self.position.y - vector.y)
        elif vector.y > (r.position.y + r.size.y):
            r.size.y = vector.y - r.position.y

        return r

    cpdef Rect2 grow(self, double amount):
        return Rect2(
            self.position.x - amount,
            self.position.y - amount,
            self.size.x + amount * 2,
            self.size.y + amount * 2
        )

    cpdef Rect2 grow_side(self, int side, double amount):
        cdef Rect2 r = Rect2(self.position.x, self.position.y, self.size.x, self.size.y)
        if side == 0:
            r.position.x -= amount
            r.size.x += amount
        elif side == 1:
            r.position.y -= amount
            r.size.y += amount
        elif side == 2:
            r.size.x += amount
        elif side == 3:
            r.size.y += amount
        return r

    cpdef bint is_equal_approx(self, Rect2 other):
        return self.position.is_equal_approx(other.position) and self.size.is_equal_approx(other.size)
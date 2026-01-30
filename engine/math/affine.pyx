# cython: language_level=3, embedsignature=True
# cython: boundscheck=False
# cython: wraparound=False

from libc.math cimport tan
from engine.math.datatypes.transform2d cimport Transform2D

cpdef Transform2D get_translation(double x, double y):
    """
    Creates a translation matrix.
    [ 1  0  x ]
    [ 0  1  y ]
    [ 0  0  1 ]
    """

    cdef Transform2D t = Transform2D()
    t.origin.x = x
    t.origin.y = y

    return t

cpdef Transform2D get_rotation(double rotation):
    """
    Creates a rotation matrix.
    [ cos -sin  0 ]
    [ sin  cos  0 ]
    [  0    0   1 ]
    """
    return Transform2D(rotation)

cpdef Transform2D get_scale(double x, double y):
    """
    Creates a scaling matrix.
    [ x  0  0 ]
    [ 0  y  0 ]
    [ 0  0  1 ]
    """
    cdef Transform2D t = Transform2D()
    t.x.x = x
    t.y.y = y

    return t

cpdef Transform2D get_skew(double x, double y):
    """
    Creates a skew matrix.
    [   1   tan(y)  0 ]
    [ tan(x)  1     0 ]
    [   0     0     1 ]
    """
    cdef Transform2D t = Transform2D()

    if x != 0.0:
        t.y.x = tan(x)

    if y != 0.0:
        t.x.y = tan(y)

    return t
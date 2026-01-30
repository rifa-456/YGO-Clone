# cython: language_level=3, embedsignature=True

from engine.math.datatypes.transform2d cimport Transform2D

cpdef Transform2D get_translation(double x, double y)
cpdef Transform2D get_rotation(double rotation)
cpdef Transform2D get_scale(double x, double y)
cpdef Transform2D get_skew(double x, double y)
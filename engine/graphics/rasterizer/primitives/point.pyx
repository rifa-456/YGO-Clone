# cython: language_level=3, embedsignature=True
# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True

from engine.graphics.tools.colors cimport uint32, blend_colors
from engine.math.datatypes.vector2 cimport Vector2

def draw_point(uint32[:, :] buffer, int x, int y, uint32 color):
    """
    Draws a single pixel with clipping and blending.
    """
    draw_pixel_c(buffer, x, y, color)

def draw_points(uint32[:, :] buffer, list points, uint32 color):
    """
    Batch draws a list of Vector2 points.
    Much faster than calling draw_point in a loop from Python.
    """
    cdef int w = <int> buffer.shape[0]
    cdef int h = <int> buffer.shape[1]
    cdef int n = len(points)
    cdef int i
    cdef int px, py
    cdef Vector2 v

    # Check bounds once for the whole batch if possible?
    # No, points are arbitrary, must check per point.
    # Inline the check for speed (avoiding function call overhead in loop).

    for i in range(n):
        v = <Vector2> points[i]
        px = <int> v.x
        py = <int> v.y

        if 0 <= px < w and 0 <= py < h:
            buffer[px, py] = blend_colors(color, buffer[px, py])

cdef void draw_pixel_c(uint32[:, :] buffer, int x, int y, uint32 color) noexcept nogil:
    cdef int w = <int> buffer.shape[0]
    cdef int h = <int> buffer.shape[1]

    if 0 <= x < w and 0 <= y < h:
        buffer[x, y] = blend_colors(color, buffer[x, y])
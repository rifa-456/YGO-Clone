# cython: language_level=3, embedsignature=True
# cython: boundscheck=False
# cython: wraparound=False

from engine.graphics.tools.colors cimport uint32, blend_colors

def draw_line(uint32[:, :] buffer, int x0, int y0, int x1, int y1, uint32 color):
    rasterize_line_c(buffer, x0, y0, x1, y1, color)

cdef void rasterize_line_c(uint32[:, :] buffer, int x0, int y0, int x1, int y1, uint32 color) noexcept nogil:
    cdef int w = <int>buffer.shape[0]
    cdef int h = <int>buffer.shape[1]
    cdef int dx = abs(x1 - x0)
    cdef int dy = abs(y1 - y0)
    cdef int sx = 1 if x0 < x1 else -1
    cdef int sy = 1 if y0 < y1 else -1
    cdef int err = dx - dy
    cdef int e2

    while True:
        if 0 <= x0 < w and 0 <= y0 < h:
            buffer[x0, y0] = blend_colors(color, buffer[x0, y0])

        if x0 == x1 and y0 == y1:
            break

        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy
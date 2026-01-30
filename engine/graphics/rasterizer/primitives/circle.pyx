# cython: language_level=3, embedsignature=True
# cython: boundscheck=False
# cython: wraparound=False

from engine.graphics.tools.colors cimport uint32, blend_colors

def draw_circle_filled(uint32[:, :] buffer, int cx, int cy, int r, uint32 color):
    cdef int buf_w = <int>buffer.shape[0]
    cdef int buf_h = <int>buffer.shape[1]
    cdef int x = 0
    cdef int y = r
    cdef int d = 3 - 2 * r

    while y >= x:
        _scanline_h(buffer, cx - x, cx + x, cy + y, color, buf_w, buf_h)
        _scanline_h(buffer, cx - x, cx + x, cy - y, color, buf_w, buf_h)
        _scanline_h(buffer, cx - y, cx + y, cy + x, color, buf_w, buf_h)
        _scanline_h(buffer, cx - y, cx + y, cy - x, color, buf_w, buf_h)

        x += 1
        if d > 0:
            y -= 1
            d = d + 4 * (x - y) + 10
        else:
            d = d + 4 * x + 6

def draw_circle_outline(uint32[:, :] buffer, int cx, int cy, int r, uint32 color):
    cdef int buf_w = <int>buffer.shape[0]
    cdef int buf_h = <int>buffer.shape[1]
    cdef int x = 0
    cdef int y = r
    cdef int d = 3 - 2 * r

    while y >= x:
        _plot(buffer, cx + x, cy + y, color, buf_w, buf_h)
        _plot(buffer, cx - x, cy + y, color, buf_w, buf_h)
        _plot(buffer, cx + x, cy - y, color, buf_w, buf_h)
        _plot(buffer, cx - x, cy - y, color, buf_w, buf_h)
        _plot(buffer, cx + y, cy + x, color, buf_w, buf_h)
        _plot(buffer, cx - y, cy + x, color, buf_w, buf_h)
        _plot(buffer, cx + y, cy - x, color, buf_w, buf_h)
        _plot(buffer, cx - y, cy - x, color, buf_w, buf_h)

        x += 1
        if d > 0:
            y -= 1
            d = d + 4 * (x - y) + 10
        else:
            d = d + 4 * x + 6

cdef inline void _plot(uint32[:, :] buffer, int x, int y, uint32 color, int w, int h) noexcept nogil:
    if 0 <= x < w and 0 <= y < h:
        buffer[x, y] = blend_colors(color, buffer[x, y])

cdef void _scanline_h(uint32[:, :] buffer, int x1, int x2, int y, uint32 color, int w, int h) noexcept nogil:
    if y < 0 or y >= h:
        return
    if x1 < 0: x1 = 0
    if x2 >= w: x2 = w - 1
    if x1 > x2: return

    cdef int i
    for i in range(x1, x2 + 1):
        buffer[i, y] = blend_colors(color, buffer[i, y])
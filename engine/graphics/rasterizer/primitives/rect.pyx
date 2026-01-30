# cython: language_level=3, embedsignature=True
# cython: boundscheck=False
# cython: wraparound=False

from engine.graphics.tools.colors cimport uint32, blend_colors

def fill_rect(uint32[:, :] buffer, int x, int y, int w, int h, uint32 color):
    rasterize_rect_filled_c(buffer, x, y, w, h, color)

def draw_rect_outline(uint32[:, :] buffer, int x, int y, int w, int h, uint32 color, int thickness):
    # Top
    rasterize_rect_filled_c(buffer, x, y, w, thickness, color)
    # Bottom
    rasterize_rect_filled_c(buffer, x, y + h - thickness, w, thickness, color)
    # Left
    rasterize_rect_filled_c(buffer, x, y + thickness, thickness, h - 2 * thickness, color)
    # Right
    rasterize_rect_filled_c(buffer, x + w - thickness, y + thickness, thickness, h - 2 * thickness, color)

cdef void rasterize_rect_filled_c(uint32[:, :] buffer, int x, int y, int w, int h, uint32 color) noexcept nogil:
    cdef int buf_w = <int>buffer.shape[0]
    cdef int buf_h = <int>buffer.shape[1]
    if x < 0:
        w += x
        x = 0
    if y < 0:
        h += y
        y = 0
    if x + w > buf_w:
        w = buf_w - x
    if y + h > buf_h:
        h = buf_h - y

    if w <= 0 or h <= 0:
        return

    cdef int i, j
    cdef int alpha = (color >> 24) & 0xFF

    if alpha == 255:
        for i in range(x, x + w):
            for j in range(y, y + h):
                buffer[i, j] = color
    elif alpha > 0:
        for i in range(x, x + w):
            for j in range(y, y + h):
                buffer[i, j] = blend_colors(color, buffer[i, j])
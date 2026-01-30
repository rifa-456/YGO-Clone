# cython: language_level=3, embedsignature=True
# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True

from libc.math cimport floor
from engine.graphics.tools.colors cimport uint32, uint8, unpack_rgba, pack_rgba

cdef inline int wrap_coord(int val, int max_dim) noexcept nogil:
    """
    Handles wrapping for texture coordinates (Repeat Mode).
    Handles negative values correctly: wrap_coord(-1, 10) -> 9.
    """
    return (val % max_dim + max_dim) % max_dim

cdef uint32 sample_nearest(uint32[:, :] tex_data, int w, int h, float u, float v) noexcept nogil:
    """
    Nearest-Neighbor filtering. Fast, blocky.
    """
    u = u - floor(u)
    v = v - floor(v)

    cdef int x = <int> (u * w)
    cdef int y = <int> (v * h)

    if x >= w: x = w - 1
    if y >= h: y = h - 1

    if x < 0: x = 0
    if y < 0: y = 0

    return tex_data[x, y]

cdef uint32 sample_bilinear(uint32[:, :] tex_data, int w, int h, float u, float v) noexcept nogil:
    """
    Bilinear filtering. Smooths pixels by interpolating the 4 nearest neighbors.
    """
    u = u - floor(u)
    v = v - floor(v)

    cdef float px = u * w - 0.5
    cdef float py = v * h - 0.5

    cdef int x0 = <int> floor(px)
    cdef int y0 = <int> floor(py)
    cdef int x1 = x0 + 1
    cdef int y1 = y0 + 1

    cdef float wx = px - x0
    cdef float wy = py - y0

    cdef float inv_wx = <float>1.0 - wx
    cdef float inv_wy = <float>1.0 - wy

    x0 = wrap_coord(x0, w)
    x1 = wrap_coord(x1, w)
    y0 = wrap_coord(y0, h)
    y1 = wrap_coord(y1, h)

    cdef uint32 c00 = tex_data[x0, y0]
    cdef uint32 c10 = tex_data[x1, y0]
    cdef uint32 c01 = tex_data[x0, y1]
    cdef uint32 c11 = tex_data[x1, y1]

    cdef uint8 r00, g00, b00, a00
    cdef uint8 r10, g10, b10, a10
    cdef uint8 r01, g01, b01, a01
    cdef uint8 r11, g11, b11, a11

    unpack_rgba(c00, &r00, &g00, &b00, &a00)
    unpack_rgba(c10, &r10, &g10, &b10, &a10)
    unpack_rgba(c01, &r01, &g01, &b01, &a01)
    unpack_rgba(c11, &r11, &g11, &b11, &a11)

    cdef float top_r = r00 * inv_wx + r10 * wx
    cdef float top_g = g00 * inv_wx + g10 * wx
    cdef float top_b = b00 * inv_wx + b10 * wx
    cdef float top_a = a00 * inv_wx + a10 * wx

    cdef float bot_r = r01 * inv_wx + r11 * wx
    cdef float bot_g = g01 * inv_wx + g11 * wx
    cdef float bot_b = b01 * inv_wx + b11 * wx
    cdef float bot_a = a01 * inv_wx + a11 * wx

    cdef uint8 final_r = <uint8> (top_r * inv_wy + bot_r * wy)
    cdef uint8 final_g = <uint8> (top_g * inv_wy + bot_g * wy)
    cdef uint8 final_b = <uint8> (top_b * inv_wy + bot_b * wy)
    cdef uint8 final_a = <uint8> (top_a * inv_wy + bot_a * wy)

    return pack_rgba(final_r, final_g, final_b, final_a)
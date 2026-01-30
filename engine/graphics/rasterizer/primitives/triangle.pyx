# cython: language_level=3, embedsignature=True
# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True

from engine.graphics.tools.colors cimport uint32, blend_colors
from engine.graphics.rasterizer.samplers.samplers cimport sample_nearest, sample_bilinear

def draw_triangle_textured(
        uint32[:, :] buffer,
        double[:, :] vertices,
        double[:, :] uvs,
        uint32[:, :] texture,
        int tex_w, int tex_h,
        bint use_bilinear
):
    cdef int w = <int>buffer.shape[0]
    cdef int h = <int>buffer.shape[1]

    cdef double x0 = vertices[0, 0], y0 = vertices[0, 1]
    cdef double x1 = vertices[1, 0], y1 = vertices[1, 1]
    cdef double x2 = vertices[2, 0], y2 = vertices[2, 1]

    cdef double u0 = uvs[0, 0], v0 = uvs[0, 1]
    cdef double u1 = uvs[1, 0], v1 = uvs[1, 1]
    cdef double u2 = uvs[2, 0], v2 = uvs[2, 1]

    if y0 > y1:
        x0, x1 = x1, x0
        y0, y1 = y1, y0
        u0, u1 = u1, u0
        v0, v1 = v1, v0
    if y0 > y2:
        x0, x2 = x2, x0
        y0, y2 = y2, y0
        u0, u2 = u2, u0
        v0, v2 = v2, v0
    if y1 > y2:
        x1, x2 = x2, x1
        y1, y2 = y2, y1
        u1, u2 = u2, u1
        v1, v2 = v2, v1

    cdef int total_height = <int> (y2 - y0)
    if total_height == 0: return

    cdef int i, y
    cdef double alpha, beta
    cdef double ax, au, av
    cdef double bx, bu, bv
    cdef int start_x, end_x
    cdef double t_step, t_curr, tu, tv
    cdef uint32 src

    for i in range(total_height):
        y = <int> y0 + i
        if y >= h: break
        if y < 0: continue

        alpha = <double> i / total_height

        ax = x0 + (x2 - x0) * alpha
        au = u0 + (u2 - u0) * alpha
        av = v0 + (v2 - v0) * alpha

        if i < (y1 - y0):
            beta = <double> i / (y1 - y0) if (y1 - y0) != 0 else 0
            bx = x0 + (x1 - x0) * beta
            bu = u0 + (u1 - u0) * beta
            bv = v0 + (v1 - v0) * beta
        else:
            beta = <double> (i - (y1 - y0)) / (y2 - y1) if (y2 - y1) != 0 else 0
            bx = x1 + (x2 - x1) * beta
            bu = u1 + (u2 - u1) * beta
            bv = v1 + (v2 - v1) * beta

        if ax > bx:
            ax, bx = bx, ax
            au, bu = bu, au
            av, bv = bv, av

        start_x = <int> ax
        end_x = <int> bx

        if end_x > start_x:
            t_step = 1.0 / (end_x - start_x)
        else:
            t_step = 0.0

        t_curr = 0.0

        for x in range(start_x, end_x):
            if x >= 0 and x < w:
                tu = au + (bu - au) * t_curr
                tv = av + (bv - av) * t_curr

                if use_bilinear:
                    src = sample_bilinear(texture, tex_w, tex_h, <float>tu, <float>tv)
                else:
                    src = sample_nearest(texture, tex_w, tex_h, <float>tu, <float>tv)

                buffer[x, y] = blend_colors(src, buffer[x, y])

            t_curr += t_step
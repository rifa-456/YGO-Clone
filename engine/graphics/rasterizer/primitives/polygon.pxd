# cython: language_level=3, embedsignature=True
from engine.graphics.tools.colors cimport uint32

cpdef void draw_polygon_filled(uint32[:, :] buffer, double[:, :] vertices, uint32 color)

cpdef void draw_polygon_outline(uint32[:, :] buffer, double[:, :] vertices, uint32 color)

cpdef void draw_polygon_textured(
    uint32[:, :] buffer,
    double[:, :] vertices,
    double[:, :] uvs,
    uint32[:, :] texture,
    int tex_w,
    int tex_h,
    uint32 modulate
)
# cython: language_level=3, embedsignature=True
from engine.graphics.tools.colors cimport uint32

cdef void rasterize_rect_filled_c(uint32[:, :] buffer, int x, int y, int w, int h, uint32 color) noexcept nogil
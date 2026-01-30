# cython: language_level=3, embedsignature=True
from engine.graphics.tools.colors cimport uint32

cdef void _scanline_h(uint32[:, :] buffer, int x1, int x2, int y, uint32 color, int w, int h) noexcept nogil
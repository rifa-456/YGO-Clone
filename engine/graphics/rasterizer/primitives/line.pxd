# cython: language_level=3, embedsignature=True
from engine.graphics.tools.colors cimport uint32

# Expose C-level function for other Cython modules
cdef void rasterize_line_c(uint32[:, :] buffer, int x0, int y0, int x1, int y1, uint32 color) noexcept nogil
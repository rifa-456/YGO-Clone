# cython: language_level=3, embedsignature=True
from engine.graphics.tools.colors cimport uint32

# Expose C-level function for internal usage (e.g. by other primitives)
cdef void draw_pixel_c(uint32[:, :] buffer, int x, int y, uint32 color) noexcept nogil
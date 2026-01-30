# cython: language_level=3, embedsignature=True

from engine.graphics.tools.colors cimport uint32

cdef uint32 sample_nearest(uint32[:, :] tex_data, int w, int h, float u, float v) noexcept nogil
cdef uint32 sample_bilinear(uint32[:, :] tex_data, int w, int h, float u, float v) noexcept nogil
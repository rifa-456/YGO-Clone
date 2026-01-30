# cython: language_level=3

ctypedef unsigned int uint32
ctypedef unsigned char uint8

cdef inline uint32 pack_rgba(uint8 r, uint8 g, uint8 b, uint8 a) noexcept nogil:
    return (a << 24) | (r << 16) | (g << 8) | b

cdef inline void unpack_rgba(uint32 color, uint8 * r, uint8 * g, uint8 * b, uint8 * a) noexcept nogil:
    a[0] = (color >> 24) & 0xFF
    r[0] = (color >> 16) & 0xFF
    g[0] = (color >> 8) & 0xFF
    b[0] = color & 0xFF

cdef inline uint32 blend_colors(uint32 src, uint32 dst) noexcept nogil:
    cdef uint8 sr, sg, sb, sa
    cdef uint8 dr, dg, db, da
    if (src >> 24) == 0:
        return dst

    if (src >> 24) == 255:
        return src

    unpack_rgba(src, &sr, &sg, &sb, &sa)
    unpack_rgba(dst, &dr, &dg, &db, &da)
    cdef uint32 inv_a = 255 - sa

    cdef uint8 out_r = (sr * sa + dr * inv_a) >> 8
    cdef uint8 out_g = (sg * sa + dg * inv_a) >> 8
    cdef uint8 out_b = (sb * sa + db * inv_a) >> 8

    cdef uint8 out_a = sa + ((da * inv_a) >> 8)

    return pack_rgba(out_r, out_g, out_b, out_a)
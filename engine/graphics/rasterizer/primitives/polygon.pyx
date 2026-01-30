# cython: language_level=3, embedsignature=True
# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True

from libc.stdlib cimport malloc, free, qsort
from libc.string cimport memset
from engine.graphics.tools.colors cimport uint32, blend_colors
from engine.graphics.rasterizer.primitives.line cimport rasterize_line_c
from engine.graphics.rasterizer.samplers.samplers cimport sample_nearest

cdef struct Edge:
    int y_max
    double x
    double dx
    double u
    double du
    double v
    double dv
    Edge * next

cdef struct ActiveEdge:
    int y_max
    double x
    double dx
    double u
    double du
    double v
    double dv

cdef int compare_edges(const void * a, const void * b) noexcept nogil:
    cdef ActiveEdge * edge_a = <ActiveEdge *> a
    cdef ActiveEdge * edge_b = <ActiveEdge *> b
    if edge_a.x < edge_b.x:
        return -1
    elif edge_a.x > edge_b.x:
        return 1
    return 0

cpdef void draw_polygon_filled(uint32[:, :] buffer, double[:, :] vertices, uint32 color):
    """
    High-performance Scanline Fill (Non-Zero Winding not guaranteed, standard Even-Odd).
    Entirely C-level with manual memory management.
    """
    # --- DECLARATIONS START ---
    cdef int w = buffer.shape[0]
    cdef int h = buffer.shape[1]
    cdef int num_verts = vertices.shape[0]
    cdef int y_min_global = h
    cdef int y_max_global = 0
    cdef int i
    cdef double py

    cdef Edge** GET
    cdef int edges_count = 0
    cdef double p1x, p1y, p2x, p2y
    cdef int y_start, y_end
    cdef double inverse_slope
    cdef Edge * new_edge

    # Hoisted variables that caused errors previously
    cdef ActiveEdge * AET
    cdef int aet_count = 0
    cdef int y
    cdef int j, k
    cdef int x_start, x_end
    cdef Edge * current_node
    cdef Edge * temp_node
    # --- DECLARATIONS END ---

    if num_verts < 3:
        return

    for i in range(num_verts):
        py = vertices[i, 1]
        if py < y_min_global: y_min_global = <int> py
        if py > y_max_global: y_max_global = <int> py

    if y_min_global < 0: y_min_global = 0
    if y_max_global >= h: y_max_global = h - 1
    if y_min_global > y_max_global: return

    GET = <Edge**> malloc(h * sizeof(Edge *))
    if GET == NULL: return
    memset(GET, 0, h * sizeof(Edge *))

    with nogil:
        for i in range(num_verts):
            p1x = vertices[i, 0]
            p1y = vertices[i, 1]
            p2x = vertices[(i + 1) % num_verts, 0]
            p2y = vertices[(i + 1) % num_verts, 1]

            if <int> p1y == <int> p2y:
                continue

            if p1y > p2y:
                p1x, p2x = p2x, p1x
                p1y, p2y = p2y, p1y

            y_start = <int> p1y
            y_end = <int> p2y

            if y_start >= h or y_end < 0:
                continue

            inverse_slope = (p2x - p1x) / (p2y - p1y)
            new_edge = <Edge *> malloc(sizeof(Edge))
            new_edge.y_max = y_end
            new_edge.x = p1x
            new_edge.dx = inverse_slope
            new_edge.next = GET[y_start]
            GET[y_start] = new_edge
            edges_count += 1

        # Execution logic (Variable declarations must be above this)
        AET = <ActiveEdge *> malloc(edges_count * sizeof(ActiveEdge))

        for y in range(y_min_global, y_max_global + 1):
            current_node = GET[y]
            while current_node != NULL:
                if aet_count < edges_count:
                    AET[aet_count].y_max = current_node.y_max
                    AET[aet_count].x = current_node.x
                    AET[aet_count].dx = current_node.dx
                    aet_count += 1

                temp_node = current_node
                current_node = current_node.next
                free(temp_node)

            GET[y] = NULL

            k = 0
            for j in range(aet_count):
                if AET[j].y_max > y:
                    AET[k] = AET[j]
                    k += 1
            aet_count = k

            qsort(AET, aet_count, sizeof(ActiveEdge), compare_edges)

            for j in range(0, aet_count - 1, 2):
                x_start = <int> AET[j].x
                x_end = <int> AET[j + 1].x

                if x_start < 0: x_start = 0
                if x_end > w: x_end = w

                if x_start < x_end:
                    for k in range(x_start, x_end):
                        buffer[k, y] = blend_colors(color, buffer[k, y])

            for j in range(aet_count):
                AET[j].x += AET[j].dx

        free(AET)
        free(GET)

cpdef void draw_polygon_outline(uint32[:, :] buffer, double[:, :] vertices, uint32 color):
    """
    Batched line drawing for polygon outline.
    """
    cdef int num_verts = vertices.shape[0]
    cdef int i
    cdef double p1x, p1y, p2x, p2y

    with nogil:
        for i in range(num_verts):
            p1x = vertices[i, 0]
            p1y = vertices[i, 1]
            p2x = vertices[(i + 1) % num_verts, 0]
            p2y = vertices[(i + 1) % num_verts, 1]

            rasterize_line_c(buffer, <int> p1x, <int> p1y, <int> p2x, <int> p2y, color)

cpdef void draw_polygon_textured(uint32[:, :] buffer, double[:, :] vertices, double[:, :] uvs,
                                 uint32[:, :] texture, int tex_w, int tex_h, uint32 modulate):
    """
    Affine Texture Mapping Scanline Rasterizer.
    Completely rewritten for raw C performance.
    """
    # --- DECLARATIONS START ---
    cdef int w = buffer.shape[0]
    cdef int h = buffer.shape[1]
    cdef int num_verts = vertices.shape[0]
    cdef int y_min_global = h
    cdef int y_max_global = 0
    cdef int i
    cdef double py

    cdef Edge** GET
    cdef int edges_count = 0
    cdef double p1x, p1y, p2x, p2y
    cdef double u1, v1, u2, v2
    cdef int y_start, y_end
    cdef double dy_inv
    cdef Edge * new_edge

    # Hoisted variables
    cdef ActiveEdge * AET
    cdef int aet_count = 0
    cdef int y, j, k, x, x_start, x_end
    cdef Edge * current_node
    cdef Edge * temp_node
    cdef double u_start, u_end, v_start, v_end
    cdef double cur_u, cur_v, du_dx, dv_dx, span_width
    cdef uint32 tex_col
    # --- DECLARATIONS END ---

    if num_verts < 3: return

    for i in range(num_verts):
        py = vertices[i, 1]
        if py < y_min_global: y_min_global = <int> py
        if py > y_max_global: y_max_global = <int> py

    if y_min_global < 0: y_min_global = 0
    if y_max_global >= h: y_max_global = h - 1
    if y_min_global > y_max_global: return

    GET = <Edge**> malloc(h * sizeof(Edge *))
    if GET == NULL: return
    memset(GET, 0, h * sizeof(Edge *))

    with nogil:
        for i in range(num_verts):
            p1x = vertices[i, 0]
            p1y = vertices[i, 1]
            u1 = uvs[i, 0]
            v1 = uvs[i, 1]

            p2x = vertices[(i + 1) % num_verts, 0]
            p2y = vertices[(i + 1) % num_verts, 1]
            u2 = uvs[(i + 1) % num_verts, 0]
            v2 = uvs[(i + 1) % num_verts, 1]

            if <int> p1y == <int> p2y:
                continue

            if p1y > p2y:
                p1x, p2x = p2x, p1x
                p1y, p2y = p2y, p1y
                u1, u2 = u2, u1
                v1, v2 = v2, v1

            y_start = <int> p1y
            y_end = <int> p2y

            if y_start >= h or y_end < 0:
                continue

            dy_inv = 1.0 / (p2y - p1y)

            new_edge = <Edge *> malloc(sizeof(Edge))
            new_edge.y_max = y_end
            new_edge.x = p1x
            new_edge.dx = (p2x - p1x) * dy_inv
            new_edge.u = u1
            new_edge.du = (u2 - u1) * dy_inv
            new_edge.v = v1
            new_edge.dv = (v2 - v1) * dy_inv

            new_edge.next = GET[y_start]
            GET[y_start] = new_edge
            edges_count += 1

        # Execution logic (Variable declarations must be above this)
        AET = <ActiveEdge *> malloc(edges_count * sizeof(ActiveEdge))

        for y in range(y_min_global, y_max_global + 1):
            current_node = GET[y]
            while current_node != NULL:
                if aet_count < edges_count:
                    AET[aet_count].y_max = current_node.y_max
                    AET[aet_count].x = current_node.x
                    AET[aet_count].dx = current_node.dx
                    AET[aet_count].u = current_node.u
                    AET[aet_count].du = current_node.du
                    AET[aet_count].v = current_node.v
                    AET[aet_count].dv = current_node.dv
                    aet_count += 1

                temp_node = current_node
                current_node = current_node.next
                free(temp_node)
            GET[y] = NULL

            k = 0
            for j in range(aet_count):
                if AET[j].y_max > y:
                    AET[k] = AET[j]
                    k += 1
            aet_count = k

            qsort(AET, aet_count, sizeof(ActiveEdge), compare_edges)

            for j in range(0, aet_count - 1, 2):
                x_start = <int> AET[j].x
                x_end = <int> AET[j + 1].x

                u_start = AET[j].u
                v_start = AET[j].v
                u_end = AET[j + 1].u
                v_end = AET[j + 1].v

                if x_end > x_start:
                    span_width = <double> (x_end - x_start)
                    du_dx = (u_end - u_start) / span_width
                    dv_dx = (v_end - v_start) / span_width

                    cur_u = u_start
                    cur_v = v_start

                    if x_start < 0:
                        cur_u += du_dx * (0 - x_start)
                        cur_v += dv_dx * (0 - x_start)
                        x_start = 0

                    if x_end > w: x_end = w

                    for x in range(x_start, x_end):
                        tex_col = sample_nearest(texture, tex_w, tex_h, <float> cur_u, <float> cur_v)

                        if modulate != <uint32>0xFFFFFFFF:
                            tex_col = blend_colors(tex_col, modulate)

                        buffer[x, y] = blend_colors(tex_col, buffer[x, y])

                        cur_u += du_dx
                        cur_v += dv_dx

            for j in range(aet_count):
                AET[j].x += AET[j].dx
                AET[j].u += AET[j].du
                AET[j].v += AET[j].dv

        free(AET)
        free(GET)
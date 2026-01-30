from typing import Tuple, List
from engine.graphics.buffers.pixel_buffer import PixelBuffer
from engine.graphics.rasterizer.pipeline.clipper import Clipper
from engine.math.datatypes.vector2 import Vector2
from engine.core.textures.texture_2d import Texture2D

from engine.graphics.rasterizer.primitives import point
from engine.graphics.rasterizer.primitives import line, rect, circle, polygon
from logger import Logger


class SoftwareRasterizer:
    """
    The main interface for 2D software rendering.
    Orchestrates high-level Python datatypes into low-level Cython modules.
    """

    def __init__(self, buffer: PixelBuffer):
        self.buffer = buffer
        self._clip_rect_min = 0.0
        self._clip_rect_min_y = 0.0
        self._clip_rect_max = float(buffer.width)
        self._clip_rect_max_y = float(buffer.height)
        self._clipper = Clipper()

    def set_clip_rect(self, x: float, y: float, w: float, h: float) -> None:
        """Sets the clipping rectangle for the rasterizer."""
        self._clip_rect_min = max(0.0, x)
        self._clip_rect_min_y = max(0.0, y)
        self._clip_rect_max = min(float(self.buffer.width), x + w)
        self._clip_rect_max_y = min(float(self.buffer.height), y + h)

    def draw_textured_polygon(
            self,
            points: List[Vector2],
            uvs: List[Vector2],
            texture: Texture2D,
            color: Tuple[int, int, int, int],
    ):
        """Draws an arbitrary textured polygon using scanline rasterization."""
        if len(points) < 3 or len(uvs) != len(points):
            return

        clipped_verts, clipped_uvs = self._clipper.clip_polygon(
            points,
            uvs,
            self._clip_rect_min,
            self._clip_rect_min_y,
            self._clip_rect_max,
            self._clip_rect_max_y
        )

        if clipped_verts.shape[0] < 3:
            return

        pixels = self.buffer.lock()
        tex_pixels = texture.lock()

        try:
            c_int = self.buffer.map_color(*color)
            tex_w = texture.get_width()
            tex_h = texture.get_height()

            polygon.draw_polygon_textured(
                pixels, clipped_verts, clipped_uvs, tex_pixels, tex_w, tex_h, c_int
            )
        finally:
            self.buffer.unlock()
            texture.unlock()

    def clear_clip_rect(self) -> None:
        """Resets the clipping rectangle."""
        self._clip_rect_min = 0.0
        self._clip_rect_min_y = 0.0
        self._clip_rect_max = float(self.buffer.width)
        self._clip_rect_max_y = float(self.buffer.height)

    def clear(self, color: Tuple[int, int, int]):
        """Clears the buffer."""
        c_int = self.buffer.map_color(*color)
        self.buffer.clear(c_int)

    def draw_line(
            self,
            from_pos: Vector2,
            to_pos: Vector2,
            color: Tuple[int, int, int, int],
            width: float = 1.0,
    ):
        """Draws a line using Bresenham algorithm."""
        if width > 1.0:
            self.draw_polyline([from_pos, to_pos], color, width)
            return

        clipped_coords, accepted = self._clipper.clip_line(
            from_pos.x, from_pos.y, to_pos.x, to_pos.y,
            self._clip_rect_min, self._clip_rect_min_y,
            self._clip_rect_max, self._clip_rect_max_y
        )

        if not accepted:
            return

        pixels = self.buffer.lock()
        try:
            c_int = self.buffer.map_color(*color)
            line.draw_line(
                pixels,
                int(clipped_coords[0]),
                int(clipped_coords[1]),
                int(clipped_coords[2]),
                int(clipped_coords[3]),
                c_int,
            )
        finally:
            self.buffer.unlock()

    def draw_polyline(
            self,
            points: List[Vector2],
            color: Tuple[int, int, int, int],
            width: float = 1.0,
    ):
        """
        Draws a connected series of line segments with thickness.
        Expands geometry into quads and circles (for joints).
        """
        if len(points) < 2:
            return

        if width <= 1.0:
            for i in range(len(points) - 1):
                self.draw_line(points[i], points[i + 1], color, 1.0)
            return

        # Geometry Expansion for Thick Lines
        half_width = width / 2.0

        for i in range(len(points) - 1):
            p1 = points[i]
            p2 = points[i + 1]

            if p1 == p2:
                continue

            # Direction vector
            diff = p2 - p1
            length = diff.length()
            if length == 0:
                continue

            # Normal vector (Orthogonal)
            # (-y, x) is 90 deg rotation
            normal = Vector2(-diff.y, diff.x) / length * half_width

            # 4 Corners of the segment
            q1 = p1 + normal
            q2 = p1 - normal
            q3 = p2 - normal
            q4 = p2 + normal

            # Draw Segment Body
            self.draw_polygon([q1, q2, q3, q4], color, filled=True)

            # Draw Joint (Circle) at p2 to smooth the corner
            # Skip the last point as it has no connection
            if i < len(points) - 2:
                self.draw_circle(p2, half_width, color, filled=True)

        # Draw start and end caps (simple round caps)
        self.draw_circle(points[0], half_width, color, filled=True)
        self.draw_circle(points[-1], half_width, color, filled=True)

    def draw_rect(
            self,
            rect_pos: Vector2,
            rect_size: Vector2,
            color: Tuple[int, int, int, int],
            filled: bool = True,
            thickness: int = 1,
    ):
        """Draws a rectangle."""
        pixels = self.buffer.lock()
        try:
            c_int = self.buffer.map_color(*color)
            if filled:
                rect.fill_rect(
                    pixels,
                    int(rect_pos.x),
                    int(rect_pos.y),
                    int(rect_size.x),
                    int(rect_size.y),
                    c_int,
                )
            else:
                rect.draw_rect_outline(
                    pixels,
                    int(rect_pos.x),
                    int(rect_pos.y),
                    int(rect_size.x),
                    int(rect_size.y),
                    c_int,
                    thickness,
                )
        finally:
            self.buffer.unlock()

    def draw_circle(
            self,
            center: Vector2,
            radius: float,
            color: Tuple[int, int, int, int],
            filled: bool = True,
    ):
        """Draws a circle."""
        if (
                center.x + radius < self._clip_rect_min
                or center.x - radius > self._clip_rect_max
                or center.y + radius < self._clip_rect_min_y
                or center.y - radius > self._clip_rect_max_y
        ):
            return

        pixels = self.buffer.lock()
        try:
            c_int = self.buffer.map_color(*color)
            if filled:
                circle.draw_circle_filled(
                    pixels, int(center.x), int(center.y), int(radius), c_int
                )
            else:
                circle.draw_circle_outline(
                    pixels, int(center.x), int(center.y), int(radius), c_int
                )
        finally:
            self.buffer.unlock()

    def draw_polygon(
            self,
            points: List[Vector2],
            color: Tuple[int, int, int, int],
            filled: bool = True,
    ):
        """Draws an arbitrary polygon."""
        if len(points) < 3:
            return

        clipped_verts_view, _ = self._clipper.clip_polygon(
            points,
            None,
            self._clip_rect_min,
            self._clip_rect_min_y,
            self._clip_rect_max,
            self._clip_rect_max_y,
        )

        if clipped_verts_view.shape[0] < 3:
            return

        pixels = self.buffer.lock()
        try:
            c_int = self.buffer.map_color(*color)

            if filled:
                polygon.draw_polygon_filled(pixels, clipped_verts_view, c_int)
            else:
                polygon.draw_polygon_outline(pixels, clipped_verts_view, c_int)
        finally:
            self.buffer.unlock()

    def draw_triangle(
            self, v1: Vector2, v2: Vector2, v3: Vector2, color: Tuple[int, int, int, int]
    ):
        min_x = min(v1.x, v2.x, v3.x)
        max_x = max(v1.x, v2.x, v3.x)
        min_y = min(v1.y, v2.y, v3.y)
        max_y = max(v1.y, v2.y, v3.y)

        if (
                max_x < self._clip_rect_min
                or min_x > self._clip_rect_max
                or max_y < self._clip_rect_min_y
                or min_y > self._clip_rect_max_y
        ):
            return

        self.draw_polygon([v1, v2, v3], color, filled=True)

    def draw_textured_triangle(
            self,
            vertices: List[Vector2],
            uvs: List[Vector2],
            texture: Texture2D,
            use_bilinear: bool = False,
    ):
        """Draws a textured triangle."""
        if len(vertices) != 3 or len(uvs) != 3:
            return

        min_x = min(v.x for v in vertices)
        max_x = max(v.x for v in vertices)
        min_y = min(v.y for v in vertices)
        max_y = max(v.y for v in vertices)

        if (
                max_x < self._clip_rect_min
                or min_x > self._clip_rect_max
                or max_y < self._clip_rect_min_y
                or min_y > self._clip_rect_max_y
        ):
            return

        self.draw_textured_polygon(vertices, uvs, texture, (255, 255, 255, 255))

    def draw_point(self, pos: Vector2, color: Tuple[int, int, int, int]):
        """Draws a single pixel."""
        if (
                pos.x < self._clip_rect_min
                or pos.x >= self._clip_rect_max
                or pos.y < self._clip_rect_min_y
                or pos.y >= self._clip_rect_max_y
        ):
            return

        pixels = self.buffer.lock()
        try:
            c_int = self.buffer.map_color(*color)
            point.draw_point(pixels, int(pos.x), int(pos.y), c_int)
        finally:
            self.buffer.unlock()

    def draw_points(self, points: List[Vector2], color: Tuple[int, int, int, int]):
        """Draws a list of points efficiently."""
        if not points:
            return

        pixels = self.buffer.lock()
        try:
            c_int = self.buffer.map_color(*color)
            point.draw_points(pixels, points, c_int)
        finally:
            self.buffer.unlock()
from typing import Optional, List, Tuple
import pygame
import numpy as np
from engine.math.datatypes.vector2 import Vector2
from engine.math.datatypes.color import Color
from engine.math.datatypes.rect2 import Rect2
from engine.servers.rasterizer.enums import BlendMode, PrimitiveType
from engine.graphics.rasterizer.software_rasterizer import SoftwareRasterizer
from engine.graphics.buffers.pixel_buffer import PixelBuffer
from engine.core.textures.texture_2d import Texture2D


class SurfaceTextureAdapter(Texture2D):
    """
    Adapts a raw Pygame Surface (used internally by RendererStorage)
    to the Texture2D interface required by SoftwareRasterizer.
    Enables strict separation of concerns and type safety.
    """

    def __init__(self, surface: pygame.Surface):
        super().__init__()
        self._surface = surface

    def get_width(self) -> int:
        return self._surface.get_width()

    def get_height(self) -> int:
        return self._surface.get_height()

    def has_alpha(self) -> bool:
        return (self._surface.get_flags() & pygame.SRCALPHA) != 0

    def get_data(self) -> pygame.Surface:
        return self._surface

    def lock(self) -> np.ndarray:
        """
        Delegates locking to Pygame's surfarray.
        Returns the pixel array required by Cython modules.
        """
        self._surface.lock()
        return pygame.surfarray.pixels2d(self._surface)

    def unlock(self):
        """
        Unlocks the underlying surface.
        """
        if self._surface.get_locked():
            self._surface.unlock()


class RasterizerCanvas:
    """
    RasterizerCanvas (Software Implementation)

    Acts as the bridge between the RenderingServer (Commands) and the SoftwareRasterizer.
    Responsible for:
    1. Managing the rendering target (wrapping Surfaces in PixelBuffers).
    2. Adapting resources (Textures) for the Rasterizer.
    3. Translating high-level draw commands to low-level Rasterizer calls.
    """

    _instance: Optional["RasterizerCanvas"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RasterizerCanvas, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.target_surface: Optional[pygame.Surface] = None
        self.pixel_buffer: Optional[PixelBuffer] = None
        self.sw_rasterizer: Optional[SoftwareRasterizer] = None

        self.current_blend_mode: BlendMode = BlendMode.BLEND_MODE_MIX
        self._initialized = True

    @staticmethod
    def get_singleton() -> "RasterizerCanvas":
        if RasterizerCanvas._instance is None:
            RasterizerCanvas()
        return RasterizerCanvas._instance

    def set_target_surface(self, surface: Optional[pygame.Surface]) -> None:
        """
        Set the surface to render to.
        Passing None unbinds the current target.
        """
        if surface is None:
            self.target_surface = None
            self.pixel_buffer = None
            self.sw_rasterizer = None
            return

        if self.target_surface != surface:
            self.target_surface = surface
            self.pixel_buffer = PixelBuffer(
                width=surface.get_width(), height=surface.get_height(), surface=surface
            )
            self.sw_rasterizer = SoftwareRasterizer(self.pixel_buffer)

    def set_blend_mode(self, mode: BlendMode) -> None:
        """
        Set blend mode for subsequent draws.
        Note: Current SoftwareRasterizer implementation primarily supports MIX.
        """
        self.current_blend_mode = mode

    def set_clip_rect(self, rect: Rect2) -> None:
        """Enable clipping to a rectangle via the SoftwareRasterizer"""
        if self.sw_rasterizer:
            self.sw_rasterizer.set_clip_rect(
                rect.position.x, rect.position.y, rect.size.x, rect.size.y
            )

    def clear_clip_rect(self) -> None:
        """Disable clipping"""
        if self.sw_rasterizer:
            self.sw_rasterizer.clear_clip_rect()

    def draw_primitive(
        self,
        points: List[Vector2],
        colors: List[Color],
        uvs: List[Vector2],
        texture: Optional[pygame.Surface],
        primitive_type: int,
    ) -> None:
        """
        Draw primitives (lines, points, etc.) using SoftwareRasterizer.
        """
        if not self.sw_rasterizer or not points:
            return

        if primitive_type == PrimitiveType.PRIMITIVE_LINES:
            self._draw_lines(points, colors)
        elif primitive_type == PrimitiveType.PRIMITIVE_LINE_STRIP:
            self._draw_line_strip(points, colors)
        elif primitive_type == PrimitiveType.PRIMITIVE_POINTS:
            self._draw_points(points, colors)
        elif primitive_type == PrimitiveType.PRIMITIVE_TRIANGLES:
            self._draw_triangle_list(points, colors, uvs, texture)

    def draw_batch(
        self,
        vertices: List[Vector2],
        colors: List[Color],
        uvs: List[Vector2],
        indices: List[int],
        texture: Optional[pygame.Surface],
    ) -> None:
        """
        Draw indexed triangle batch using SoftwareRasterizer.
        """
        if not self.sw_rasterizer or not vertices:
            return

        tex_adapter = SurfaceTextureAdapter(texture) if texture else None
        for i in range(0, len(indices), 3):
            if i + 2 >= len(indices):
                break

            idx0, idx1, idx2 = indices[i], indices[i + 1], indices[i + 2]

            if idx0 >= len(vertices) or idx1 >= len(vertices) or idx2 >= len(vertices):
                continue

            v0, v1, v2 = vertices[idx0], vertices[idx1], vertices[idx2]
            c0 = colors[idx0] if colors else Color(1, 1, 1, 1)
            c1 = colors[idx1] if colors else c0
            c2 = colors[idx2] if colors else c0
            avg_color = self._average_colors([c0, c1, c2])
            col_tuple = self._color_to_tuple_int(avg_color)

            if tex_adapter:
                tri_uvs = [
                    uvs[idx0] if uvs else Vector2(0, 0),
                    uvs[idx1] if uvs else Vector2(0, 0),
                    uvs[idx2] if uvs else Vector2(0, 0),
                ]
                self.sw_rasterizer.draw_textured_triangle(
                    [v0, v1, v2], tri_uvs, tex_adapter, use_bilinear=False
                )
            else:
                self.sw_rasterizer.draw_triangle(v0, v1, v2, col_tuple)

    def _draw_lines(self, points: List[Vector2], colors: List[Color]) -> None:
        """Draw individual line segments"""
        for i in range(0, len(points), 2):
            if i + 1 >= len(points):
                break

            p1 = points[i]
            p2 = points[i + 1]
            color_idx = min(i // 2, len(colors) - 1) if colors else 0
            col = colors[color_idx] if colors else Color(1, 1, 1, 1)
            self.sw_rasterizer.draw_line(p1, p2, self._color_to_tuple_int(col))

    def _draw_line_strip(self, points: List[Vector2], colors: List[Color]) -> None:
        """Draw connected line strip"""
        if len(points) < 2:
            return

        for i in range(len(points) - 1):
            p1 = points[i]
            p2 = points[i + 1]
            color_idx = min(i, len(colors) - 1) if colors else 0
            col = colors[color_idx] if colors else Color(1, 1, 1, 1)
            self.sw_rasterizer.draw_line(p1, p2, self._color_to_tuple_int(col))

    def _draw_points(self, points: List[Vector2], colors: List[Color]) -> None:
        """Draw individual points"""
        for i, point in enumerate(points):
            color_idx = min(i, len(colors) - 1) if colors else 0
            col = colors[color_idx] if colors else Color(1, 1, 1, 1)
            self.sw_rasterizer.draw_point(point, self._color_to_tuple_int(col))

    def _draw_triangle_list(
        self,
        points: List[Vector2],
        colors: List[Color],
        uvs: List[Vector2],
        texture: Optional[pygame.Surface],
    ) -> None:
        """Draw unindexed list of triangles"""
        tex_adapter = SurfaceTextureAdapter(texture) if texture else None

        for i in range(0, len(points), 3):
            if i + 2 >= len(points):
                break

            tri_verts = points[i : i + 3]

            c0 = colors[i] if colors else Color(1, 1, 1, 1)
            c1 = colors[i + 1] if colors else c0
            c2 = colors[i + 2] if colors else c0
            avg_color = self._average_colors([c0, c1, c2])
            col_tuple = self._color_to_tuple_int(avg_color)

            if tex_adapter:
                tri_uvs = uvs[i : i + 3] if uvs else [Vector2(0, 0)] * 3
                self.sw_rasterizer.draw_textured_triangle(
                    tri_verts, tri_uvs, tex_adapter
                )
            else:
                self.sw_rasterizer.draw_triangle(
                    tri_verts[0], tri_verts[1], tri_verts[2], col_tuple
                )

    def _color_to_tuple_int(self, color: Color) -> Tuple[int, int, int, int]:
        """Convert Color to RGBA tuple 0-255"""
        return (
            int(color.r * 255),
            int(color.g * 255),
            int(color.b * 255),
            int(color.a * 255),
        )

    def _average_colors(self, colors: List[Color]) -> Color:
        """Average multiple colors"""
        if not colors:
            return Color(1, 1, 1, 1)

        r = sum(c.r for c in colors) / len(colors)
        g = sum(c.g for c in colors) / len(colors)
        b = sum(c.b for c in colors) / len(colors)
        a = sum(c.a for c in colors) / len(colors)

        return Color(r, g, b, a)

    def draw_rect(self, rect: Rect2, color: Color, filled: bool = True) -> None:
        """Draw a rectangle (Direct rasterizer call)"""
        if not self.sw_rasterizer:
            return
        self.sw_rasterizer.draw_rect(
            rect.position, rect.size, self._color_to_tuple_int(color), filled
        )

    def draw_circle(
        self, center: Vector2, radius: float, color: Color, filled: bool = True
    ) -> None:
        """Draw a circle (Direct rasterizer call)"""
        if not self.sw_rasterizer:
            return
        self.sw_rasterizer.draw_circle(
            center, radius, self._color_to_tuple_int(color), filled
        )

    def draw_polyline(
            self, points: List[Vector2], color: Color, width: float = 1.0, antialiased: bool = False
    ) -> None:
        """
        Draws a polyline with thickness.
        """
        if not self.sw_rasterizer or len(points) < 2:
            return

        col_tuple = self._color_to_tuple_int(color)
        self.sw_rasterizer.draw_polyline(points, col_tuple, width)

    def draw_line(
        self, from_pos: Vector2, to_pos: Vector2, color: Color, width: int = 1
    ) -> None:
        """Draw a line (Direct rasterizer call)"""
        if not self.sw_rasterizer:
            return
        self.sw_rasterizer.draw_line(
            from_pos, to_pos, self._color_to_tuple_int(color), float(width)
        )

    def blit_texture(
        self, texture: pygame.Surface, position: Vector2, source_rect: Rect2 = None
    ) -> None:
        """
        Replaces pygame.blit with software textured quad drawing.
        """
        if not self.sw_rasterizer or not texture:
            return

        w, h = texture.get_width(), texture.get_height()

        v0 = position
        v1 = Vector2(position.x + w, position.y)
        v2 = Vector2(position.x + w, position.y + h)
        v3 = Vector2(position.x, position.y + h)

        if source_rect:
            u_min = source_rect.position.x / w
            v_min = source_rect.position.y / h
            u_max = (source_rect.position.x + source_rect.size.x) / w
            v_max = (source_rect.position.y + source_rect.size.y) / h

            uv0 = Vector2(u_min, v_min)
            uv1 = Vector2(u_max, v_min)
            uv2 = Vector2(u_max, v_max)
            uv3 = Vector2(u_min, v_max)

            v1.x = position.x + source_rect.size.x
            v2.x = position.x + source_rect.size.x
            v2.y = position.y + source_rect.size.y
            v3.y = position.y + source_rect.size.y
        else:
            uv0 = Vector2(0, 0)
            uv1 = Vector2(1, 0)
            uv2 = Vector2(1, 1)
            uv3 = Vector2(0, 1)

        tex_adapter = SurfaceTextureAdapter(texture)

        self.sw_rasterizer.draw_textured_triangle(
            [v0, v1, v2], [uv0, uv1, uv2], tex_adapter
        )
        self.sw_rasterizer.draw_textured_triangle(
            [v0, v2, v3], [uv0, uv2, uv3], tex_adapter
        )
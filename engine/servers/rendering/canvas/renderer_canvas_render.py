import math
from typing import Optional, List
import pygame
from engine.core.rid import RID
from engine.math.datatypes.vector2 import Vector2
from engine.math.datatypes.transform2d import Transform2D
from engine.math.datatypes.color import Color
from .render_enums import CanvasBlendMode
from .render_state import RenderState, BatchData
from .commands import (
    CommandRect,
    CommandNinePatch,
    CommandPrimitive,
    CommandPolygon,
    CommandClipIgnore, CommandPolyline, CommandCircle,
)
from engine.logger import Logger

class RendererCanvasRender:
    _instance: Optional["RendererCanvasRender"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RendererCanvasRender, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        from engine.servers.rendering.renderer_storage import RendererStorage
        self.storage = RendererStorage.get_singleton()

        from engine.servers.rasterizer.rasterizer_canvas import RasterizerCanvas
        self.rasterizer = RasterizerCanvas.get_singleton()

        self.state = RenderState()
        self.current_batch: Optional[BatchData] = None
        self.batches: List[BatchData] = []
        self.max_vertices_per_batch = 8192
        self.draw_calls_this_frame = 0
        self.vertices_drawn_this_frame = 0
        self._initialized = True

    @staticmethod
    def get_singleton() -> "RendererCanvasRender":
        if RendererCanvasRender._instance is None:
            RendererCanvasRender()
        return RendererCanvasRender._instance

    def render_canvas_item(
        self, transform: Transform2D, commands: List, modulate: Color
    ) -> None:
        prev_transform = self.state.transform
        prev_modulate = self.state.modulate

        self.state.transform = transform
        self.state.modulate = modulate

        for cmd in commands:
            self._execute_command(cmd)

        self.state.transform = prev_transform
        self.state.modulate = prev_modulate

    def _execute_command(self, cmd) -> None:
        if isinstance(cmd, CommandRect):
            self._draw_rect(cmd)
        elif isinstance(cmd, CommandNinePatch):
            self._draw_nine_patch(cmd)
        elif isinstance(cmd, CommandPrimitive):
            self._draw_primitive(cmd)
        elif isinstance(cmd, CommandPolygon):
            self._draw_polygon(cmd)
        elif isinstance(cmd, CommandPolyline):
            self._draw_polyline(cmd)
        elif isinstance(cmd, CommandCircle):
            self._draw_circle(cmd)
        elif isinstance(cmd, CommandClipIgnore):
            self.state.clip_enabled = not cmd.ignore

    def _draw_circle(self, cmd) -> None:
        """
        Draws a circle or ellipse using polygon tessellation.
        This ensures the shape is correctly transformed (rotated/skewed) by the global transform.
        """
        segment_count = 64

        vertices = []
        pos = cmd.position
        rx = cmd.radius.x
        ry = cmd.radius.y

        for i in range(segment_count):
            angle = (i / segment_count) * math.tau
            v_local = Vector2(
                pos.x + math.cos(angle) * rx,
                pos.y + math.sin(angle) * ry
            )
            v_global = self.state.transform.xform(v_local)
            vertices.append(v_global)

        final_color = Color(
            cmd.color.r * self.state.modulate.r,
            cmd.color.g * self.state.modulate.g,
            cmd.color.b * self.state.modulate.b,
            cmd.color.a * self.state.modulate.a,
        )
        self._flush_batches()
        self.rasterizer.sw_rasterizer.draw_polygon(
            vertices,
            self.rasterizer._color_to_tuple_int(final_color),
            filled=True
        )
        self.draw_calls_this_frame += 1

    def _draw_polyline(self, cmd) -> None:
        transformed_points = [self.state.transform.xform(p) for p in cmd.points]
        base_color = cmd.colors[0] if cmd.colors else Color(1, 1, 1, 1)
        final_color = Color(
            base_color.r * self.state.modulate.r,
            base_color.g * self.state.modulate.g,
            base_color.b * self.state.modulate.b,
            base_color.a * self.state.modulate.a,
        )
        self._flush_batches()
        self.rasterizer.draw_polyline(
            transformed_points,
            final_color,
            cmd.width,
            cmd.antialiased
        )
        self.draw_calls_this_frame += 1

    def _draw_rect(self, cmd) -> None:
        rect = cmd.rect
        pos = rect.position
        size = rect.size

        vertices = [
            self.state.transform.xform(pos),
            self.state.transform.xform(Vector2(pos.x + size.x, pos.y)),
            self.state.transform.xform(Vector2(pos.x + size.x, pos.y + size.y)),
            self.state.transform.xform(Vector2(pos.x, pos.y + size.y)),
        ]

        final_color = Color(
            cmd.modulate.r * self.state.modulate.r,
            cmd.modulate.g * self.state.modulate.g,
            cmd.modulate.b * self.state.modulate.b,
            cmd.modulate.a * self.state.modulate.a,
        )

        colors = [final_color] * 4
        uvs = [Vector2(0, 0)] * 4
        indices = [0, 1, 2, 0, 2, 3]

        self._add_to_batch(
            vertices, colors, uvs, indices, None, CanvasBlendMode.BLEND_MODE_MIX
        )

    def _draw_primitive(self, cmd) -> None:
        transformed_points = [self.state.transform.xform(p) for p in cmd.points]

        modulated_colors = [
            Color(
                c.r * self.state.modulate.r,
                c.g * self.state.modulate.g,
                c.b * self.state.modulate.b,
                c.a * self.state.modulate.a,
            )
            for c in cmd.colors
        ]

        is_texture_missing = False
        if cmd.texture:
            if self.storage.texture_get_native_handle(cmd.texture) is None:
                is_texture_missing = True
                modulated_colors = [Color(1, 0, 1, 1)] * len(modulated_colors)

        if cmd.primitive_type == 1:
            self._flush_batches()
            self.rasterizer.draw_primitive(
                transformed_points,
                modulated_colors,
                cmd.uvs,
                cmd.texture,
                cmd.primitive_type,
            )
            self.draw_calls_this_frame += 1

        elif cmd.primitive_type == 3:
            indices = list(range(len(transformed_points)))
            self._add_to_batch(
                transformed_points,
                modulated_colors,
                cmd.uvs,
                indices,
                None if is_texture_missing else cmd.texture,
                CanvasBlendMode.BLEND_MODE_MIX,
            )

        elif cmd.primitive_type == 4:
            indices = []
            for i in range(1, len(transformed_points) - 1):
                indices.extend([0, i, i + 1])
            self._add_to_batch(
                transformed_points,
                modulated_colors,
                cmd.uvs,
                indices,
                None if is_texture_missing else cmd.texture,
                CanvasBlendMode.BLEND_MODE_MIX,
            )
        else:
            self._flush_batches()
            self.rasterizer.draw_primitive(
                transformed_points,
                modulated_colors,
                cmd.uvs,
                cmd.texture,
                cmd.primitive_type,
            )
            self.draw_calls_this_frame += 1

    def _draw_polygon(self, cmd) -> None:
        transformed_points = [self.state.transform.xform(p) for p in cmd.points]

        base_color = cmd.colors[0] if cmd.colors else Color(1, 1, 1, 1)
        final_color = Color(
            base_color.r * self.state.modulate.r,
            base_color.g * self.state.modulate.g,
            base_color.b * self.state.modulate.b,
            base_color.a * self.state.modulate.a,
        )

        is_missing = False
        if cmd.texture:
            tex_surface = self.storage.texture_get_native_handle(cmd.texture)
            if not tex_surface:
                is_missing = True
                final_color = Color(1, 0, 1, 1)

        if cmd.texture and not is_missing:
            self._flush_batches()
            tex_surface = self.storage.texture_get_native_handle(cmd.texture)
            from engine.servers.rasterizer.rasterizer_canvas import (
                SurfaceTextureAdapter,
            )
            tex_adapter = SurfaceTextureAdapter(tex_surface)
            self.rasterizer.sw_rasterizer.draw_textured_polygon(
                transformed_points,
                cmd.uvs,
                tex_adapter,
                self.rasterizer._color_to_tuple_int(final_color),
            )
        else:
            self._flush_batches()
            self.rasterizer.sw_rasterizer.draw_polygon(
                transformed_points,
                self.rasterizer._color_to_tuple_int(final_color),
                filled=True,
            )

    def _draw_nine_patch(self, cmd) -> None:
        pass

    def _add_to_batch(
        self,
        vertices: List[Vector2],
        colors: List[Color],
        uvs: List[Vector2],
        indices: List[int],
        texture: Optional[RID],
        blend_mode: CanvasBlendMode,
    ) -> None:
        if self.current_batch is None:
            self.current_batch = BatchData()
            self.current_batch.texture = texture
            self.current_batch.blend_mode = blend_mode
            self.current_batch.clip_rect = (
                self.state.clip_rect if self.state.clip_enabled else None
            )

        if not self.current_batch.can_batch_with(
            texture,
            blend_mode,
            self.state.clip_rect if self.state.clip_enabled else None,
        ):
            self._flush_current_batch()
            self.current_batch = BatchData()
            self.current_batch.texture = texture
            self.current_batch.blend_mode = blend_mode
            self.current_batch.clip_rect = (
                self.state.clip_rect if self.state.clip_enabled else None
            )

        if (
            len(self.current_batch.vertices) + len(vertices)
            > self.max_vertices_per_batch
        ):
            self._flush_current_batch()
            self.current_batch = BatchData()
            self.current_batch.texture = texture
            self.current_batch.blend_mode = blend_mode
            self.current_batch.clip_rect = (
                self.state.clip_rect if self.state.clip_enabled else None
            )

        base_index = len(self.current_batch.vertices)
        self.current_batch.vertices.extend(vertices)
        self.current_batch.colors.extend(colors)
        self.current_batch.uvs.extend(uvs)
        self.current_batch.indices.extend([i + base_index for i in indices])

    def _flush_current_batch(self) -> None:
        if self.current_batch and not self.current_batch.is_empty():
            self._draw_batch(self.current_batch)
            self.current_batch = None

    def _flush_batches(self) -> None:
        self._flush_current_batch()

    def _draw_batch(self, batch: BatchData) -> None:
        self.rasterizer.set_blend_mode(batch.blend_mode)

        if batch.clip_rect:
            self.rasterizer.set_clip_rect(batch.clip_rect)
        else:
            self.rasterizer.clear_clip_rect()

        texture_surface = None
        if batch.texture:
            texture_surface = self.storage.texture_get_native_handle(batch.texture)

        self.rasterizer.draw_batch(
            batch.vertices, batch.colors, batch.uvs, batch.indices, texture_surface
        )

        self.draw_calls_this_frame += 1
        self.vertices_drawn_this_frame += len(batch.vertices)

    def begin_frame(self) -> None:
        self.draw_calls_this_frame = 0
        self.vertices_drawn_this_frame = 0
        self.state = RenderState()
        self.current_batch = None

    def end_frame(self) -> None:
        self._flush_batches()

    def set_target_surface(self, surface: pygame.Surface) -> None:
        self.rasterizer.set_target_surface(surface)

    def clear_target(self, color: Color) -> None:
        if self.rasterizer.sw_rasterizer:
            self.rasterizer.sw_rasterizer.clear(
                (int(color.r * 255), int(color.g * 255), int(color.b * 255))
            )
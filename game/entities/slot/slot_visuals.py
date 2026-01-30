from typing import List, Optional
from engine.core.resource_loader import ResourceLoader
from engine.core.textures import Texture
from engine.math.datatypes.vector2 import Vector2
from engine.math.datatypes.color import Color
from engine.ui.control import Control


class SlotVisuals(Control):
    def __init__(
            self,
            width: int,
            height: int,
            background_texture_key: str,
            highlight_texture_key: str,
            name: str = "Visuals",
    ) -> None:
        super().__init__(name)
        self.slot_width: int = width
        self.slot_height: int = height

        self._points: List[Vector2] = []
        self._bg_texture: Optional[Texture] = ResourceLoader.load(background_texture_key, Texture)
        self._hl_texture: Optional[Texture] = ResourceLoader.load(highlight_texture_key, Texture)

        self._highlight_active: bool = False
        self._white_color = Color(1, 1, 1, 1)
        self._highlight_color = Color(1, 1, 1, 150 / 255.0)

        self._standard_uvs: List[Vector2] = [
            Vector2(0, 0),
            Vector2(1, 0),
            Vector2(1, 1),
            Vector2(0, 1)
        ]

    def _draw(self) -> None:
        """
        Custom drawing override to ensure rendering happens in Control's coordinate space.
        Replaces child Polygon2D nodes to fix transform inheritance issues.
        """
        if not self._points:
            return

        if self._bg_texture:
            colors = [self._white_color] * len(self._points)
            self.draw_polygon(self._points, colors, self._standard_uvs, self._bg_texture)

        if self._highlight_active and self._hl_texture:
            colors = [self._highlight_color] * len(self._points)
            self.draw_polygon(self._points, colors, self._standard_uvs, self._hl_texture)

    def update_shape(self, points: List[Vector2]) -> None:
        """
        Updates the vertices for the slot geometry.
        """
        if not points:
            return

        self._points = points
        self.queue_redraw()

    def set_background_texture(self, texture_key: str) -> None:
        self._bg_texture = ResourceLoader.load(texture_key, Texture)
        self.queue_redraw()

    def set_highlight(self, active: bool) -> None:
        if self._highlight_active != active:
            self._highlight_active = active
            self.queue_redraw()

    def set_highlight_texture(self, texture_key: str) -> None:
        self._hl_texture = ResourceLoader.load(texture_key, Texture)
        self.queue_redraw()
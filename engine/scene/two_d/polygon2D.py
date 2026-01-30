from typing import List, Optional
from engine.scene.two_d.node2D import Node2D
from engine.scene.two_d.canvas_item import CanvasItem
from engine.scene.main.node import Node
from engine.core.textures.texture import Texture
from engine.math.datatypes.vector2 import Vector2
from engine.math.datatypes.color import Color
from engine.servers.rendering.rendering_server import RenderingServer


class Polygon2D(Node2D):
    """
    A 2D Node that displays a textured or colored polygon.
    """

    def __init__(self, name: str = "Polygon2D"):
        super().__init__(name)
        self._texture: Optional[Texture] = None
        self._polygon: List[Vector2] = []
        self._uv: List[Vector2] = []
        self._color: Color = Color(1, 1, 1, 1)
        self._offset: Vector2 = Vector2(0, 0)

    def _notification(self, what: int):
        if hasattr(super(), "_notification"):
            super()._notification(what)

        if what == Node.NOTIFICATION_ENTER_TREE:
            parent = self.get_parent()
            if parent and isinstance(parent, CanvasItem):
                RenderingServer.get_singleton().canvas_item_set_parent(
                    self.get_rid(), parent.get_rid()
                )

    @property
    def texture(self) -> Optional[Texture]:
        return self._texture

    @texture.setter
    def texture(self, value: Optional[Texture]):
        self._texture = value
        self.queue_redraw()

    @property
    def polygon(self) -> List[Vector2]:
        return self._polygon

    @polygon.setter
    def polygon(self, value: List[Vector2]):
        self._polygon = value
        self.queue_redraw()

    @property
    def uv(self) -> List[Vector2]:
        return self._uv

    @uv.setter
    def uv(self, value: List[Vector2]):
        self._uv = value
        self.queue_redraw()

    @property
    def color(self) -> Color:
        return self._color

    @color.setter
    def color(self, value: Color):
        self._color = value
        self.queue_redraw()

    @property
    def offset(self) -> Vector2:
        return self._offset

    @offset.setter
    def offset(self, value: Vector2):
        self._offset = value
        self.queue_redraw()

    def _draw(self):
        if len(self._polygon) < 3:
            return

        final_points = [p + self._offset for p in self._polygon]
        colors = [self._color] * len(final_points)
        final_uvs = self._uv
        if not final_uvs or len(final_uvs) != len(final_points):
            if self._texture:
                w = self._texture.get_width()
                h = self._texture.get_height()
                if w > 0 and h > 0:
                    final_uvs = [Vector2(p.x / w, p.y / h) for p in self._polygon]
                else:
                    final_uvs = [Vector2(0, 0)] * len(final_points)
            else:
                final_uvs = [Vector2(0, 0)] * len(final_points)

        self.draw_polygon(final_points, colors, final_uvs, self._texture)

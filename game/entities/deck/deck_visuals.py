import math
from typing import List
from engine.ui.control import Control
from engine.ui.widgets.label import Label
from engine.ui.enums import LayoutPreset, MouseFilter
from engine.math.datatypes.vector2 import Vector2
from engine.math.datatypes.color import Color
from engine.core.resource_loader import ResourceLoader
from engine.core.textures import Texture
from game.entities.card.card import Card


class DeckVisuals(Control):
    """
    Component: Renders the deck as a stack of individual card back slices.
    Refactored: Uses _draw() loop instead of Polygon2D pool for correct transform inheritance.
    """

    MAX_VISUAL_STACK = 40
    VISUAL_STEP = 1
    THICKNESS_PER_CARD = 1

    def __init__(self, name: str = "Visuals"):
        super().__init__(name)
        self.mouse_filter = MouseFilter.IGNORE
        self._current_count = 0

        self._base_points: List[Vector2] = []
        self._slice_polygons: List[List[Vector2]] = []

        self._back_texture = ResourceLoader.load(Card.KEY_CARD_BACK, Texture)
        self._standard_uvs: List[Vector2] = [
            Vector2(0, 0),
            Vector2(1, 0),
            Vector2(1, 1),
            Vector2(0, 1)
        ]
        self._white_color = Color(1, 1, 1, 1)

        self.counter_label = Label("0", "Counter")
        self.counter_label.z_index = 100
        self.add_child(self.counter_label)

    def _draw(self) -> None:
        """
        Iterates through cached slice polygons and draws them.
        """
        if not self._slice_polygons or not self._back_texture:
            return

        colors = [self._white_color] * 4
        for poly in self._slice_polygons:
            self.draw_polygon(poly, colors, self._standard_uvs, self._back_texture)

    def update_count(self, count: int) -> None:
        """
        Updates the label text and triggers a geometry refresh.
        """
        self._current_count = count
        self.counter_label.set_text(str(count))
        self.counter_label._update_layout()
        self._update_geometry()

    def set_quad_geometry(self, points: List[Vector2]) -> None:
        """
        Sets the base footprint of the deck on the table.
        """
        if not points or len(points) != 4:
            return

        self._base_points = points
        self._update_geometry()

    def _update_geometry(self) -> None:
        """
        Calculates the slice polygons based on the current count and base points.
        Caches the result in _slice_polygons and queues a redraw.
        """
        if not self._base_points:
            return

        self._slice_polygons.clear()

        displayable_count = min(self._current_count, self.MAX_VISUAL_STACK)
        active_slices = math.ceil(displayable_count / self.VISUAL_STEP)

        for i in range(active_slices):
            offset_y = -(i * self.THICKNESS_PER_CARD)
            offset_vec = Vector2(0, offset_y)
            new_points = [p + offset_vec for p in self._base_points]
            self._slice_polygons.append(new_points)

        sum_x = sum(p.x for p in self._base_points)
        sum_y = sum(p.y for p in self._base_points)
        centroid = Vector2(sum_x / 4.0, sum_y / 4.0)

        stack_height = active_slices * self.THICKNESS_PER_CARD
        centroid.y -= (stack_height / 2.0)

        label_size = self.counter_label.get_size()
        label_pos = Vector2(
            centroid.x - (label_size.x / 2.0),
            centroid.y - (label_size.y / 2.0)
        )

        self.counter_label.set_position(label_pos)
        self.queue_redraw()
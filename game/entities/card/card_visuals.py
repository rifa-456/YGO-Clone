from typing import Optional, List

from engine.ui.control import Control
from engine.ui.widgets.texture_rect import TextureRect
from engine.ui.enums import LayoutPreset, MouseFilter
from engine.math.datatypes.vector2 import Vector2
from engine.math.datatypes.color import Color
from .card_visual_mode import CardVisualMode


class CardVisuals(Control):
    """
    State-Driven Visual Component.
    """

    def __init__(self, mode: CardVisualMode):
        super().__init__("CardVisuals")
        self.set_anchors_preset(LayoutPreset.FULL_RECT)
        self.mouse_filter = MouseFilter.IGNORE
        self._current_mode = mode

        self._is_field_mode = False
        self._is_defense_orientation = False
        self._field_points: List[Vector2] = []
        self._white_color = Color(1, 1, 1, 1)
        self._standard_uvs: List[Vector2] = [
            Vector2(0, 0),
            Vector2(1, 0),
            Vector2(1, 1),
            Vector2(0, 1)
        ]

        self.back_rect: Optional[TextureRect] = None
        self.front_rect: Optional[TextureRect] = None

    def _draw(self) -> None:
        """
        Renders the Card Polygon when in Field Mode.
        Handles orientation changes via UV mapping instead of Node rotation to preserve geometry alignment.
        """
        if not self._is_field_mode or not self._field_points:
            return

        is_face_up = getattr(self, "_is_face_up", True)

        if self._current_mode == CardVisualMode.DECK:
            is_face_up = False
        elif self._current_mode == CardVisualMode.BACK:
            is_face_up = False

        texture = None
        if is_face_up and self.front_rect:
            texture = self.front_rect.texture
        elif not is_face_up and self.back_rect:
            texture = self.back_rect.texture

        if texture:
            colors = [self._white_color] * len(self._field_points)
            if self._is_defense_orientation:
                uvs = [
                    Vector2(0, 1),
                    Vector2(0, 0),
                    Vector2(1, 0),
                    Vector2(1, 1)
                ]
            else:
                uvs = self._standard_uvs

            self.draw_polygon(self._field_points, colors, uvs, texture)

    def set_quad_geometry(self, points: list[Vector2]):
        """
        Enables Field Mode and sets the perspective geometry.
        """
        if not points or len(points) != 4:
            return

        self._is_field_mode = True
        self._field_points = points
        self.rotation = 0.0
        self._hide_rects()
        self.queue_redraw()

    def reset_geometry(self):
        """Disables Field Mode and returns to standard UI rendering (TextureRects)."""
        self._is_field_mode = False
        self.queue_redraw()
        self._refresh_visibility()

    def set_face_up(self, is_face_up: bool):
        if self._current_mode in [CardVisualMode.DECK, CardVisualMode.BACK]:
            return

        self._is_face_up = is_face_up
        self.queue_redraw()
        self._refresh_visibility()

    def _refresh_visibility(self):
        """Decides what to show based on Mode (Field vs UI) and State (FaceUp vs Down)."""
        is_face_up = getattr(self, "_is_face_up", True)

        if self._current_mode == CardVisualMode.DECK:
            is_face_up = False

        if not self._is_field_mode:
            if self.back_rect:
                self.back_rect.visible = not is_face_up
            if self.front_rect:
                self.front_rect.visible = is_face_up
        else:
            self._hide_rects()

    def _hide_rects(self):
        if self.back_rect:
            self.back_rect.visible = False
        if self.front_rect:
            self.front_rect.visible = False

    def set_orientation(self, is_defense: bool):
        """
        Sets the visual orientation.
        In Field Mode, this updates the UV flag.
        In UI Mode (Hand), this rotates the actual Node.
        """
        self._is_defense_orientation = is_defense

        if self._is_field_mode:
            self.rotation = 0.0
        else:
            target_rot = 90.0 if is_defense else 0.0
            self.rotation = target_rot

        self.queue_redraw()

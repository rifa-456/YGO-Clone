from typing import Optional
import pygame
import numpy as np
from engine.ui.control import Control
from engine.ui.enums import FocusMode, SizeFlag, LayoutPreset, MouseFilter
from engine.math.datatypes.vector2 import Vector2
from engine.scene.main.input import Input
from engine.scene.main.signal import Signal
from .slot_logic import SlotLogic
from .slot_visuals import SlotVisuals
from .slot_enums import SlotType
from engine.math.algorithms.geometry import Geometry2D


class Slot(Control):
    """
    Root Entity for a grid cell.ons
    """

    SQUARE_WIDTH = 90
    SQUARE_HEIGHT = 90

    from game.entities.card.card import Card

    CARD_WIDTH = Card.CARD_WIDTH
    CARD_HEIGHT = Card.CARD_HEIGHT

    SLOT_WIDTH = SQUARE_WIDTH
    SLOT_HEIGHT = SQUARE_HEIGHT
    SLOT_ASPECT_RATIO = 1.0

    KEY_SLOT_NORMAL = "assets/board/board_monster.png"
    KEY_SLOT_FIELD = "assets/board/board_field.png"
    KEY_SLOT_GRAVE = "assets/board/board_graveyard.png"
    KEY_SLOT_EXTRA = "assets/board/board_extra.png"
    KEY_SLOT_HIGHLIGHT = "assets/board/board_highlight.png"

    def __init__(
            self,
            row: int,
            col: int,
            slot_type: SlotType,
            background_texture: str = None,
            highlight_texture: str = None,
            name: str = None,
            custom_size: Vector2 = None,
    ):
        super().__init__(name if name else f"Slot_{row}_{col}")

        self.row = row
        self.col = col
        self.slot_type = slot_type
        self.logic = SlotLogic()

        if custom_size:
            self.base_width = int(custom_size.x)
            self.base_height = int(custom_size.y)
        else:
            if self.slot_type in (SlotType.MONSTER, SlotType.SPELL_TRAP):
                self.base_width = self.SQUARE_WIDTH
                self.base_height = self.SQUARE_HEIGHT
            else:
                self.base_width = self.CARD_WIDTH
                self.base_height = self.CARD_HEIGHT

        self.custom_minimum_size = Vector2(self.base_width, self.base_height)
        self.size_flags_horizontal = SizeFlag.SHRINK_CENTER
        self.size_flags_vertical = SizeFlag.SHRINK_CENTER

        bg_tex = background_texture if background_texture else self.KEY_SLOT_NORMAL
        hl_tex = highlight_texture if highlight_texture else self.KEY_SLOT_HIGHLIGHT

        self.visuals = SlotVisuals(
            width=self.base_width,
            height=self.base_height,
            background_texture_key=bg_tex,
            highlight_texture_key=hl_tex,
        )
        self.visuals.mouse_filter = MouseFilter.IGNORE
        for child in self.visuals.children:
            if isinstance(child, Control):
                child.mouse_filter = MouseFilter.IGNORE
        self.visuals.set_highlight_texture(self.KEY_SLOT_HIGHLIGHT)

        self.add_child(self.visuals)
        self.focus_mode = FocusMode.ALL
        self.on_selected = Signal("on_selected")

        self._visual_poly_points: list[Vector2] = []
        self._poly_cache = np.zeros((0, 2), dtype=np.float64)

    def _gui_input(self, event):
        """
        Handles input events sent by the Viewport.
        Captures both 'ui_accept' (Keyboard Enter/Space) and Left Mouse Clicks.
        """
        super()._gui_input(event)
        if Input.is_event_action(event, "ui_accept"):
            self.on_selected.emit(self)
            self.accept_event()
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.on_selected.emit(self)
            self.accept_event()

    def _notification(self, what: int):
        super()._notification(what)
        if what == Control.NOTIFICATION_FOCUS_ENTER:
            self.visuals.set_highlight(True)
        elif what == Control.NOTIFICATION_FOCUS_EXIT:
            self.visuals.set_highlight(False)

    def set_background_texture(self, texture_key: str) -> None:
        self.visuals.set_background_texture(texture_key)

    def get_card(self) -> Optional["Card"]:
        return self.logic.card_node

    def is_occupied(self) -> bool:
        return self.logic.is_occupied()

    def assign_card(self, card: "Card"):
        self.logic.set_card(card)
        self.add_child(card)
        if isinstance(card, Control):
            card.set_anchors_preset(LayoutPreset.TOP_LEFT)
            card.size_flags_horizontal = 0
            card.size_flags_vertical = 0

        self._update_card_geometry()
        card._mark_dirty()

    def set_quad_geometry(self, points: list[Vector2]) -> None:
        """
        Sets the explicit 4-point geometry for this slot.
        Updates both the visual list and the numpy cache for physics.
        """
        if not points or len(points) != 4:
            return

        self._visual_poly_points = points

        count = len(points)
        self._poly_cache = np.zeros((count, 2), dtype=np.float64)
        for i in range(count):
            self._poly_cache[i, 0] = points[i].x
            self._poly_cache[i, 1] = points[i].y

        self.visuals.update_shape(self._visual_poly_points)
        self._update_card_geometry()

    def _update_card_geometry(self):
        """
        Calculates and injects the perspective geometry into the assigned card.
        CHANGED: Now works entirely in local coordinate spaces without global conversions.
        """
        if not self.logic.is_occupied():
            return

        card = self.logic.card_node
        if not self._visual_poly_points:
            return

        padding = 4.0
        offset_points = Geometry2D.offset_polygon(self._visual_poly_points, padding)

        if not offset_points:
            return

        slot_to_card = card.get_transform().affine_inverse()
        card_local_points = [slot_to_card.xform(p) for p in offset_points]
        card.set_quad_geometry(card_local_points)

    def _has_point(self, point: Vector2) -> bool:
        """
        Checks if the point (in Local Space) is inside the custom geometry.
        Uses the cached numpy array for Cython compatibility.
        """
        if not self._visual_poly_points or len(self._visual_poly_points) < 3:
            return self.get_rect().has_point(point)

        return Geometry2D.is_point_in_polygon(point, self._poly_cache)

    def _center_card(self, card: "Card"):
        center_x = self.size.x / 2
        center_y = self.size.y / 2
        card.position = Vector2(center_x, center_y)

    def remove_card(self) -> Optional["Card"]:
        c = self.logic.clear_card()
        if c:
            self.remove_child(c)
        return c
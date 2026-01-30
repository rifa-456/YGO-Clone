import pygame
import math
from typing import List
from engine.ui.range import Range
from engine.ui.enums import FocusMode
from engine.math.datatypes.vector2 import Vector2
from engine.math.datatypes.color import Color
from engine.math.datatypes.rect2 import Rect2
from engine.scene.main.signal import Signal


class ScrollBar(Range):
    """
    A ScrollBar that uses geometric primitives (Triangles) for buttons
    and supports dragging.
    """

    def __init__(self, orientation: int = 0, name: str = "ScrollBar"):
        super().__init__(name)
        self.orientation = orientation
        self.focus_mode = FocusMode.CLICK
        self.scrolling = Signal("scrolling")

        self._drag_active: bool = False
        self._drag_offset: float = 0.0

        self._color_arrow_active = Color(1.0, 0.9, 0.0, 1.0)
        self._color_arrow_inactive = Color(0.3, 0.3, 0.3, 0.5)
        self._color_grabber = Color(0.5, 0.5, 0.5, 1.0)
        self._color_bg = Color(0.0, 0.0, 0.0, 0.0)

        self.min_size = Vector2(16, 16)

    def _get_area_size(self) -> float:
        return self.size.y if self.orientation == 0 else self.size.x

    def _get_thickness(self) -> float:
        return self.size.x if self.orientation == 0 else self.size.y

    def _get_grabber_size(self) -> float:
        area_size = self._get_area_size()
        arrow_size = self._get_thickness()
        track_size = area_size - (arrow_size * 2)

        if track_size <= 0:
            return 0.0

        range_len = self.max_value - self.min_value
        if range_len <= 0:
            return 0.0

        ratio = self.page / (range_len + self.page)
        grabber_size = track_size * ratio

        return max(grabber_size, 10.0)

    def _get_grabber_offset(self) -> float:
        area_size = self._get_area_size()
        arrow_size = self._get_thickness()
        track_size = area_size - (arrow_size * 2)
        grabber_size = self._get_grabber_size()

        scrollable_len = track_size - grabber_size
        range_len = self.max_value - self.min_value

        if range_len <= 0 or scrollable_len <= 0:
            return float(arrow_size)

        ratio = (self.value - self.min_value) / range_len
        return arrow_size + (ratio * scrollable_len)

    def _gui_input(self, event: pygame.event.Event):
        super()._gui_input(event)

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self._handle_click(Vector2(event.pos[0], event.pos[1]))

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self._drag_active = False

        elif event.type == pygame.MOUSEMOTION:
            if self._drag_active:
                self._handle_drag(Vector2(event.pos[0], event.pos[1]))

    def _handle_click(self, global_pos: Vector2):
        local_pos = self.get_global_transform().affine_inverse().xform(global_pos)
        click_coord = local_pos.y if self.orientation == 0 else local_pos.x

        arrow_size = self._get_thickness()
        area_size = self._get_area_size()

        if click_coord < arrow_size:
            self.value -= self.step
            return

        if click_coord > (area_size - arrow_size):
            self.value += self.step
            return

        grabber_offset = self._get_grabber_offset()
        grabber_size = self._get_grabber_size()

        if grabber_offset <= click_coord <= grabber_offset + grabber_size:
            self._drag_active = True
            self._drag_offset = click_coord - grabber_offset
        else:
            if click_coord < grabber_offset:
                self.value -= self.page
            else:
                self.value += self.page

    def _handle_drag(self, global_pos: Vector2):
        local_pos = self.get_global_transform().affine_inverse().xform(global_pos)
        curr_coord = local_pos.y if self.orientation == 0 else local_pos.x

        arrow_size = self._get_thickness()
        area_size = self._get_area_size()
        grabber_size = self._get_grabber_size()
        track_size = area_size - (arrow_size * 2)
        scrollable_len = track_size - grabber_size

        if scrollable_len <= 0:
            return

        relative_pos = curr_coord - arrow_size - self._drag_offset
        ratio = relative_pos / scrollable_len
        ratio = max(0.0, min(1.0, ratio))

        new_val = self.min_value + (ratio * (self.max_value - self.min_value))
        self.value = new_val

    def _draw(self):
        thickness = self._get_thickness()
        length = self._get_area_size()

        arrow_size = thickness

        top_color = self._color_arrow_active if self.value > self.min_value else self._color_arrow_inactive
        self._draw_arrow(0, arrow_size, thickness, top_color, direction=-1)

        btm_color = self._color_arrow_active if self.value < (self.max_value - 0.01) else self._color_arrow_inactive
        self._draw_arrow(length - arrow_size, arrow_size, thickness, btm_color, direction=1)

        grabber_offset = self._get_grabber_offset()
        grabber_size = self._get_grabber_size()

        padding = 2

        if self.orientation == 0:
            rect = Rect2(padding, grabber_offset, thickness - (padding * 2), grabber_size)
        else:
            rect = Rect2(grabber_offset, padding, grabber_size, thickness - (padding * 2))

        self.draw_rect(rect, self._color_grabber)

    def _draw_arrow(self, offset: float, arrow_len: float, thickness: float, color: Color, direction: int):
        """
        Draws an arrow triangle.
        Direction: -1 for Up/Left (Start), 1 for Down/Right (End)
        """
        center_cross = thickness * 0.5
        padding = 4.0
        half_base = (thickness - padding * 2) * 0.5

        # Calculate main axis coordinates (Y for Vert, X for Horz)
        if direction == 1:  # End
            base_main = offset + padding
            tip_main = offset + arrow_len - padding
        else:  # Start
            base_main = offset + arrow_len - padding
            tip_main = offset + padding

        if self.orientation == 0:  # Vertical
            # Main Axis: Y, Cross Axis: X
            p1 = Vector2(center_cross, tip_main)  # Tip
            p2 = Vector2(center_cross - half_base, base_main)  # Base Left
            p3 = Vector2(center_cross + half_base, base_main)  # Base Right
        else:  # Horizontal
            # Main Axis: X, Cross Axis: Y
            p1 = Vector2(tip_main, center_cross)  # Tip
            p2 = Vector2(base_main, center_cross - half_base)  # Base Top
            p3 = Vector2(base_main, center_cross + half_base)  # Base Bottom

        self.draw_colored_polygon([p1, p2, p3], color)


class VScrollBar(ScrollBar):
    def __init__(self, name: str = "VScrollBar"):
        super().__init__(orientation=0, name=name)
        self.min_size = Vector2(12, 0)


class HScrollBar(ScrollBar):
    def __init__(self, name: str = "HScrollBar"):
        super().__init__(orientation=1, name=name)
        self.min_size = Vector2(0, 12)
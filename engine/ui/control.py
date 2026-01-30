import math
import pygame
from typing import Optional, Dict, Any
from engine.math.datatypes.color import Color
from engine.core.textures.texture import Texture
from engine.scene.two_d.canvas_item import CanvasItem
from engine.scene.main.node import Node
from engine.scene.main.signal import Signal
from engine.scene.main.input import Input
from engine.math.datatypes.vector2 import Vector2
from engine.math.datatypes.rect2 import Rect2
from engine.math.datatypes.transform2d import Transform2D
from engine.math import affine
from engine.logger import Logger

from engine.ui.enums import (
    LayoutPreset,
    SizeFlag,
    MouseFilter,
    FocusMode,
    CursorShape,
    GrowDirection,
    Side,
)
from engine.ui.theme import Theme, StyleBox
from game.autoload.settings import Settings
from servers.rendering.rendering_server import RenderingServer


class Control(CanvasItem):

    NOTIFICATION_RESIZED = 40
    NOTIFICATION_MOUSE_ENTER = 41
    NOTIFICATION_MOUSE_EXIT = 42
    NOTIFICATION_FOCUS_ENTER = 43
    NOTIFICATION_FOCUS_EXIT = 44
    NOTIFICATION_THEME_CHANGED = 45
    NOTIFICATION_SORT_CHILDREN = 46
    NOTIFICATION_LAYOUT_CHANGED = 47

    def __init__(self, name: str = "Control"):
        super().__init__(name)

        self._anchor_left: float = 0.0
        self._anchor_top: float = 0.0
        self._anchor_right: float = 0.0
        self._anchor_bottom: float = 0.0

        self._offset_left: float = 0.0
        self._offset_top: float = 0.0
        self._offset_right: float = 0.0
        self._offset_bottom: float = 0.0

        self._grow_horizontal: GrowDirection = GrowDirection.END
        self._grow_vertical: GrowDirection = GrowDirection.END

        self._position: Vector2 = Vector2(0, 0)
        self._size: Vector2 = Vector2(0, 0)
        self._rotation: float = 0.0
        self._scale: Vector2 = Vector2(1.0, 1.0)
        self._pivot_offset: Vector2 = Vector2(0.0, 0.0)
        self._global_position: Vector2 = Vector2(0, 0)

        self._custom_minimum_size = Vector2(0, 0)
        self._size_flags_horizontal = SizeFlag.FILL
        self._size_flags_vertical = SizeFlag.FILL
        self._size_flags_stretch_ratio: float = 1.0

        self._block_layout_update = False
        self.mouse_filter: MouseFilter = MouseFilter.STOP
        self.focus_mode: FocusMode = FocusMode.NONE
        self.mouse_default_cursor_shape: CursorShape = CursorShape.ARROW
        self.shortcut_context: Optional[object] = None
        self.clip_contents: bool = False
        self.tooltip_text: str = ""

        self._is_mouse_over: bool = False
        self._drag_start_pos: Optional[Vector2] = None
        self._event_accepted: bool = False

        self.theme: Optional[Theme] = None
        self.theme_type_variation: str = ""
        self._theme_owner_node: Optional["Control"] = None
        self._theme_icon_overrides: Dict[str, Texture] = {}
        self._theme_stylebox_overrides: Dict[str, StyleBox] = {}
        self._theme_font_overrides: Dict[str, Any] = {}
        self._theme_color_overrides: Dict[str, Color] = {}
        self._theme_constant_overrides: Dict[str, int] = {}

        self.focus_neighbor_left: str = ""
        self.focus_neighbor_top: str = ""
        self.focus_neighbor_right: str = ""
        self.focus_neighbor_bottom: str = ""
        self.focus_next: str = ""
        self.focus_previous: str = ""

        self.resized = Signal("resized")
        self.gui_input = Signal("gui_input")
        self.mouse_entered = Signal("mouse_entered")
        self.mouse_exited = Signal("mouse_exited")
        self.focus_entered = Signal("focus_entered")
        self.focus_exited = Signal("focus_exited")
        self.size_flags_changed = Signal("size_flags_changed")
        self.minimum_size_changed_signal = Signal("minimum_size_changed")

    def accept_event(self):
        """
        Marks the current input event as handled.
        """
        self._event_accepted = True

    def get_focus_neighbor(self, side: Side) -> Optional["Control"]:
        """
        Returns the focus neighbor for the given side.
        Resolves the NodePath relative to this control.
        """
        path = ""
        side_name = "UNKNOWN"
        if side == Side.LEFT:
            path = self.focus_neighbor_left
            side_name = "LEFT"
        elif side == Side.TOP:
            path = self.focus_neighbor_top
            side_name = "TOP"
        elif side == Side.RIGHT:
            path = self.focus_neighbor_right
            side_name = "RIGHT"
        elif side == Side.BOTTOM:
            path = self.focus_neighbor_bottom
            side_name = "BOTTOM"


        if path:
            node = self.get_node(path)
            if isinstance(node, Control):
                return node
        else:
            Logger.warn(f"[{self.name}] No path defined for {side_name}", "Control")

        return None

    def get_transform(self) -> Transform2D:
        """
        Builds local transform: T_pos * T_pivot * R * S * T_neg_pivot
        """
        t_pos = affine.get_translation(self._position.x, self._position.y)
        t_pivot = affine.get_translation(self._pivot_offset.x, self._pivot_offset.y)
        r = affine.get_rotation(self._rotation)
        s = affine.get_scale(self._scale.x, self._scale.y)
        t_neg_pivot = affine.get_translation(
            -self._pivot_offset.x, -self._pivot_offset.y
        )
        return t_pos @ (t_pivot @ (r @ (s @ t_neg_pivot)))

    def make_input_local(self, event: pygame.event.Event) -> pygame.event.Event:
        """
        Transforms a pygame mouse event into this Control's local coordinate space.
        - Positions are transformed using the full affine inverse
        - Relative motion vectors are transformed using the inverse basis only
          (no translation component, mathematically correct for directions)
        """

        if event.type not in (
                pygame.MOUSEMOTION,
                pygame.MOUSEBUTTONDOWN,
                pygame.MOUSEBUTTONUP,
        ):
            return event

        new_dict = dict(event.__dict__)
        inv: Transform2D = self.get_global_transform().affine_inverse()
        gx, gy = event.pos
        global_pos = Vector2(gx, gy)
        local_pos = inv.xform(global_pos)
        new_dict["pos"] = (local_pos.x, local_pos.y)
        if event.type == pygame.MOUSEMOTION:
            rx, ry = event.rel
            rel_vec = Vector2(rx, ry)
            local_rel = inv.basis_xform_inv(rel_vec)
            new_dict["rel"] = (local_rel.x, local_rel.y)

        return pygame.event.Event(event.type, new_dict)

    def _gui_input(self, event: pygame.event.Event):
        """
        Virtual method.
        Override this to handle GUI input.
        """
        self.gui_input.emit(event)

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.focus_mode in (FocusMode.CLICK, FocusMode.ALL):
                    self.grab_focus()
                self.accept_event()

        if event.type == pygame.KEYDOWN and self.has_focus():
            if Input.is_event_action(event, "ui_left"):
                self._move_focus(Side.LEFT)
                self.accept_event()
            elif Input.is_event_action(event, "ui_right"):
                self._move_focus(Side.RIGHT)
                self.accept_event()
            elif Input.is_event_action(event, "ui_up"):
                self._move_focus(Side.TOP)
                self.accept_event()
            elif Input.is_event_action(event, "ui_down"):
                self._move_focus(Side.BOTTOM)
                self.accept_event()
            elif Input.is_event_action(event, "ui_focus_next"):
                pass

    def _notification(self, what: int):
        super()._notification(what)

        if what == CanvasItem.NOTIFICATION_DRAW:
            self._draw_theme()

        elif what == Node.NOTIFICATION_ENTER_TREE:
            self._update_layout()

            parent = self.get_parent()
            if parent and isinstance(parent, CanvasItem):
                RenderingServer.get_singleton().canvas_item_set_parent(
                    self.get_rid(), parent.get_rid()
                )

        elif what == self.NOTIFICATION_SORT_CHILDREN:
            self._reflow_children()

        elif what == self.NOTIFICATION_RESIZED:
            self.resized.emit()

        elif what == self.NOTIFICATION_VISIBILITY_CHANGED:
            if self.visible:
                self._update_layout()

        elif what == self.NOTIFICATION_ENTER_CANVAS:
            self._update_layout()

        elif what == self.NOTIFICATION_THEME_CHANGED:
            self.queue_redraw()

        elif what == self.NOTIFICATION_FOCUS_ENTER:
            self.focus_entered.emit()
            self.queue_redraw()

        elif what == self.NOTIFICATION_FOCUS_EXIT:
            self.focus_exited.emit()
            self.queue_redraw()

    def _draw_theme(self):
        if self.has_focus():
            style = self.get_theme_stylebox("focus")
            if style:
                style.draw(self.get_rid(), Rect2(0, 0, self._size.x, self._size.y))

    def get_class(self) -> str:
        return "Control"

    def add_theme_icon_override(self, name: str, texture: Texture):
        self._theme_icon_overrides[name] = texture
        self.notification(self.NOTIFICATION_THEME_CHANGED)
        self.queue_redraw()

    def get_theme_icon(self, name: str, theme_type: str = "") -> Optional[Texture]:
        if not theme_type:
            theme_type = self._get_theme_type_variation()

        if name in self._theme_icon_overrides:
            return self._theme_icon_overrides[name]

        current: Optional[Control] = self
        while current:
            if current.theme:
                val = current.theme.get_icon(name, theme_type)
                if val is not None:
                    return val

            if isinstance(current.parent, Control):
                current = current.parent
            else:
                current = None

        return Theme.get_default().get_icon(name, theme_type)

    def add_theme_constant_override(self, name: str, constant: int):
        self._theme_constant_overrides[name] = constant
        self.notification(self.NOTIFICATION_THEME_CHANGED)
        self._update_layout()
        self.queue_redraw()

    def add_theme_color_override(self, name: str, color: Color):
        self._theme_color_overrides[name] = color
        self.notification(self.NOTIFICATION_THEME_CHANGED)
        self.queue_redraw()

    def add_theme_stylebox_override(self, name: str, stylebox: StyleBox):
        self._theme_stylebox_overrides[name] = stylebox
        self.notification(self.NOTIFICATION_THEME_CHANGED)
        self._update_layout()
        self.queue_redraw()

    def add_theme_font_override(self, name: str, font: pygame.font.Font):
        self._theme_font_overrides[name] = font
        self.notification(self.NOTIFICATION_THEME_CHANGED)
        self._update_layout()
        self.queue_redraw()

    def get_theme_color(self, name: str, theme_type: str = "") -> Color:
        if not theme_type:
            theme_type = self._get_theme_type_variation()

        if name in self._theme_color_overrides:
            return self._theme_color_overrides[name]

        current: Optional[Control] = self
        while current:
            if current.theme:
                val = current.theme.get_color(name, theme_type)
                if val is not None:
                    return val

            if isinstance(current.parent, Control):
                current = current.parent
            else:
                current = None

        val = Theme.get_default().get_color(name, theme_type)
        return val if val is not None else Color(1, 0, 1, 1)

    def get_theme_font(self, name: str, theme_type: str = "") -> pygame.font.Font:
        if not theme_type:
            theme_type = self._get_theme_type_variation()

        if name in self._theme_font_overrides:
            return self._theme_font_overrides[name]

        current: Optional[Control] = self
        while current:
            if current.theme:
                val = current.theme.get_font(name, theme_type)
                if val is not None:
                    return val

            if isinstance(current.parent, Control):
                current = current.parent
            else:
                current = None

        val = Theme.get_default().get_font(name, theme_type)
        return val if val is not None else pygame.font.SysFont("Arial", 14)

    def get_theme_stylebox(self, name: str, theme_type: str = "") -> Optional[StyleBox]:
        if not theme_type:
            theme_type = self._get_theme_type_variation()

        if name in self._theme_stylebox_overrides:
            return self._theme_stylebox_overrides[name]

        current: Optional[Control] = self
        while current:
            if current.theme:
                val = current.theme.get_stylebox(name, theme_type)
                if val is not None:
                    return val

            if isinstance(current.parent, Control):
                current = current.parent
            else:
                current = None

        return Theme.get_default().get_stylebox(name, theme_type)

    def _get_theme_type_variation(self) -> str:
        return (
            self.theme_type_variation if self.theme_type_variation else self.get_class()
        )

    def get_theme_constant(self, name: str, theme_type: str = "") -> int:
        if not theme_type:
            theme_type = self._get_theme_type_variation()

        if name in self._theme_constant_overrides:
            return self._theme_constant_overrides[name]

        current: Optional[Control] = self
        while current:
            if current.theme:
                val = current.theme.get_constant(name, theme_type)
                if val is not None:
                    return val

            if isinstance(current.parent, Control):
                current = current.parent
            else:
                current = None

        val = Theme.get_default().get_constant(name, theme_type)
        return val if val is not None else 0

    @staticmethod
    def get_drag_data(position: Vector2) -> Any:
        pass

    @staticmethod
    def can_drop_data(position: Vector2, data: Any) -> bool:
        pass

    @staticmethod
    def drop_data(position: Vector2, data: Any):
        pass

    def _enter_tree(self):
        """Override: Controls start layout calculation when entering tree."""
        super()._enter_tree()

    def _move_focus(self, side: Side):
        """
        Attempts to move focus to the neighbor on the specified side.
        Use automatic geometry search if no neighbor is defined.
        """
        neighbor = self.get_focus_neighbor(side)
        if neighbor:
            if neighbor.is_visible_in_tree() and neighbor.focus_mode != FocusMode.NONE:
                Logger.debug(f"[{self.name}] Transferring focus to neighbor: {neighbor.name}", "Control")
                neighbor.grab_focus()
                return
            else:
                Logger.warn(
                    f"[{self.name}] Neighbor found ({neighbor.name}) but is invalid (Visible={neighbor.is_visible_in_tree()}, FocusMode={neighbor.focus_mode})",
                    "Control"
                )
        else:
            Logger.debug(f"[{self.name}] No explicit neighbor found. Attempting geometry search...", "Control")

        viewport = self.get_viewport()
        if viewport:
            next_focus = viewport.find_next_focus(self, side)
            if next_focus:
                Logger.info(f"[{self.name}] Geometry search found: {next_focus.name}", "Control")
                next_focus.grab_focus()
            else:
                Logger.info(f"[{self.name}] Geometry search found NOTHING.", "Control")

    def _mark_dirty(self):
        self.notification(self.NOTIFICATION_TRANSFORM_CHANGED)

    def has_point(self, point: Vector2) -> bool:
        """
        Check if a global point is inside this control's hit area.
        """
        try:
            inv = self.get_global_transform().affine_inverse()
        except Exception:
            return False

        local_point = inv.xform(point)
        return self._has_point(local_point)

    def _has_point(self, point: Vector2) -> bool:
        """
        Virtual method to check if a local point is inside the control.
        """
        return (0 <= point.x <= self._size.x) and (0 <= point.y <= self._size.y)

    @property
    def rotation(self) -> float:
        return self._rotation

    @rotation.setter
    def rotation(self, radians: float):
        if self._rotation != radians:
            self._rotation = radians
            self._mark_dirty()

    @property
    def rotation_degrees(self) -> float:
        return math.degrees(self._rotation)

    @rotation_degrees.setter
    def rotation_degrees(self, degrees: float):
        self.rotation = math.radians(degrees)

    @property
    def scale(self) -> Vector2:
        return self._scale

    @scale.setter
    def scale(self, value: Vector2):
        if self._scale.x != value.x or self._scale.y != value.y:
            self._scale = value
            self._mark_dirty()

    @property
    def pivot_offset(self) -> Vector2:
        return self._pivot_offset

    @pivot_offset.setter
    def pivot_offset(self, value: Vector2):
        if self._pivot_offset.x != value.x or self._pivot_offset.y != value.y:
            self._pivot_offset = value
            self._mark_dirty()

    def _set_anchor(self, attr_name: str, value: float):
        if getattr(self, attr_name) != value:
            setattr(self, attr_name, value)
            self._update_layout()

    @property
    def anchor_left(self) -> float:
        return self._anchor_left

    @anchor_left.setter
    def anchor_left(self, v):
        self._set_anchor("_anchor_left", v)

    @property
    def anchor_top(self) -> float:
        return self._anchor_top

    @anchor_top.setter
    def anchor_top(self, v):
        self._set_anchor("_anchor_top", v)

    @property
    def anchor_right(self) -> float:
        return self._anchor_right

    @anchor_right.setter
    def anchor_right(self, v):
        self._set_anchor("_anchor_right", v)

    @property
    def anchor_bottom(self) -> float:
        return self._anchor_bottom

    @anchor_bottom.setter
    def anchor_bottom(self, v):
        self._set_anchor("_anchor_bottom", v)

    def _set_offset(self, attr_name: str, value: float):
        if getattr(self, attr_name) != value:
            setattr(self, attr_name, value)
            self._update_layout()

    @property
    def offset_left(self) -> float:
        return self._offset_left

    @offset_left.setter
    def offset_left(self, v):
        self._set_offset("_offset_left", v)

    @property
    def offset_top(self) -> float:
        return self._offset_top

    @offset_top.setter
    def offset_top(self, v):
        self._set_offset("_offset_top", v)

    @property
    def offset_right(self) -> float:
        return self._offset_right

    @offset_right.setter
    def offset_right(self, v):
        self._set_offset("_offset_right", v)

    @property
    def offset_bottom(self) -> float:
        return self._offset_bottom

    @offset_bottom.setter
    def offset_bottom(self, v):
        self._set_offset("_offset_bottom", v)

    @property
    def custom_minimum_size(self) -> Vector2:
        """
        The minimum size forced by the user.
        """
        return self._custom_minimum_size

    @custom_minimum_size.setter
    def custom_minimum_size(self, value: Vector2):
        if self._custom_minimum_size != value:
            self._custom_minimum_size = value
            self.minimum_size_changed()

    def get_minimum_size(self) -> Vector2:
        """
        Virtual.
        Override this to calculate minimum size based on content
        (e.g. Label text size, Container children).
        """
        return Vector2(0, 0)

    def get_global_position(self) -> Vector2:
        """
        Returns the global position of the Control relative to the screen/canvas.
        Calculated via the global transform matrix to account for all parent offsets (e.g., Layouts).
        """
        return self.get_global_transform().origin

    def get_combined_minimum_size(self) -> Vector2:
        """
        Returns the greater of custom_minimum_size and get_minimum_size().
        """
        content_min = self.get_minimum_size()
        return Vector2(
            max(content_min.x, self._custom_minimum_size.x),
            max(content_min.y, self._custom_minimum_size.y),
        )

    def minimum_size_changed(self):
        """
        Invalidates the cache and notifies parents to update layout.
        """
        self.minimum_size_changed_signal.emit()
        if self.parent and hasattr(self.parent, "on_child_min_size_changed"):
            self.parent.on_child_min_size_changed()
        else:
            self._update_layout()

    def on_child_min_size_changed(self):
        """
        Called when a child's minimum size changes.
        Override in Containers.
        """
        self.minimum_size_changed()

    def queue_sort(self):
        """
        Schedules a layout update.
        Deferred execution via SceneTree to prevent recursion.
        """
        if self.is_inside_tree() and self.tree:
            self.tree.queue_layout_update(self)

    def get_size(self) -> Vector2:
        return self._size

    def set_size(self, value: Vector2):
        """
        Resizes the Control.
        This modifies offsets based on anchors.
        """
        if self._size.is_equal_approx(value):
            return

        diff = value - self._size
        self._offset_right += diff.x
        self._offset_bottom += diff.y
        self._update_layout()

    def get_position(self) -> Vector2:
        return self._position

    def set_position(self, value: Vector2):
        if self._position.is_equal_approx(value):
            return

        diff = value - self._position
        self._offset_left += diff.x
        self._offset_right += diff.x
        self._offset_top += diff.y
        self._offset_bottom += diff.y
        self._update_layout()

    @property
    def position(self) -> Vector2:
        return self.get_position()

    @position.setter
    def position(self, value: Vector2):
        self.set_position(value)

    @property
    def size(self) -> Vector2:
        return self.get_size()

    @size.setter
    def size(self, value: Vector2):
        self.set_size(value)

    def _update_layout(self):
        """
        Calculates position and size based on parent rect, anchors, and offsets.
        Uses Strict Rect2 math.
        """
        if self._block_layout_update:
            return

        parent_size = Vector2(Settings.SCREEN_WIDTH, Settings.SCREEN_HEIGHT)
        if self.parent and isinstance(self.parent, Control):
            parent_size = self.parent.get_size()

        left = (self._anchor_left * parent_size.x) + self._offset_left
        top = (self._anchor_top * parent_size.y) + self._offset_top
        right = (self._anchor_right * parent_size.x) + self._offset_right
        bottom = (self._anchor_bottom * parent_size.y) + self._offset_bottom

        width = right - left
        height = bottom - top

        min_size = self.get_combined_minimum_size()

        if width < min_size.x:
            if self._grow_horizontal == GrowDirection.BEGIN:
                left = right - min_size.x
            elif self._grow_horizontal == GrowDirection.BOTH:
                center = left + width * 0.5
                left = center - min_size.x * 0.5
            width = min_size.x

        if height < min_size.y:
            if self._grow_vertical == GrowDirection.BEGIN:
                top = bottom - min_size.y
            elif self._grow_vertical == GrowDirection.BOTH:
                center = top + height * 0.5
                top = center - min_size.y * 0.5
            height = min_size.y

        new_pos = Vector2(left, top)
        new_size = Vector2(width, height)

        pos_changed = not new_pos.is_equal_approx(self._position)
        size_changed = not new_size.is_equal_approx(self._size)

        self._position = new_pos
        self._size = new_size

        if pos_changed or size_changed:
            self.set_transform(self.get_transform())
            self.item_rect_changed.emit()

        if size_changed:
            self.notification(self.NOTIFICATION_RESIZED)
            if self.parent and isinstance(self.parent, Control):
                self.parent.queue_sort()
            self.queue_sort()
            self.on_resized()

    @property
    def grow_horizontal(self) -> GrowDirection:
        return self._grow_horizontal

    @grow_horizontal.setter
    def grow_horizontal(self, value: GrowDirection):
        if self._grow_horizontal != value:
            self._grow_horizontal = value
            self._update_layout()

    @property
    def grow_vertical(self) -> GrowDirection:
        return self._grow_vertical

    @grow_vertical.setter
    def grow_vertical(self, value: GrowDirection):
        if self._grow_vertical != value:
            self._grow_vertical = value
            self._update_layout()

    def on_resized(self):
        pass

    def _reflow_children(self):
        for child in self.children:
            if isinstance(child, Control):
                child._update_layout()

    def get_rect(self) -> Rect2:
        """Returns the control's local rect (0, 0, width, height)"""
        return Rect2(0, 0, self._size.x, self._size.y)

    def get_global_rect(self) -> Rect2:
        """
        Returns the global screen-space bounding box.
        Approximated as AABB of transformed rect.
        """
        gt = self.get_global_transform()
        p0 = gt.xform(Vector2(0, 0))
        p1 = gt.xform(Vector2(self._size.x, 0))
        p2 = gt.xform(Vector2(self._size.x, self._size.y))
        p3 = gt.xform(Vector2(0, self._size.y))

        min_x = min(p0.x, p1.x, p2.x, p3.x)
        max_x = max(p0.x, p1.x, p2.x, p3.x)
        min_y = min(p0.y, p1.y, p2.y, p3.y)
        max_y = max(p0.y, p1.y, p2.y, p3.y)

        return Rect2(min_x, min_y, max_x - min_x, max_y - min_y)

    def get_focus_rect(self) -> pygame.Rect:
        return self.get_global_rect()

    def set_anchors_preset(self, preset: LayoutPreset, keep_offsets: bool = False):
        if preset == LayoutPreset.TOP_LEFT:
            self._set_anchors(0, 0, 0, 0)
        elif preset == LayoutPreset.TOP_RIGHT:
            self._set_anchors(1, 0, 1, 0)
        elif preset == LayoutPreset.BOTTOM_LEFT:
            self._set_anchors(0, 1, 0, 1)
        elif preset == LayoutPreset.BOTTOM_RIGHT:
            self._set_anchors(1, 1, 1, 1)
        elif preset == LayoutPreset.FULL_RECT:
            self._set_anchors(0, 0, 1, 1)
        elif preset == LayoutPreset.CENTER:
            self._set_anchors(0.5, 0.5, 0.5, 0.5)
        elif preset == LayoutPreset.TOP_WIDE:
            self._set_anchors(0, 0, 1, 0)
        elif preset == LayoutPreset.BOTTOM_WIDE:
            self._set_anchors(0, 1, 1, 1)
        elif preset == LayoutPreset.LEFT_WIDE:
            self._set_anchors(0, 0, 0, 1)
        elif preset == LayoutPreset.RIGHT_WIDE:
            self._set_anchors(1, 0, 1, 1)

        if not keep_offsets:
            self._offset_left = 0
            self._offset_top = 0
            self._offset_right = 0
            self._offset_bottom = 0

        self._update_layout()

    def _set_anchors(self, left, top, right, bottom):
        self._anchor_left = left
        self._anchor_top = top
        self._anchor_right = right
        self._anchor_bottom = bottom

    def grab_focus(self):
        if self.focus_mode == FocusMode.NONE:
            return
        if not self.is_visible_in_tree():
            return

        viewport = self.get_viewport()
        if viewport:
            viewport.gui_set_focus(self)
            self._update_layout()

    def release_focus(self):
        viewport = self.get_viewport()
        if viewport and viewport.gui_get_focus_owner() == self:
            viewport.gui_release_focus()
            self._update_layout()

    def has_focus(self) -> bool:
        viewport = self.get_viewport()
        if viewport:
            return viewport.gui_get_focus_owner() == self
        return False

    def force_drag(self, data: Any, preview: Optional["Control"]):
        if data is None:
            return

        viewport = self.get_viewport()
        if viewport:
            viewport.gui_set_drag_data(data, self, preview)

    @property
    def size_flags_horizontal(self) -> int:
        return self._size_flags_horizontal

    @size_flags_horizontal.setter
    def size_flags_horizontal(self, v):
        if self._size_flags_horizontal != v:
            self._size_flags_horizontal = v
            self.size_flags_changed.emit()
            self.minimum_size_changed()

    @property
    def size_flags_vertical(self) -> int:
        return self._size_flags_vertical

    @size_flags_vertical.setter
    def size_flags_vertical(self, v):
        if self._size_flags_vertical != v:
            self._size_flags_vertical = v
            self.size_flags_changed.emit()
            self.minimum_size_changed()

    @property
    def size_flags_stretch_ratio(self) -> float:
        return self._size_flags_stretch_ratio

    @size_flags_stretch_ratio.setter
    def size_flags_stretch_ratio(self, value: float):
        if self._size_flags_stretch_ratio != value:
            self._size_flags_stretch_ratio = value
            self.size_flags_changed.emit()

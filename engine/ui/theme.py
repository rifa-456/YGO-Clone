import math
from abc import ABC, abstractmethod
from typing import Dict, Optional, Any, TypeVar, List

from engine.core.resource import Resource
from engine.core.textures.texture import Texture
from engine.math.datatypes.vector2 import Vector2
from engine.math.datatypes.color import Color
from engine.math.datatypes.rect2 import Rect2
from engine.core.rid import RID
from engine.servers.rendering.rendering_server import RenderingServer

T = TypeVar("T")


class StyleBox(Resource, ABC):
    """
    Base class for drawing stylized boxes (backgrounds, borders).
    Uses the RenderingServer strictly.
    """

    def __init__(self):
        super().__init__()
        self.content_margin_left: float = 0.0
        self.content_margin_top: float = 0.0
        self.content_margin_right: float = 0.0
        self.content_margin_bottom: float = 0.0

    @abstractmethod
    def draw(self, canvas_item: RID, rect: Rect2):
        """
        Draws the stylebox onto the given CanvasItem RID.
        """
        pass

    def get_minimum_size(self) -> Vector2:
        return Vector2(
            self.content_margin_left + self.content_margin_right,
            self.content_margin_top + self.content_margin_bottom,
        )


class StyleBoxFlat(StyleBox):
    """
    Draws a flat color box with optional borders and corner radius using generated geometry.
    """

    def __init__(self):
        super().__init__()
        self.bg_color: Color = Color(0.2, 0.2, 0.2, 1.0)
        self.border_color: Color = Color(0.8, 0.8, 0.8, 1.0)

        self._border_width_left: int = 0
        self._border_width_top: int = 0
        self._border_width_right: int = 0
        self._border_width_bottom: int = 0

        self._corner_radius_top_left: int = 0
        self._corner_radius_top_right: int = 0
        self._corner_radius_bottom_right: int = 0
        self._corner_radius_bottom_left: int = 0

        self.draw_center: bool = True
        self.shadow_color: Color = Color(0, 0, 0, 0.5)
        self.shadow_size: int = 0
        self.shadow_offset: Vector2 = Vector2(0, 0)

        self._corner_detail: int = 4
        self._server = RenderingServer.get_singleton()

    @property
    def border_width(self) -> int:
        return self._border_width_left

    @border_width.setter
    def border_width(self, width: int):
        self._border_width_left = width
        self._border_width_top = width
        self._border_width_right = width
        self._border_width_bottom = width

    @property
    def corner_radius(self) -> int:
        return self._corner_radius_top_left

    @corner_radius.setter
    def corner_radius(self, radius: int):
        self._corner_radius_top_left = radius
        self._corner_radius_top_right = radius
        self._corner_radius_bottom_right = radius
        self._corner_radius_bottom_left = radius

    def _get_rounded_rect_points(
        self, rect: Rect2, expand: float = 0.0
    ) -> List[Vector2]:
        """
        Generates vertices for a rounded rectangle.
        """
        x = rect.position.x - expand
        y = rect.position.y - expand
        w = rect.size.x + (expand * 2)
        h = rect.size.y + (expand * 2)

        points: List[Vector2] = []

        def add_arc(center_x, center_y, radius, start_angle, end_angle):
            if radius <= 0:
                points.append(Vector2(center_x, center_y))
                return

            safe_radius = max(0.0, min(radius, min(w, h) / 2.0))
            steps = self._corner_detail
            for i in range(steps + 1):
                theta = start_angle + (end_angle - start_angle) * (i / steps)
                px = center_x + math.cos(theta) * safe_radius
                py = center_y + math.sin(theta) * safe_radius
                points.append(Vector2(px, py))

        add_arc(
            x + w - self._corner_radius_top_right,
            y + self._corner_radius_top_right,
            self._corner_radius_top_right,
            -math.pi / 2,
            0,
        )

        add_arc(
            x + w - self._corner_radius_bottom_right,
            y + h - self._corner_radius_bottom_right,
            self._corner_radius_bottom_right,
            0,
            math.pi / 2,
        )

        add_arc(
            x + self._corner_radius_bottom_left,
            y + h - self._corner_radius_bottom_left,
            self._corner_radius_bottom_left,
            math.pi / 2,
            math.pi,
        )

        add_arc(
            x + self._corner_radius_top_left,
            y + self._corner_radius_top_left,
            self._corner_radius_top_left,
            math.pi,
            3 * math.pi / 2,
        )
        return points

    def draw(self, canvas_item: RID, rect: Rect2):
        if self.shadow_size > 0:
            shadow_rect = Rect2(
                rect.position.x + self.shadow_offset.x,
                rect.position.y + self.shadow_offset.y,
                rect.size.x,
                rect.size.y,
            )
            shadow_points = self._get_rounded_rect_points(shadow_rect, expand=0)
            self._server.canvas_item_add_polygon(
                canvas_item,
                shadow_points,
                [self.shadow_color] * len(shadow_points),
            )

        if self.draw_center:
            points = self._get_rounded_rect_points(rect)
            self._server.canvas_item_add_polygon(
                canvas_item,
                points,
                [self.bg_color] * len(points),
            )

        avg_border = (self._border_width_left + self._border_width_top) // 2
        if avg_border > 0:
            border_points = self._get_rounded_rect_points(rect)
            border_points.append(border_points[0])
            self._server.canvas_item_add_polyline(
                canvas_item,
                border_points,
                [self.border_color] * len(border_points),
                float(avg_border),
            )


class StyleBoxTexture(StyleBox):
    """
    Draws a texture, potentially scaled.
    """

    def __init__(self, texture: Optional[Texture] = None):
        super().__init__()
        self.texture = texture
        self.modulate_color: Color = Color(1, 1, 1, 1)
        self._server = RenderingServer.get_singleton()

    def draw(self, canvas_item: RID, rect: Rect2):
        if not self.texture:
            return

        tex_rid = self.texture.get_rid()
        self._server.canvas_item_add_texture_rect(
            canvas_item, rect, tex_rid, False, self.modulate_color
        )


class Theme(Resource):
    """
    A resource used to style Controls.
    Stores Colors, Fonts, Constants, StyleBoxes, and Icons.
    """

    _default_theme: Optional["Theme"] = None

    def __init__(self):
        super().__init__()
        self._colors: Dict[str, Dict[str, Color]] = {}
        self._constants: Dict[str, Dict[str, int]] = {}
        self._fonts: Dict[str, Dict[str, Any]] = {}
        self._styleboxes: Dict[str, Dict[str, StyleBox]] = {}
        self._icons: Dict[str, Dict[str, Texture]] = {}

    @staticmethod
    def get_default() -> "Theme":
        if Theme._default_theme is None:
            Theme._default_theme = Theme()
        return Theme._default_theme

    @staticmethod
    def set_default(theme: "Theme"):
        Theme._default_theme = theme

    def _set_item(
        self, storage_name: str, name: str, item_type: str, value: Any
    ) -> None:
        storage: Dict[str, Dict[str, Any]] = getattr(self, storage_name)
        if item_type not in storage:
            storage[item_type] = {}
        storage[item_type][name] = value

    def _get_item(self, storage_name: str, name: str, item_type: str) -> Optional[Any]:
        storage: Dict[str, Dict[str, Any]] = getattr(self, storage_name)
        if item_type in storage and name in storage[item_type]:
            return storage[item_type][name]

        default = Theme.get_default()
        if default and default is not self:
            return default._get_item(storage_name, name, item_type)

        return None

    def set_icon(self, name: str, item_type: str, icon: Texture):
        self._set_item("_icons", name, item_type, icon)

    def get_icon(self, name: str, item_type: str) -> Optional[Texture]:
        return self._get_item("_icons", name, item_type)

    def set_color(self, name: str, item_type: str, color: Color):
        if not isinstance(color, Color):
            raise TypeError(
                f"Theme.set_color expected type 'Color', got '{type(color).__name__}'. "
                f"Value: {color}. Ensure you are normalizing 0-255 values to 0.0-1.0."
            )
        self._set_item("_colors", name, item_type, color)

    def get_color(self, name: str, item_type: str) -> Optional[Color]:
        res = self._get_item("_colors", name, item_type)
        return res if res is not None else Color(1, 0, 1, 1)

    def set_constant(self, name: str, item_type: str, constant: int):
        self._set_item("_constants", name, item_type, constant)

    def get_constant(self, name: str, item_type: str) -> Optional[int]:
        res = self._get_item("_constants", name, item_type)
        return res if res is not None else 0

    def set_font(self, name: str, item_type: str, font: Any):
        self._set_item("_fonts", name, item_type, font)

    def get_font(self, name: str, item_type: str) -> Optional[Any]:
        return self._get_item("_fonts", name, item_type)

    def set_stylebox(self, name: str, item_type: str, stylebox: StyleBox):
        self._set_item("_styleboxes", name, item_type, stylebox)

    def get_stylebox(self, name: str, item_type: str) -> Optional[StyleBox]:
        return self._get_item("_styleboxes", name, item_type)
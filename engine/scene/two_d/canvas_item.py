from typing import Optional, List, TYPE_CHECKING
from engine.core.textures.texture import Texture
from engine.scene.main.node import Node
from engine.math.datatypes.transform2d import Transform2D
from engine.math.datatypes.vector2 import Vector2
from engine.math.datatypes.color import Color
from engine.math.datatypes.rect2 import Rect2
from engine.scene.main.signal import Signal
from engine.servers.rendering.rendering_server import RenderingServer
from engine.core.rid import RID

if TYPE_CHECKING:
    from engine.ui.theme import StyleBox


class CanvasItem(Node):
    """
    Base class for anything that draws 2D.
    Acts as a client driver for the RenderingServer.
    """

    NOTIFICATION_TRANSFORM_CHANGED = 2000
    NOTIFICATION_DRAW = 2001
    NOTIFICATION_VISIBILITY_CHANGED = 2002
    NOTIFICATION_ENTER_CANVAS = 2003
    NOTIFICATION_EXIT_CANVAS = 2004

    def __init__(self, name: str = "CanvasItem"):
        super().__init__(name)

        self._server = RenderingServer.get_singleton()
        self._rid: RID = self._server.canvas_item_allocate()
        self._server.canvas_item_initialize(self._rid)

        self._visible: bool = True
        self._modulate: Color = Color(1, 1, 1, 1)
        self._self_modulate: Color = Color(1, 1, 1, 1)
        self._z_index: int = 0
        self._z_as_relative: bool = True
        self._y_sort_enabled: bool = False
        self._local_transform: Transform2D = Transform2D.identity()

        self.draw = Signal("draw")
        self.visibility_changed = Signal("visibility_changed")
        self.item_rect_changed = Signal("item_rect_changed")

    def get_rid(self) -> RID:
        return self._rid

    def _enter_tree(self):
        super()._enter_tree()
        parent = self.get_parent()
        parent_rid: Optional[RID] = None

        if isinstance(parent, CanvasItem):
            parent_rid = parent.get_rid()
        elif parent and parent.get_class() == "CanvasLayer":
            parent_rid = parent.get_canvas()
        else:
            vp = self.get_viewport()
            if vp:
                parent_rid = vp.get_canvas()

        if parent_rid:
            self._server.canvas_item_set_parent(self._rid, parent_rid)

        self._update_server_transform()
        self._server.canvas_item_set_visible(self._rid, self._visible)
        self._server.canvas_item_set_z_index(self._rid, self._z_index)
        self._server.canvas_item_set_modulate(self._rid, self._modulate)
        self._server.canvas_item_set_self_modulate(self._rid, self._self_modulate)
        self.queue_redraw()

    def _exit_tree(self):
        self._server.canvas_item_set_parent(self._rid, RID())
        super()._exit_tree()

    def _notification(self, what: int) -> None:
        super()._notification(what)
        if what == self.NOTIFICATION_TRANSFORM_CHANGED:
            self._update_server_transform()
            for child in self.children:
                if isinstance(child, CanvasItem):
                    child.notification(self.NOTIFICATION_TRANSFORM_CHANGED)

        elif what == self.NOTIFICATION_DRAW:
            if not self.is_inside_tree():
                return
            self._server.canvas_item_clear(self._rid)
            self._draw()
            self.draw.emit()

        elif what == self.NOTIFICATION_VISIBILITY_CHANGED:
            self.visibility_changed.emit()
            self._server.canvas_item_set_visible(self._rid, self.is_visible_in_tree())

    @property
    def visible(self) -> bool:
        return self._visible

    @visible.setter
    def visible(self, value: bool):
        if self._visible == value:
            return
        self._visible = value
        self.notification(self.NOTIFICATION_VISIBILITY_CHANGED)

    @property
    def modulate(self) -> Color:
        return self._modulate

    @modulate.setter
    def modulate(self, value: Color):
        self._modulate = value
        self._server.canvas_item_set_modulate(self._rid, value)

    @property
    def self_modulate(self) -> Color:
        return self._self_modulate

    @self_modulate.setter
    def self_modulate(self, value: Color):
        self._self_modulate = value
        self._server.canvas_item_set_self_modulate(self._rid, value)

    @property
    def z_index(self) -> int:
        return self._z_index

    @z_index.setter
    def z_index(self, value: int):
        self._z_index = value
        self._server.canvas_item_set_z_index(self._rid, value)

    def set_transform(self, transform: Transform2D):
        self._local_transform = transform
        self.notification(self.NOTIFICATION_TRANSFORM_CHANGED)

    def get_transform(self) -> Transform2D:
        return self._local_transform

    def get_global_transform(self) -> Transform2D:
        """
        Returns the global transform relative to the canvas.
        """
        if self.parent and isinstance(self.parent, CanvasItem):
            return self.parent.get_global_transform() * self._local_transform
        return self._local_transform

    def _update_server_transform(self):
        self._server.canvas_item_set_transform(self._rid, self._local_transform)

    def is_visible_in_tree(self) -> bool:
        if not self._visible:
            return False
        parent = self.get_parent()
        if isinstance(parent, CanvasItem):
            return parent.is_visible_in_tree()
        return True

    def queue_redraw(self):
        """Schedules a redraw request."""
        if self.is_inside_tree():
            self.notification(self.NOTIFICATION_DRAW)

    def _draw(self):
        """Virtual method. Override this to issue draw commands."""
        pass

    def draw_line(
        self, from_pos: Vector2, to_pos: Vector2, color: Color, width: float = 1.0
    ):
        self._server.canvas_item_add_line(self._rid, from_pos, to_pos, color, width)

    def draw_rect(self, rect: Rect2, color: Color):
        self._server.canvas_item_add_rect(self._rid, rect, color)

    def draw_circle(self, position: Vector2, radius: float, color: Color):
        self._server.canvas_item_add_circle(self._rid, position, radius, color)

    def draw_texture(
        self, texture: Texture, position: Vector2, modulate: Color = Color(1, 1, 1, 1)
    ):
        if not texture:
            return
        tex_rid = texture.get_rid()
        rect = Rect2(
            position.x,
            position.y,
            float(texture.get_width()),
            float(texture.get_height()),
        )
        self._server.canvas_item_add_texture_rect(
            self._rid, rect, tex_rid, False, modulate
        )

    def draw_texture_rect(
        self,
        texture: Texture,
        rect: Rect2,
        tile: bool = False,
        modulate: Color = Color(1, 1, 1, 1),
    ):
        if not texture:
            return
        tex_rid = texture.get_rid()
        self._server.canvas_item_add_texture_rect(
            self._rid, rect, tex_rid, tile, modulate
        )

    def draw_polygon(
        self,
        points: List[Vector2],
        colors: List[Color],
        uvs: List[Vector2] = None,
        texture: Texture = None,
    ):
        """
        Draws a textured or colored polygon.
        """
        tex_rid = texture.get_rid() if texture else RID()
        self._server.canvas_item_add_polygon(self._rid, points, colors, uvs, tex_rid)

    def draw_colored_polygon(
        self,
        points: List[Vector2],
        color: Color,
        uvs: List[Vector2] = None,
        texture: Texture = None,
    ):
        """
        Helper to draw a polygon with a single color.
        """
        colors = [color] * len(points)
        self.draw_polygon(points, colors, uvs, texture)

    def draw_style_box(self, style_box: "StyleBox", rect: Rect2):
        """
        Helper to draw a stylebox.
        """
        if style_box:
            style_box.draw(self._rid, rect)

    def get_class(self) -> str:
        return "CanvasItem"

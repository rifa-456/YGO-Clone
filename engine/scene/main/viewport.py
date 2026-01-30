import pygame
from typing import Optional, TYPE_CHECKING, Any, List
from engine.core.rid import RID
from engine.math.datatypes.transform2d import Transform2D
from engine.math.datatypes.vector2 import Vector2
from engine.scene.main.node import Node
from engine.scene.main.signal import Signal
from engine.scene.resources.world_2d import World2D
from engine.servers.rendering.rendering_server import RenderingServer
from engine.logger import Logger
from engine.ui.enums import MouseFilter

if TYPE_CHECKING:
    from engine.ui.control import Control


class Viewport(Node):
    """
    The Viewport is responsible for handling input events, GUI focus, and
    acting as the root for specific scenes.
    """

    def __init__(self, name: str = "Viewport"):
        super().__init__(name)

        self._server = RenderingServer.get_singleton()
        self._viewport_rid: RID = self._server.viewport_allocate()

        self._world_2d: Optional[World2D] = World2D()
        canvas_rid = self._world_2d.get_canvas()

        Logger.info(f"Viewport '{name}' created World2D. Canvas RID: {canvas_rid}", "Viewport")

        self._server.viewport_attach_canvas(
            self._viewport_rid, canvas_rid
        )

        self.size = Vector2(800, 600)
        self._server.viewport_set_size(self._viewport_rid, 800, 600)
        self._transparent_bg = False
        self._global_canvas_transform = Transform2D.identity()

        self._gui_focus_owner: Optional["Control"] = None
        self._gui_mouse_focus: Optional["Control"] = None
        self._gui_drag_data: Any = None

        self.gui_focus_changed = Signal("gui_focus_changed")

    def push_input(self, event: pygame.event.Event):
        if not self.is_inside_tree():
            return

        self._propagate_input(self, event)
        if hasattr(event, "accepted") and event.accepted:
            return

        self._gui_input_propagation(event)
        pass

    def _propagate_input(self, node: Node, event: pygame.event.Event):
        if hasattr(node, "_input"):
            node._input(event)

        for child in node.children:
            self._propagate_input(child, event)

    def _gui_input_propagation(self, event: pygame.event.Event) -> bool:
        """
        Orchestrates the GUI input logic.
        """
        if event.type in (pygame.KEYDOWN, pygame.KEYUP):
            if self._gui_focus_owner:
                self._gui_focus_owner._gui_input(event)
                if self._gui_focus_owner._event_accepted:
                    self._gui_focus_owner._event_accepted = False
                    return True
            return False

        if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            mouse_pos = Vector2(event.pos[0], event.pos[1])
            return self._gui_find_control(self, mouse_pos, event)

        return False

    def _gui_find_control(self, node: Node, mouse_pos: Vector2, event: pygame.event.Event) -> bool:
        """
        Recursive Post-Order traversal to find the top-most control.
        """
        for i in range(len(node.children) - 1, -1, -1):
            child = node.children[i]
            if child.is_queued_for_deletion():
                continue

            if self._gui_find_control(child, mouse_pos, event):
                return True

        from engine.ui.control import Control

        if isinstance(node, Control) and node.visible:
            if node.mouse_filter == MouseFilter.IGNORE:
                return False

            if node.has_point(mouse_pos):
                local_event = node.make_input_local(event)
                node._gui_input(local_event)
                if node._event_accepted:
                    node._event_accepted = False
                    return True

                if node.mouse_filter == MouseFilter.STOP:
                    return True

        return False

    def get_class(self) -> str:
        return "Viewport"

    def get_viewport_rid(self) -> RID:
        return self._viewport_rid

    @property
    def world_2d(self) -> Optional[World2D]:
        return self._world_2d

    @world_2d.setter
    def world_2d(self, value: World2D):
        if self._world_2d == value:
            return

        if self._world_2d:
            self._server.viewport_remove_canvas(
                self._viewport_rid, self._world_2d.get_canvas()
            )

        self._world_2d = value
        if self._world_2d:
            canvas_rid = self._world_2d.get_canvas()
            Logger.info(f"Viewport '{self.name}' switched World2D. New Canvas RID: {canvas_rid}", "Viewport")
            self._server.viewport_attach_canvas(
                self._viewport_rid, canvas_rid
            )

    def find_world_2d(self) -> Optional[World2D]:
        if self._world_2d:
            return self._world_2d
        if self.parent:
            vp = self.parent.get_viewport()
            if vp:
                return vp.find_world_2d()
        return None

    def get_canvas(self) -> RID:
        """Returns the default World 2D canvas."""
        if self._world_2d:
            return self._world_2d.get_canvas()
        return RID()

    def set_size(self, width: int, height: int):
        self.size = Vector2(width, height)
        self._server.viewport_set_size(self._viewport_rid, width, height)

    def _enter_tree(self):
        super()._enter_tree()
        self._server.viewport_set_active(self._viewport_rid, True)

    def _exit_tree(self):
        self._server.viewport_set_active(self._viewport_rid, False)
        super()._exit_tree()

    @property
    def transparent_bg(self) -> bool:
        return self._transparent_bg

    @transparent_bg.setter
    def transparent_bg(self, value: bool):
        self._transparent_bg = value
        self._server.viewport_set_transparent_background(self._viewport_rid, value)

    @property
    def canvas_transform(self) -> Transform2D:
        return self._global_canvas_transform

    @canvas_transform.setter
    def canvas_transform(self, value: Transform2D):
        self._global_canvas_transform = value
        self._server.viewport_set_global_canvas_transform(self._viewport_rid, value)

    def gui_get_focus_owner(self) -> Optional["Control"]:
        return self._gui_focus_owner

    def gui_set_focus(self, control: Optional["Control"]):
        if self._gui_focus_owner == control:
            return

        if self._gui_focus_owner:
            self._gui_focus_owner.notification(44)
            self._gui_focus_owner.queue_redraw()

        self._gui_focus_owner = control

        if self._gui_focus_owner:
            self._gui_focus_owner.notification(43)
            self._gui_focus_owner.queue_redraw()

        self.gui_focus_changed.emit(control)

    def gui_release_focus(self):
        self.gui_set_focus(None)

    def gui_get_drag_data(self) -> Any:
        return self._gui_drag_data

    def gui_set_drag_data(self, data: Any, control: "Control", preview: Optional["Control"]):
        self._gui_drag_data = {
            "data": data,
            "source": control,
            "preview": preview
        }

    def find_next_focus(self, current_focus: "Control", side: int) -> Optional["Control"]:
        return None
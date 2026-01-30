from engine.scene.main.node import Node
from engine.servers.rendering.rendering_server import RenderingServer
from engine.core.rid import RID
from engine.math.datatypes.transform2d import Transform2D
from engine.math.datatypes.vector2 import Vector2
from engine.math import affine


class CanvasLayer(Node):
    """
    A Node that creates a separate 2D rendering layer (Canvas).
    """

    def __init__(self, name: str = "CanvasLayer"):
        super().__init__(name)
        self._server = RenderingServer.get_singleton()
        self._canvas_rid: RID = self._server.canvas_allocate()
        self._server.canvas_initialize(self._canvas_rid)

        self.layer: int = 1
        self.offset: Vector2 = Vector2(0, 0)
        self.rotation: float = 0.0
        self.scale: Vector2 = Vector2(1, 1)
        self.transform: Transform2D = Transform2D.identity()

    def get_canvas(self) -> RID:
        return self._canvas_rid

    def get_class(self) -> str:
        return "CanvasLayer"

    def _enter_tree(self):
        super()._enter_tree()
        vp = self.get_viewport()
        if vp:
            vp_rid = vp.get_viewport_rid()
            self._server.viewport_attach_canvas(vp_rid, self._canvas_rid)
            self._server.viewport_set_canvas_stacking(
                vp_rid, self._canvas_rid, self.layer, 0
            )
            self._update_transform()

    def _exit_tree(self):
        vp = self.get_viewport()
        if vp:
            vp_rid = vp.get_viewport_rid()
            self._server.viewport_remove_canvas(vp_rid, self._canvas_rid)
        super()._exit_tree()

    def _update_transform(self):
        t_mat = affine.get_translation(self.offset.x, self.offset.y)
        r_mat = affine.get_rotation(self.rotation)
        s_mat = affine.get_scale(self.scale.x, self.scale.y)
        self.transform = t_mat @ (r_mat @ s_mat)

        vp = self.get_viewport()
        if vp:
            self._server.viewport_set_canvas_transform(
                vp.get_viewport_rid(), self._canvas_rid, self.transform
            )

    def set_layer(self, layer: int):
        self.layer = layer
        vp = self.get_viewport()
        if vp:
            self._server.viewport_set_canvas_stacking(
                vp.get_viewport_rid(), self._canvas_rid, self.layer, 0
            )

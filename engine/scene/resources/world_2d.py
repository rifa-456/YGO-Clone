from engine.core.resource import Resource
from engine.servers.rendering.rendering_server import RenderingServer
from engine.core.rid import RID


class World2D(Resource):
    """
    Class that has everything related to a 2D world:
    - Physics space (TODO)
    - Canvas (The rendering layer where CanvasItems are drawn)
    """

    def __init__(self):
        super().__init__()
        self._server = RenderingServer.get_singleton()
        self._canvas: RID = self._server.canvas_allocate()
        self._space: RID = RID()

    @property
    def canvas(self) -> RID:
        return self._canvas

    @property
    def space(self) -> RID:
        return self._space

    def get_canvas(self) -> RID:
        return self._canvas

    def get_space(self) -> RID:
        return self._space

from typing import Optional
from engine.core.rid import RID
from engine.servers.rendering.renderer_storage import RendererStorage
from engine.servers.rendering.viewport.renderer_viewport import RendererViewport
from engine.servers.rendering.canvas.renderer_canvas_cull import RendererCanvasCull
from engine.servers.rendering.canvas.renderer_canvas_render import RendererCanvasRender
from engine.servers.rasterizer.rasterizer_canvas import RasterizerCanvas


class RenderingServer(RendererStorage, RendererCanvasCull, RendererViewport):
    _instance: Optional["RenderingServer"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RenderingServer, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        RendererStorage.__init__(self)
        RendererCanvasCull.__init__(self)
        RendererViewport.__init__(self)

        self.storage = self
        self.viewport = self
        self.canvas_cull = self

        self.canvas_render = RendererCanvasRender.get_singleton()
        self.rasterizer = RasterizerCanvas.get_singleton()

        self._main_viewport: Optional[RID] = None
        self._frame_count: int = 0
        self._time: float = 0.0
        self._initialized = True

    @staticmethod
    def get_singleton() -> "RenderingServer":
        if RenderingServer._instance is None:
            RenderingServer()
        return RenderingServer._instance

    def free_rid(self, rid: RID) -> None:
        """
        Free any RID resource.
        Calls specific mixin implementations.
        """
        RendererStorage.free_rid(self, rid)
        RendererCanvasCull.free_rid(self, rid)
        RendererViewport.free_rid(self, rid)

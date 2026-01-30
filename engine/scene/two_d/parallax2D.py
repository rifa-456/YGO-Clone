from typing import Optional
from engine.scene.node2D import Node2D
from engine.scene.camera2D import Camera2D
from engine.math.vector2 import Vector2


class Parallax2D(Node2D):
    """
    A 2D Node that moves visually to create a parallax effect.
    """

    def __init__(self, name: str = "Parallax2D"):
        super().__init__(name)
        self.scroll_scale: Vector2 = Vector2(1.0, 1.0)
        self.scroll_offset: Vector2 = Vector2(0, 0)
        self.repeat_size: Vector2 = Vector2(0, 0)
        self.repeat_times: int = 1
        self.ignore_camera_scroll: bool = False
        self.limit_begin: Vector2 = Vector2(0, 0)
        self.limit_end: Vector2 = Vector2(0, 0)
        self._last_camera_pos: Vector2 = Vector2(0, 0)

    def _process(self, delta: float):
        if self.ignore_camera_scroll:
            return

        camera = self._get_active_camera()
        if not camera:
            return

        camera_pos = camera.get_global_position()
        ofs = (camera_pos * (Vector2(1, 1) - self.scroll_scale)) + self.scroll_offset
        if self.repeat_size.x > 0:
            ofs.x = ofs.x % self.repeat_size.x
            pass

        if self.repeat_size.y > 0:
            ofs.y = ofs.y % self.repeat_size.y

        self.position = ofs

    def _get_active_camera(self) -> Optional[Camera2D]:
        if self.tree and self.tree.current_camera:
            return self.tree.current_camera
        return None

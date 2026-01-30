from engine.math.datatypes.vector2 import Vector2
from engine.math.datatypes.transform2d import Transform2D
from engine.scene.two_d.canvas_item import CanvasItem


class Node2D(CanvasItem):
    """
    A 2D node that has a transform (position, rotation, scale).
    """

    def __init__(self, name: str = "Node2D"):
        super().__init__(name)
        self._position = Vector2()
        self._rotation = 0.0
        self._scale = Vector2(1, 1)
        self._transform_dirty = True

    @property
    def position(self) -> Vector2:
        return self._position

    @position.setter
    def position(self, value: Vector2):
        self._position = value
        self._update_transform()

    @property
    def rotation(self) -> float:
        return self._rotation

    @rotation.setter
    def rotation(self, value: float):
        self._rotation = value
        self._update_transform()

    @property
    def scale(self) -> Vector2:
        return self._scale

    @scale.setter
    def scale(self, value: Vector2):
        self._scale = value
        self._update_transform()

    def _update_transform(self):
        t = Transform2D(self._rotation, self._position)
        t = t.scaled(self._scale)

        self._rendering_server.canvas_item_set_transform(self.get_rid(), t)

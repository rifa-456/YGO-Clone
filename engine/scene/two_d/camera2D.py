from engine.scene.two_d.node2D import Node2D
from engine.math.datatypes.transform2d import Transform2D


class Camera2D(Node2D):
    """
    A Node2D that acts as the viewpoint for the scene.
    """

    def __init__(self, name: str = "Camera2D"):
        super().__init__(name)

    def get_view_matrix(self) -> Transform2D:
        """
        Calculates the View Matrix.
        """
        global_t = self.global_transform
        return global_t.inverse()

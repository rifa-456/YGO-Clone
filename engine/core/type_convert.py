from typing import Any
from engine.math.transform2D import Transform2D
from engine.math.vector2 import Vector2


class TypeConvert:
    @staticmethod
    def to_vector2(val: Any) -> Vector2:
        if isinstance(val, Vector2):
            return val
        if isinstance(val, (list, tuple)) and len(val) >= 2:
            return Vector2(val[0], val[1])
        raise TypeError(f"Cannot convert {type(val)} to Vector2")

    @staticmethod
    def to_transform2d(val: Any) -> Transform2D:
        if isinstance(val, Transform2D):
            return val
        raise TypeError(f"Cannot convert {type(val)} to Transform2D")

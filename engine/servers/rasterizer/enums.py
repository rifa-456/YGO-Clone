from enum import IntEnum


class BlendMode(IntEnum):
    """Blend modes for compositing"""

    BLEND_MODE_MIX = 0
    BLEND_MODE_ADD = 1
    BLEND_MODE_SUB = 2
    BLEND_MODE_MUL = 3
    BLEND_MODE_PREMULT_ALPHA = 4
    BLEND_MODE_DISABLED = 5


class PrimitiveType(IntEnum):
    """Primitive drawing datatypes"""

    PRIMITIVE_POINTS = 0
    PRIMITIVE_LINES = 1
    PRIMITIVE_LINE_STRIP = 2
    PRIMITIVE_TRIANGLES = 3
    PRIMITIVE_TRIANGLE_STRIP = 4
    PRIMITIVE_TRIANGLE_FAN = 5

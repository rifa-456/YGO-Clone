from enum import IntEnum


class CanvasBlendMode(IntEnum):
    """Blend modes for canvas rendering"""

    BLEND_MODE_MIX = 0
    BLEND_MODE_ADD = 1
    BLEND_MODE_SUB = 2
    BLEND_MODE_MUL = 3
    BLEND_MODE_PREMULT_ALPHA = 4
    BLEND_MODE_DISABLED = 5


class CanvasItemLightMode(IntEnum):
    """
    Lighting mode for specific canvas items.
    Distinguished from CanvasLightMode (Point/Directional) in enums.py.
    """

    LIGHT_MODE_NORMAL = 0
    LIGHT_MODE_UNSHADED = 1
    LIGHT_MODE_LIGHT_ONLY = 2

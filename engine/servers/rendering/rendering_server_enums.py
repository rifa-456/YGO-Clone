from enum import IntEnum


class TextureType(IntEnum):
    TYPE_2D = 0
    TYPE_LAYERED = 1


class BlendMode(IntEnum):
    MIX = 0
    ADD = 1
    SUB = 2
    MUL = 3

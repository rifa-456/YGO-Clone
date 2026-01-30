from enum import IntEnum


class LayoutPreset(IntEnum):
    TOP_LEFT = 0
    TOP_RIGHT = 1
    BOTTOM_LEFT = 2
    BOTTOM_RIGHT = 3
    CENTER = 4
    FULL_RECT = 5
    TOP_WIDE = 6
    BOTTOM_WIDE = 7
    LEFT_WIDE = 8
    RIGHT_WIDE = 9


class SizeFlag(IntEnum):
    SHRINK_BEGIN = 0
    SHRINK_END = 1
    SHRINK_CENTER = 2
    EXPAND = 4
    FILL = 8
    EXPAND_FILL = 12


class MouseFilter(IntEnum):
    """
    Controls how the control handles mouse input.
    """

    STOP = 0
    PASS = 1
    IGNORE = 2


class FocusMode(IntEnum):
    """
    Controls how the control handles focus.
    """

    NONE = 0
    CLICK = 1
    ALL = 2


class CursorShape(IntEnum):
    ARROW = 0
    IBEAM = 1
    POINTING_HAND = 2
    CROSS = 3
    WAIT = 4
    BUSY = 5
    DRAG = 6
    CAN_DROP = 7
    FORBIDDEN = 8
    VSIZE = 9
    HSIZE = 10
    BDIAGSIZE = 11
    FDIAGSIZE = 12
    MOVE = 13
    VSPLIT = 14
    HSPLIT = 15
    HELP = 16


class GrowDirection(IntEnum):
    BEGIN = 0
    END = 1
    BOTH = 2


class ScrollMode(IntEnum):
    DISABLED = 0
    AUTO = 1
    ALWAYS = 2
    SHOW_NEVER = 3


class Side(IntEnum):
    LEFT = 0
    TOP = 1
    RIGHT = 2
    BOTTOM = 3


class HorizontalAlignment(IntEnum):
    LEFT = 0
    CENTER = 1
    RIGHT = 2
    FILL = 3


class VerticalAlignment(IntEnum):
    TOP = 0
    CENTER = 1
    BOTTOM = 2
    FILL = 3
from enum import IntEnum


class ViewportUpdateMode(IntEnum):
    UPDATE_DISABLED = 0
    UPDATE_ONCE = 1
    UPDATE_WHEN_VISIBLE = 2
    UPDATE_WHEN_PARENT_VISIBLE = 3
    UPDATE_ALWAYS = 4


class ViewportClearMode(IntEnum):
    CLEAR_MODE_ALWAYS = 0
    CLEAR_MODE_NEVER = 1
    CLEAR_MODE_ONLY_NEXT_FRAME = 2


class ViewportMSAA(IntEnum):
    MSAA_DISABLED = 0
    MSAA_2X = 1
    MSAA_4X = 2
    MSAA_8X = 3


class ViewportScreenSpaceAA(IntEnum):
    SCREEN_SPACE_AA_DISABLED = 0
    SCREEN_SPACE_AA_FXAA = 1


class ViewportRenderInfo(IntEnum):
    RENDER_INFO_OBJECTS_IN_FRAME = 0
    RENDER_INFO_PRIMITIVES_IN_FRAME = 1
    RENDER_INFO_DRAW_CALLS_IN_FRAME = 2


class ViewportDebugDraw(IntEnum):
    DEBUG_DRAW_DISABLED = 0
    DEBUG_DRAW_UNSHADED = 1
    DEBUG_DRAW_LIGHTING = 2
    DEBUG_DRAW_OVERDRAW = 3
    DEBUG_DRAW_WIREFRAME = 4

from typing import Optional, Dict, List
from dataclasses import dataclass, field
import pygame
from engine.core.rid import RID
from engine.math.datatypes.vector2 import Vector2
from engine.math.datatypes.transform2d import Transform2D
from engine.math.datatypes.color import Color
from engine.math.datatypes.rect2 import Rect2
from engine.servers.rendering.viewport.enums import (
    ViewportUpdateMode,
    ViewportClearMode,
    ViewportMSAA,
    ViewportScreenSpaceAA,
    ViewportDebugDraw,
)
from engine.servers.rendering.viewport.canvas_attachment import CanvasAttachment


@dataclass
class ViewportData:
    """
    Internal storage for a Viewport.
    """

    rid: RID

    size: Vector2 = field(default_factory=lambda: Vector2(800, 600))
    rect: Rect2 = field(default_factory=lambda: Rect2(0, 0, 800, 600))
    global_transform: Transform2D = field(default_factory=Transform2D.identity)
    canvas_transform: Transform2D = field(default_factory=Transform2D.identity)

    visible: bool = True
    parent: Optional[RID] = None

    update_mode: ViewportUpdateMode = ViewportUpdateMode.UPDATE_WHEN_VISIBLE
    clear_mode: ViewportClearMode = ViewportClearMode.CLEAR_MODE_ALWAYS
    clear_color: Color = field(default_factory=lambda: Color(0, 0, 0, 1))
    transparent_bg: bool = False
    disable_2d: bool = False

    msaa: ViewportMSAA = ViewportMSAA.MSAA_DISABLED
    screen_space_aa: ViewportScreenSpaceAA = (
        ViewportScreenSpaceAA.SCREEN_SPACE_AA_DISABLED
    )
    use_debanding: bool = False

    debug_draw: ViewportDebugDraw = ViewportDebugDraw.DEBUG_DRAW_DISABLED

    use_xr: bool = False
    screen_attachment: bool = False

    render_target: Optional[pygame.Surface] = None
    render_target_texture: Optional[RID] = None

    canvas_map: Dict[RID, CanvasAttachment] = field(default_factory=dict)
    canvas_list: List[CanvasAttachment] = field(default_factory=list)

    render_info: Dict[int, int] = field(default_factory=dict)
    time: float = 0.0
    needs_update: bool = True
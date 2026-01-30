from typing import Optional, List
from dataclasses import dataclass, field
from engine.core.rid import RID
from engine.math.datatypes.vector2 import Vector2
from engine.math.datatypes.transform2d import Transform2D
from engine.math.datatypes.color import Color
from engine.math.datatypes.rect2 import Rect2

from .render_enums import CanvasBlendMode, CanvasItemLightMode


@dataclass
class RenderState:
    """
    Current rendering state used by RendererCanvasRender.
    Tracks active blend mode, clipping, etc.
    """

    # Transform stack
    transform: Transform2D = field(default_factory=Transform2D.identity)

    blend_mode: CanvasBlendMode = CanvasBlendMode.BLEND_MODE_MIX

    clip_rect: Optional[Rect2] = None
    clip_enabled: bool = False

    modulate: Color = field(default_factory=lambda: Color(1, 1, 1, 1))

    light_mode: CanvasItemLightMode = CanvasItemLightMode.LIGHT_MODE_NORMAL

    texture_filter: int = 1
    texture_repeat: int = 0


@dataclass
class BatchData:
    """
    Data for a single draw batch.
    Batching combines multiple draw calls into one to minimize state changes.
    """

    vertices: List[Vector2] = field(default_factory=list)
    colors: List[Color] = field(default_factory=list)
    uvs: List[Vector2] = field(default_factory=list)
    indices: List[int] = field(default_factory=list)

    texture: Optional[RID] = None

    blend_mode: CanvasBlendMode = CanvasBlendMode.BLEND_MODE_MIX

    clip_rect: Optional[Rect2] = None

    primitive_type: int = 3

    def clear(self):
        self.vertices.clear()
        self.colors.clear()
        self.uvs.clear()
        self.indices.clear()

    def is_empty(self) -> bool:
        return len(self.vertices) == 0

    def can_batch_with(
        self,
        texture: Optional[RID],
        blend: CanvasBlendMode,
        clip: Optional[Rect2],
    ) -> bool:
        """Check if we can add more geometry to this batch"""
        return (
            self.texture == texture
            and self.blend_mode == blend
            and self.clip_rect == clip
        )
from typing import Optional, Dict, List, Set
from dataclasses import dataclass, field

from engine.core.rid import RID
from engine.math.datatypes.vector2 import Vector2
from engine.math.datatypes.transform2d import Transform2D
from engine.math.datatypes.color import Color
from engine.math.datatypes.rect2 import Rect2

from .enums import (
    CanvasItemTextureFilter,
    CanvasItemTextureRepeat,
    CanvasLightMode,
    CanvasLightBlendMode,
)
from .commands import Command


@dataclass
class Item:
    rid: RID = field(default_factory=RID)

    # Hierarchy
    parent: Optional["Item"] = None
    parent_rid: Optional[RID] = None
    children: List["Item"] = field(default_factory=list)

    # Transform
    transform: Transform2D = field(default_factory=Transform2D.identity)
    global_transform: Transform2D = field(default_factory=Transform2D.identity)

    # Visibility
    visible: bool = True
    visible_in_tree: bool = True

    # Z-ordering
    z_index: int = 0
    z_relative: bool = True
    sort_y: bool = False

    # Visuals
    modulate: Color = field(default_factory=lambda: Color(1, 1, 1, 1))
    self_modulate: Color = field(default_factory=lambda: Color(1, 1, 1, 1))
    final_modulate: Color = field(default_factory=lambda: Color(1, 1, 1, 1))

    material: Optional[RID] = None
    use_parent_material: bool = False

    texture_filter: CanvasItemTextureFilter = (
        CanvasItemTextureFilter.TEXTURE_FILTER_PARENT_NODE
    )
    texture_repeat: CanvasItemTextureRepeat = (
        CanvasItemTextureRepeat.TEXTURE_REPEAT_PARENT_NODE
    )

    commands: List[Command] = field(default_factory=list)

    # Organization
    canvas_layer: Optional["CanvasLayer"] = None
    clip: bool = False

    # Culling internals
    rect_dirty: bool = True
    rect: Rect2 = field(default_factory=lambda: Rect2(Vector2(0, 0), Vector2(0, 0)))
    index: int = 0
    behind: bool = False
    copy_back_buffer: Optional[Rect2] = None


@dataclass
class CanvasLayer:
    rid: RID = field(default_factory=RID)
    layer: int = 0
    transform: Transform2D = field(default_factory=Transform2D.identity)
    offset: Vector2 = field(default_factory=lambda: Vector2(0, 0))
    rotation: float = 0.0
    scale: Vector2 = field(default_factory=lambda: Vector2(1, 1))
    items: Set[RID] = field(default_factory=set)
    follow_viewport: bool = False
    follow_viewport_scale: float = 1.0


@dataclass
class Canvas:
    rid: RID = field(default_factory=RID)
    transform: Transform2D = field(default_factory=Transform2D.identity)
    root_items: Set[RID] = field(default_factory=set)
    layers: Dict[int, CanvasLayer] = field(default_factory=dict)
    items: Set[RID] = field(default_factory=set)


@dataclass
class CanvasLight:
    rid: RID = field(default_factory=RID)
    transform: Transform2D = field(default_factory=Transform2D.identity)
    enabled: bool = True
    color: Color = field(default_factory=lambda: Color(1, 1, 1, 1))
    energy: float = 1.0
    mode: CanvasLightMode = CanvasLightMode.LIGHT_MODE_POINT
    texture: Optional[RID] = None
    texture_offset: Vector2 = field(default_factory=lambda: Vector2(0, 0))
    texture_scale: float = 1.0
    height: float = 0.0
    blend_mode: CanvasLightBlendMode = CanvasLightBlendMode.LIGHT_BLEND_MODE_ADD
    canvas: Optional[RID] = None

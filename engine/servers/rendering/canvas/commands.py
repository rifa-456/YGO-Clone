from typing import Optional, List, Tuple
from dataclasses import dataclass, field

from engine.core.rid import RID
from engine.math.datatypes.vector2 import Vector2
from engine.math.datatypes.rect2 import Rect2
from engine.math.datatypes.color import Color


@dataclass
class Command:
    pass


@dataclass
class CommandRect(Command):
    rect: Rect2 = field(default_factory=lambda: Rect2(Vector2(0, 0), Vector2(0, 0)))
    modulate: Color = field(default_factory=lambda: Color(1, 1, 1, 1))
    tile: bool = False


@dataclass
class CommandNinePatch(Command):
    rect: Rect2 = field(default_factory=lambda: Rect2(Vector2(0, 0), Vector2(0, 0)))
    source: Rect2 = field(default_factory=lambda: Rect2(Vector2(0, 0), Vector2(0, 0)))
    texture: Optional[RID] = None
    margins: Tuple[float, float, float, float] = (0, 0, 0, 0)
    draw_center: bool = True
    modulate: Color = field(default_factory=lambda: Color(1, 1, 1, 1))


@dataclass
class CommandPrimitive(Command):
    points: List[Vector2] = field(default_factory=list)
    colors: List[Color] = field(default_factory=list)
    uvs: List[Vector2] = field(default_factory=list)
    texture: Optional[RID] = None
    primitive_type: int = 3


@dataclass
class CommandPolygon(Command):
    points: List[Vector2] = field(default_factory=list)
    colors: List[Color] = field(default_factory=list)
    uvs: List[Vector2] = field(default_factory=list)
    indices: List[int] = field(default_factory=list)
    texture: Optional[RID] = None
    antialiased: bool = False


@dataclass
class CommandClipIgnore(Command):
    ignore: bool = True

@dataclass
class CommandPolyline(Command):
    points: List[Vector2] = field(default_factory=list)
    colors: List[Color] = field(default_factory=list)
    width: float = 1.0
    antialiased: bool = False

@dataclass
class CommandCircle(Command):
    position: Vector2 = field(default_factory=lambda: Vector2(0, 0))
    radius: Vector2 = field(default_factory=lambda: Vector2(0, 0))
    color: Color = field(default_factory=lambda: Color(1, 1, 1, 1))
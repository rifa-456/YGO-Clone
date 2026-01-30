from dataclasses import field, dataclass
from engine.core.rid import RID
from engine.math.datatypes.transform2d import Transform2D


@dataclass
class CanvasAttachment:
    canvas: RID
    layer: int = 0
    sublayer: int = 0
    transform: Transform2D = field(default_factory=Transform2D.identity)

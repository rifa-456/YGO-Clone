from typing import Union, Optional
from engine.scene.two_d.node2D import Node2D
from engine.core.textures.texture import Texture
from engine.math.datatypes.rect2 import Rect2
from engine.math.datatypes.vector2 import Vector2
from game.autoload.texture_registry import TextureRegistry


class Sprite2D(Node2D):
    """
    A specific VisualNode that renders a texture.
    Acts as a component.
    """

    def __init__(
            self,
            texture: Union[str, Texture],
            name: str = "Sprite"
    ):
        super().__init__(name)
        self._texture: Optional[Texture] = None

        # Resolve texture immediately
        if isinstance(texture, str):
            self.set_texture_path(texture)
        else:
            self._texture = texture

        self.centered: bool = True
        self.offset: Vector2 = Vector2(0, 0)

    def set_texture(self, texture: Texture) -> None:
        self._texture = texture
        self.queue_redraw()

    def set_texture_path(self, path: str) -> None:
        """
        Sets the texture via path lookup from the Registry.
        """
        self._texture = TextureRegistry.get(path)
        self.queue_redraw()

    def get_texture(self) -> Optional[Texture]:
        return self._texture

    def _draw(self):
        """
        Renders the texture using CanvasItem API.
        """
        if not self._texture:
            return

        tex_w = self._texture.get_width()
        tex_h = self._texture.get_height()

        dest_pos = Vector2(0, 0)

        if self.centered:
            dest_pos = Vector2(-tex_w / 2, -tex_h / 2)

        dest_pos += self.offset

        rect = Rect2(dest_pos.x, dest_pos.y, float(tex_w), float(tex_h))

        self.draw_texture_rect(self._texture, rect)
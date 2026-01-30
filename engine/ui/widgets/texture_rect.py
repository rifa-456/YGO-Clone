from typing import Optional

from engine.core.textures import Texture2D
from engine.ui.control import Control
from engine.math.datatypes.vector2 import Vector2
from engine.math.datatypes.rect2 import Rect2


class TextureRect(Control):
    """
    Control for drawing textures.
    """

    def __init__(self, texture: Optional[Texture2D] = None, name: str = "TextureRect"):
        super().__init__(name)
        self._texture: Optional[Texture2D] = texture
        self._stretch_mode: bool = False
        self._expand_mode: bool = False

    @property
    def texture(self) -> Optional[Texture2D]:
        return self._texture

    @texture.setter
    def texture(self, value: Optional[Texture2D]):
        if self._texture != value:
            self._texture = value
            self.minimum_size_changed()
            self.queue_sort()
            self.queue_redraw()

    @property
    def stretch_mode(self) -> bool:
        """
        If True, the texture scales to fit the control's size.
        If False, the texture is drawn at its native resolution (centered).
        """
        return self._stretch_mode

    @stretch_mode.setter
    def stretch_mode(self, value: bool):
        if self._stretch_mode != value:
            self._stretch_mode = value
            self.queue_sort()
            self.queue_redraw()

    @property
    def expand_mode(self) -> bool:
        """
        If True, the control's minimum size is (0,0), allowing it to shrink
        smaller than the texture.
        """
        return self._expand_mode

    @expand_mode.setter
    def expand_mode(self, value: bool):
        if self._expand_mode != value:
            self._expand_mode = value
            self.minimum_size_changed()
            self.queue_sort()
            self.queue_redraw()

    STRETCH_SCALE_ON_EXPAND = True
    STRETCH_KEEP_ASPECT_CENTERED = False

    def get_minimum_size(self) -> Vector2:
        """
        If expand_mode is True, min size is (0,0).
        If False, min size is the texture size.
        """
        if self._expand_mode:
            return Vector2(0, 0)

        if self._texture:
            return Vector2(
                float(self._texture.get_width()), float(self._texture.get_height())
            )

        return Vector2(0, 0)

    def on_resized(self):
        """
        Triggers a redraw when the control's size changes.
        """
        super().on_resized()
        self.queue_redraw()

    def _draw(self):
        """
        Draws the texture using CanvasItem's optimized routines.
        """
        if not self._texture:
            return

        tex_w = float(self._texture.get_width())
        tex_h = float(self._texture.get_height())

        dest_rect: Rect2

        if self._expand_mode:
            size = self.get_size()
            if self._stretch_mode:
                dest_rect = Rect2(0, 0, size.x, size.y)
            else:
                x = (size.x - tex_w) * 0.5
                y = (size.y - tex_h) * 0.5
                dest_rect = Rect2(x, y, tex_w, tex_h)
        else:
            dest_rect = Rect2(0, 0, tex_w, tex_h)

        self.draw_texture_rect(self._texture, dest_rect, tile=False)
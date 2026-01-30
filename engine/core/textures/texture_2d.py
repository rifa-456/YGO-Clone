from abc import ABC, abstractmethod
from typing import Tuple
import pygame
from engine.core.textures.texture import Texture


class Texture2D(Texture, ABC):
    """
    Abstract base class for 2D textures.
    """

    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def get_width(self) -> int:
        """Returns the texture width in pixels."""
        pass

    @abstractmethod
    def get_height(self) -> int:
        """Returns the texture height in pixels."""
        pass

    def get_size(self) -> Tuple[int, int]:
        """Returns the texture size (width, height) as a tuple."""
        return (self.get_width(), self.get_height())

    @abstractmethod
    def has_alpha(self) -> bool:
        """Returns True if the texture has an alpha channel."""
        pass

    @abstractmethod
    def get_data(self) -> pygame.Surface:
        """Returns the raw underlying surface (Internal API)."""
        pass

    def lock(self):
        """Prepares texture for reading. Returns pixel array."""
        return pygame.surfarray.pixels2d(self.get_data())

    def unlock(self):
        """Releases the pixel array."""
        pass

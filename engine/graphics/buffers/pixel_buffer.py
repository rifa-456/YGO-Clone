import pygame
import numpy as np
from typing import Optional

from engine.logger import Logger
from engine.graphics.formats import create_compatible_surface


class PixelBuffer:
    """
    A specific wrapper around a Pygame Surface that enforces direct pixel array manipulation.
    Acts as the 'Video Memory' for the software rasterizer.
    """

    def __init__(
            self, width: int, height: int, surface: Optional[pygame.Surface] = None
    ):
        if surface:
            self.surface = surface
            if self.surface.get_width() != width or self.surface.get_height() != height:
                raise ValueError(
                    "Provided surface dimensions do not match buffer dimensions."
                )
        else:
            self.surface = create_compatible_surface(width, height)

        self.width = width
        self.height = height
        self._pixels: Optional[np.ndarray] = None

    def lock(self) -> np.ndarray:
        """
        Locks the surface and returns a writeable 2D numpy view.
        Must be paired with unlock().
        """
        self.surface.lock()
        self._pixels = pygame.surfarray.pixels2d(self.surface)

        if self._pixels.shape != (self.width, self.height):
            Logger.warn(f"PixelBuffer lock mismatch! Expected {self.width}x{self.height}, got {self._pixels.shape}",
                        "PixelBuffer")

        return self._pixels

    def unlock(self) -> None:
        """
        Unlocks the surface, flushing changes.
        """
        if self._pixels is not None:
            del self._pixels
            self._pixels = None
        self.surface.unlock()

    def clear(self, color_int: int = 0) -> None:
        """
        Fast clear using fill.
        Handles the Pygame C-Long overflow issue for 32-bit colors.
        """
        if color_int > 2147483647:
            color_int -= 4294967296

        self.surface.fill(color_int)

    def map_color(self, r: int, g: int, b: int, a: int = 255) -> int:
        """
        Maps an RGBA tuple to the integer format of the underlying surface.
        Returns a Python int (unsigned 32-bit).
        """
        return int(self.surface.map_rgb((r, g, b, a))) & 0xFFFFFFFF
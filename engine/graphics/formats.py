"""
Central definition for Engine Pixel Formats.
Ensures compatibility between Pygame Surfaces and Cython Rasterizers.
"""
import pygame
from engine.logger import Logger

CYTHON_PIXEL_MASKS = (0x00FF0000, 0x0000FF00, 0x000000FF, 0xFF000000)

def log_format_details():
    Logger.info(f"--- FORMATS DIAGNOSTICS ---", "Formats")
    Logger.info(f"CYTHON_PIXEL_MASKS (R,G,B,A): {hex(CYTHON_PIXEL_MASKS[0])}, {hex(CYTHON_PIXEL_MASKS[1])}, {hex(CYTHON_PIXEL_MASKS[2])}, {hex(CYTHON_PIXEL_MASKS[3])}", "Formats")

def enforce_engine_format(surface: pygame.Surface) -> pygame.Surface:
    """
    Converts a surface to the strict format expected by the software rasterizer.
    """

    new_surf = pygame.Surface(
        surface.get_size(),
        flags=pygame.SRCALPHA,
        depth=32,
        masks=CYTHON_PIXEL_MASKS
    )
    new_surf.blit(surface, (0, 0))

    return new_surf


def create_compatible_surface(width: int, height: int) -> pygame.Surface:
    """
    Creates a blank surface compatible with the software rasterizer.
    """
    s = pygame.Surface(
        (width, height),
        flags=pygame.SRCALPHA,
        depth=32,
        masks=CYTHON_PIXEL_MASKS
    )
    m = s.get_masks()
    if m != CYTHON_PIXEL_MASKS:
         Logger.warn(f"create_compatible_surface MISMATCH! Requested {CYTHON_PIXEL_MASKS} but got {m}", "Formats")
    return s
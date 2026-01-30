import os
import pygame
from typing import List
from engine.core.resource import Resource
from engine.core.resource_format_loader import ResourceFormatLoader
from engine.core.textures.image_texture import ImageTexture


class ImageTextureFormatLoader(ResourceFormatLoader):
    """
    Resource format loader for ImageTexture.
    Handles loading image files from disk into ImageTexture resources.
    """

    def get_recognized_extensions(self) -> List[str]:
        return ["png", "jpg", "jpeg", "bmp"]

    def handles_type(self, type_name: str) -> bool:
        return type_name == "ImageTexture"

    def get_resource_type(self, path: str) -> str:
        return "ImageTexture"

    def load(self, path: str, original_path: str = "") -> Resource:
        surface = pygame.image.load(path).convert_alpha()
        texture = ImageTexture(surface)
        texture.resource_name = os.path.basename(path)
        return texture

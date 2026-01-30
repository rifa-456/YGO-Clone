from typing import Optional, Dict
from dataclasses import dataclass, field
import pygame
from engine.core.rid import RID
from engine.math.datatypes.vector2 import Vector2
from engine.servers.rendering.canvas.enums import (
    CanvasItemTextureFilter,
    CanvasItemTextureRepeat,
)
from engine.graphics.formats import enforce_engine_format, create_compatible_surface
from engine.logger import Logger  # Added Logger


@dataclass
class Texture:
    """
    Internal texture representation
    """

    rid: RID = field(default_factory=RID)
    surface: Optional[pygame.Surface] = None
    width: int = 0
    height: int = 0

    filter: CanvasItemTextureFilter = CanvasItemTextureFilter.TEXTURE_FILTER_LINEAR
    repeat: CanvasItemTextureRepeat = CanvasItemTextureRepeat.TEXTURE_REPEAT_DISABLED

    has_mipmaps: bool = False
    is_proxy: bool = False
    proxy_to: Optional[RID] = None

    path: str = ""

    def get_size(self) -> Vector2:
        return Vector2(self.width, self.height)


class RendererStorage:
    _instance: Optional["RendererStorage"] = None

    @staticmethod
    def get_singleton() -> "RendererStorage":
        if RendererStorage._instance is None:
            RendererStorage()
        return RendererStorage._instance

    def __init__(self):
        if RendererStorage._instance is None:
            RendererStorage._instance = self

        self._textures: Dict[RID, Texture] = {}
        self._default_texture: Optional[RID] = None
        self._default_material: Optional[RID] = None
        Logger.info("RendererStorage: Initialized.", "RendererStorage")

    def texture_allocate(self) -> RID:
        """Create a new texture resource"""
        rid = RID()
        self._textures[rid] = Texture(rid=rid)
        return rid

    def texture_2d_initialize(self, texture: RID, image: pygame.Surface) -> None:
        """Initialize texture with image data"""
        if texture not in self._textures:
            Logger.error(f"texture_2d_initialize: RID {texture} not found!", "RendererStorage")
            return

        tex = self._textures[texture]
        tex.surface = enforce_engine_format(image)
        tex.width = image.get_width()
        tex.height = image.get_height()

    def texture_set_image(self, texture: RID, image: pygame.Surface) -> None:
        """Update texture image data"""
        self.texture_2d_initialize(texture, image)

    def texture_get_size(self, texture: RID) -> Vector2:
        """Get texture dimensions"""
        if texture not in self._textures:
            return Vector2(0, 0)
        return self._textures[texture].get_size()

    def texture_get_native_handle(self, texture: RID) -> Optional[pygame.Surface]:
        """Get the underlying pygame surface"""
        if texture not in self._textures:
            return None
        return self._textures[texture].surface

    def texture_set_path(self, texture: RID, path: str) -> None:
        if texture in self._textures:
            self._textures[texture].path = path

    def texture_get_path(self, texture: RID) -> str:
        if texture not in self._textures:
            return ""
        return self._textures[texture].path

    def canvas_texture_allocate(self) -> RID:
        return self.texture_allocate()

    def canvas_texture_set_channel(
            self, canvas_texture: RID, channel: int, texture: RID
    ) -> None:
        if (
                channel == 0
                and canvas_texture in self._textures
                and texture in self._textures
        ):
            self._textures[canvas_texture].proxy_to = texture
            self._textures[canvas_texture].is_proxy = True

    def canvas_texture_set_texture_filter(
            self, canvas_texture: RID, filter: CanvasItemTextureFilter
    ) -> None:
        if canvas_texture in self._textures:
            self._textures[canvas_texture].filter = filter

    def canvas_texture_set_texture_repeat(
            self, canvas_texture: RID, repeat: CanvasItemTextureRepeat
    ) -> None:
        if canvas_texture in self._textures:
            self._textures[canvas_texture].repeat = repeat

    def free_rid(self, rid: RID) -> None:
        if rid in self._textures:
            del self._textures[rid]

    def get_resource_type(self, rid: RID) -> str:
        if rid in self._textures:
            return "Texture"
        return "Unknown"

    def get_default_texture(self) -> RID:
        if self._default_texture is None:
            self._default_texture = self.texture_allocate()
            surf = create_compatible_surface(1, 1)
            surf.fill((255, 255, 255))
            tex = self._textures[self._default_texture]
            tex.surface = surf
            tex.width = 1
            tex.height = 1
        return self._default_texture
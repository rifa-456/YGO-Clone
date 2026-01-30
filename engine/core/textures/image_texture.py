import pygame
from typing import Optional, Tuple
from engine.core.textures.texture_2d import Texture2D
from engine.core.rid import RID


class ImageTexture(Texture2D):
    """
    Concrete implementation of Texture2D.
    Acts as a client-side handle to a texture stored in the RenderingServer.
    """

    def __init__(self, surface: Optional[pygame.Surface] = None) -> None:
        super().__init__()

        from engine.servers.rendering.rendering_server import RenderingServer

        self._rendering_server = RenderingServer.get_singleton()

        self._rid = self._rendering_server.texture_allocate()

        self._width = 0
        self._height = 0

        if surface:
            self.set_image(surface)

    def set_image(self, surface: pygame.Surface) -> None:
        """
        Uploads the image data to the RenderingServer.
        """
        self._width = surface.get_width()
        self._height = surface.get_height()

        self._rendering_server.texture_2d_initialize(self._rid, surface)

    def get_width(self) -> int:
        return self._width

    def get_height(self) -> int:
        return self._height

    def get_rid(self) -> RID:
        return self._rid

    def has_alpha(self) -> bool:
        return True

    def get_data(self) -> pygame.Surface:
        """
        Retrieves the data back from the server.
        """
        return self._rendering_server.texture_get_native_handle(self._rid)

    def draw(
            self,
            canvas: pygame.Surface,
            position: Tuple[float, float],
            modulate: Tuple[int, int, int, int] = (255, 255, 255, 255),
    ) -> None:
        """
        Client-side fallback drawing.
        """
        surf = self.get_data()
        if not surf:
            return

        if modulate != (255, 255, 255, 255):
            temp_surf = surf.copy()
            temp_surf.fill(modulate, special_flags=pygame.BLEND_RGBA_MULT)
            canvas.blit(temp_surf, position)
        else:
            canvas.blit(surf, position)

    def draw_rect(
            self,
            canvas: pygame.Surface,
            dest_rect: Tuple[float, float, float, float],
            src_rect: Tuple[float, float, float, float] = None,
    ) -> None:
        """
        Client-side fallback drawing.
        """
        surf = self.get_data()
        if not surf:
            return

        if src_rect:
            canvas.blit(surf, dest_rect, area=src_rect)
        else:
            scaled = pygame.transform.scale(
                surf, (int(dest_rect[2]), int(dest_rect[3]))
            )
            canvas.blit(scaled, (dest_rect[0], dest_rect[1]))

    def _duplicate(self, subresources: bool) -> None:
        pass
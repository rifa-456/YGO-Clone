from typing import Optional, Dict
import pygame
# surfarray removed: We use blit for strict presentation compliance
from engine.core.rid import RID
from engine.math.datatypes.vector2 import Vector2
from engine.math.datatypes.transform2d import Transform2D
from engine.math.datatypes.color import Color
from engine.math.datatypes.rect2 import Rect2
from engine.servers.rendering.viewport.canvas_attachment import CanvasAttachment
from engine.servers.rendering.viewport.enums import (
    ViewportUpdateMode,
    ViewportRenderInfo,
    ViewportClearMode,
)
from engine.servers.rendering.viewport.viewport_data import ViewportData
from engine.logger import Logger
from engine.graphics.formats import create_compatible_surface


class RendererViewport:
    def __init__(self):
        self._viewports: Dict[RID, ViewportData] = {}
        self._display_window_surface: Optional[pygame.Surface] = None
        from engine.servers.rendering.canvas.renderer_canvas_render import (
            RendererCanvasRender,
        )

        self.canvas_render = RendererCanvasRender.get_singleton()

    def set_display_window(self, surface: pygame.Surface):
        self._display_window_surface = surface
        Logger.info("RendererViewport: Display Window Surface set.", "RendererViewport")

    def _get_vp(self, rid: RID) -> Optional[ViewportData]:
        return self._viewports.get(rid)

    @staticmethod
    def _create_render_target(vp: ViewportData):
        """
        Creates a backbuffer strictly compatible with the Engine's internal format
        (ARGB defined in formats.py).
        """
        w, h = int(vp.size.x), int(vp.size.y)
        if w <= 0 or h <= 0:
            Logger.warn(
                f"Viewport {vp.rid}: Size is invalid ({w}x{h}). Skipping render target creation.",
                "RendererViewport",
            )
            return

        vp.render_target = create_compatible_surface(w, h)
        vp.needs_update = True

    def viewport_allocate(self) -> RID:
        rid = RID()
        vp = ViewportData(rid=rid)
        self._viewports[rid] = vp
        self._create_render_target(vp)
        return rid

    def free_rid(self, rid: RID) -> None:
        if rid in self._viewports:
            vp = self._viewports[rid]
            if vp.render_target_texture:
                self.storage.free_rid(vp.render_target_texture)
            del self._viewports[rid]

    def viewport_attach_to_screen(
            self, viewport: RID, rect: Rect2 = Rect2(), screen_id: int = 0
    ) -> None:
        if vp := self._get_vp(viewport):
            Logger.info(
                f"Viewport {viewport} attached to screen. Rect: {rect}",
                "RendererViewport",
            )
            vp.screen_attachment = True
            vp.rect = rect
            vp.size = vp.rect.size
            self._create_render_target(vp)

    def viewport_set_size(self, viewport: RID, width: int, height: int) -> None:
        if vp := self._get_vp(viewport):
            if vp.size.x != width or vp.size.y != height:
                vp.size = Vector2(width, height)
                if not vp.screen_attachment:
                    vp.rect = Rect2(0, 0, width, height)
                self._create_render_target(vp)

    def viewport_set_active(self, viewport: RID, active: bool) -> None:
        if vp := self._get_vp(viewport):
            vp.visible = active
            Logger.info(
                f"Viewport {viewport} active state set to: {active}", "RendererViewport"
            )

    def viewport_set_parent_viewport(self, viewport: RID, parent: RID) -> None:
        if vp := self._get_vp(viewport):
            vp.parent = parent

    def viewport_set_clear_mode(self, viewport: RID, mode: ViewportClearMode) -> None:
        if vp := self._get_vp(viewport):
            vp.clear_mode = mode

    def viewport_set_update_mode(self, viewport: RID, mode: ViewportUpdateMode) -> None:
        if vp := self._get_vp(viewport):
            vp.update_mode = mode

    def viewport_set_clear_color(self, viewport: RID, color: Color) -> None:
        if vp := self._get_vp(viewport):
            vp.clear_color = color

    def viewport_set_transparent_background(self, viewport: RID, enabled: bool) -> None:
        if vp := self._get_vp(viewport):
            if vp.transparent_bg != enabled:
                vp.transparent_bg = enabled
                self._create_render_target(vp)

    def viewport_set_global_canvas_transform(
            self, viewport: RID, transform: Transform2D
    ) -> None:
        if vp := self._get_vp(viewport):
            vp.canvas_transform = transform
            vp.needs_update = True

    def viewport_attach_canvas(self, viewport: RID, canvas: RID) -> None:
        vp = self._get_vp(viewport)
        if vp and canvas not in vp.canvas_map:
            Logger.info(
                f"Attaching Canvas {canvas} to Viewport {viewport}", "RendererViewport"
            )
            vp.canvas_map[canvas] = CanvasAttachment(canvas)
            self._sort_canvas_list(vp)
            vp.needs_update = True

    def viewport_remove_canvas(self, viewport: RID, canvas: RID) -> None:
        vp = self._get_vp(viewport)
        if vp and canvas in vp.canvas_map:
            del vp.canvas_map[canvas]
            self._sort_canvas_list(vp)
            vp.needs_update = True

    def viewport_set_canvas_transform(
            self, viewport: RID, canvas: RID, transform: Transform2D
    ) -> None:
        vp = self._get_vp(viewport)
        if vp and canvas in vp.canvas_map:
            vp.canvas_map[canvas].transform = transform
            vp.needs_update = True

    def viewport_set_canvas_stacking(
            self, viewport: RID, canvas: RID, layer: int, sublayer: int
    ) -> None:
        vp = self._get_vp(viewport)
        if vp and canvas in vp.canvas_map:
            att = vp.canvas_map[canvas]
            att.layer = layer
            att.sublayer = sublayer
            self._sort_canvas_list(vp)
            vp.needs_update = True

    @staticmethod
    def _sort_canvas_list(vp: ViewportData) -> None:
        vp.canvas_list = sorted(
            vp.canvas_map.values(), key=lambda x: (x.layer, x.sublayer)
        )

    def viewport_get_texture(self, viewport: RID) -> RID:
        vp = self._get_vp(viewport)
        if not vp:
            return RID()

        if vp.render_target_texture is None:
            vp.render_target_texture = self.storage.texture_allocate()
            if vp.render_target:
                self.storage.texture_set_image(
                    vp.render_target_texture, vp.render_target
                )

        return vp.render_target_texture

    def viewport_draw(self, viewport: RID, delta: float) -> None:
        vp = self._get_vp(viewport)
        if not vp:
            Logger.error(
                f"Draw requested for non-existent Viewport {viewport}",
                "RendererViewport",
            )
            return

        if not self._should_update(vp):
            return

        target_surface = vp.render_target

        if not target_surface:
            self._create_render_target(vp)
            target_surface = vp.render_target
            if not target_surface:
                Logger.warn(
                    f"Viewport {viewport} has NO render target. Skipping draw.",
                    "RendererViewport",
                )
                return

        vp.time += delta
        self.canvas_render.set_target_surface(target_surface)
        self._clear_viewport(vp)

        if not vp.disable_2d:
            self.canvas_render.begin_frame()

            vp.render_info.clear()
            total_objects = 0

            for i, attachment in enumerate(vp.canvas_list):
                xform = vp.canvas_transform @ attachment.transform

                items = self.canvas_cull.cull_canvas(
                    attachment.canvas, xform, vp.rect
                )

                for item_ref, item_xform, item_z in items:
                    self.canvas_render.render_canvas_item(
                        item_xform, item_ref.commands, item_ref.final_modulate
                    )

                total_objects += len(items)

            self.canvas_render.end_frame()
            vp.render_info[ViewportRenderInfo.RENDER_INFO_OBJECTS_IN_FRAME] = (
                total_objects
            )

        if vp.render_target_texture and vp.render_target:
            self.storage.texture_set_image(vp.render_target_texture, vp.render_target)

        # 3. Present to OS Window (Screen Transfer)
        if vp.screen_attachment and self._display_window_surface:
            self._transfer_to_screen(target_surface, self._display_window_surface)

        if vp.clear_mode == ViewportClearMode.CLEAR_MODE_ONLY_NEXT_FRAME:
            vp.clear_mode = ViewportClearMode.CLEAR_MODE_NEVER

        vp.needs_update = False
        self.canvas_render.set_target_surface(None)

    def _transfer_to_screen(self, source: pygame.Surface, dest: pygame.Surface) -> None:
        """
        Transfers pixels from source (Backbuffer ARGB) to dest (OS Window).
        Using .blit() is strictly required here to handle the Pixel Format conversion
        (e.g., stripping Alpha channel for RGBX windows) which surfarray cannot do automatically.
        """
        try:
            # Simple Blit. This handles clipping and format conversion (Swizzling) internally.
            dest.blit(source, (0, 0))
        except Exception as e:
            Logger.error(f"Screen Transfer Failed: {e}", "RendererViewport")

    def _should_update(self, vp: ViewportData) -> bool:
        mode = vp.update_mode
        if mode == ViewportUpdateMode.UPDATE_DISABLED:
            return False
        if mode == ViewportUpdateMode.UPDATE_ONCE:
            return vp.needs_update
        if mode == ViewportUpdateMode.UPDATE_ALWAYS:
            return True
        if mode == ViewportUpdateMode.UPDATE_WHEN_VISIBLE:
            if not vp.visible:
                return False
            return True
        if mode == ViewportUpdateMode.UPDATE_WHEN_PARENT_VISIBLE:
            if vp.parent:
                parent_vp = self._get_vp(vp.parent)
                return parent_vp.visible if parent_vp else False
        return True

    def _clear_viewport(self, vp: ViewportData) -> None:
        if vp.clear_mode == ViewportClearMode.CLEAR_MODE_NEVER:
            return

        if vp.transparent_bg:
            self.canvas_render.clear_target(Color(0, 0, 0, 0))
        else:
            self.canvas_render.clear_target(vp.clear_color)
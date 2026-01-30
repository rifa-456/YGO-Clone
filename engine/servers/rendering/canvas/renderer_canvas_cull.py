from typing import Optional, Dict, List, Tuple, Union
from engine.core.rid import RID
from engine.math.datatypes.vector2 import Vector2
from engine.math.datatypes.transform2d import Transform2D
from engine.math.datatypes.color import Color
from engine.servers.rendering.canvas.canvas_data import (
    CanvasLight,
    CanvasLayer,
    Canvas,
    Item,
)
from engine.servers.rendering.canvas.commands import (
    CommandRect,
    CommandPrimitive,
    CommandPolygon,
    CommandClipIgnore,
    CommandNinePatch,
)
from engine.servers.rendering.canvas.enums import (
    CanvasItemTextureFilter,
    CanvasItemTextureRepeat,
)
from engine.math.datatypes.rect2 import Rect2
from engine.logger import Logger  # Strict compliance: Added Logger


class RendererCanvasCull:
    def __init__(self):
        self._items: Dict[RID, Item] = {}
        self._canvases: Dict[RID, Canvas] = {}
        self._canvas_layers: Dict[RID, CanvasLayer] = {}
        self._lights: Dict[RID, CanvasLight] = {}
        self.z_range = (-4096, 4096)
        self._item_index_counter: int = 0

    def canvas_allocate(self) -> RID:
        """Create a new canvas"""
        rid = RID()
        self._canvases[rid] = Canvas(rid=rid)
        return rid

    def canvas_initialize(self, canvas: RID) -> None:
        """Initialize canvas"""
        pass

    def canvas_set_transform(self, canvas: RID, transform: Transform2D) -> None:
        """Set canvas transform"""
        if canvas in self._canvases:
            self._canvases[canvas].transform = transform

    def canvas_item_allocate(self) -> RID:
        """Create a new canvas item"""
        rid = RID()
        item = Item(rid=rid, index=self._item_index_counter)
        self._item_index_counter += 1
        self._items[rid] = item
        return rid

    def canvas_item_initialize(self, item_rid: RID) -> None:
        """Initialize canvas item"""
        pass

    def canvas_item_set_parent(self, item_rid: RID, parent_rid: RID) -> None:
        """
        Set parent of canvas item
        Parent can be another CanvasItem or a Canvas
        """
        if item_rid not in self._items:
            return

        item = self._items[item_rid]
        if item.parent:
            item.parent.children.remove(item)
            item.parent = None
        elif item.parent_rid and item.parent_rid in self._canvases:
            self._canvases[item.parent_rid].root_items.discard(item_rid)

        item.parent_rid = parent_rid
        if parent_rid in self._items:
            parent_item = self._items[parent_rid]
            parent_item.children.append(item)
            item.parent = parent_item
            if parent_item.canvas_layer:
                item.canvas_layer = parent_item.canvas_layer

        elif parent_rid in self._canvases:
            canvas = self._canvases[parent_rid]
            canvas.root_items.add(item_rid)
            canvas.items.add(item_rid)

        self._mark_transform_dirty(item)

    def canvas_item_set_transform(self, item_rid: RID, transform: Transform2D) -> None:
        """Set item local transform"""
        if item_rid not in self._items:
            return

        item = self._items[item_rid]
        item.transform = transform
        self._mark_transform_dirty(item)

    def canvas_item_set_clip(self, item_rid: RID, clip: bool) -> None:
        """Enable/disable clipping for this item's children"""
        if item_rid in self._items:
            self._items[item_rid].clip = clip

    def canvas_item_set_visible(self, item_rid: RID, visible: bool) -> None:
        """Set item visibility"""
        if item_rid not in self._items:
            return

        item = self._items[item_rid]
        item.visible = visible
        self._update_visibility_recursive(item)

    def canvas_item_set_z_index(self, item_rid: RID, z_index: int) -> None:
        """Set Z-index for draw order"""
        if item_rid in self._items:
            # Clamp to valid range
            z_index = max(self.z_range[0], min(self.z_range[1], z_index))
            self._items[item_rid].z_index = z_index

    def canvas_item_set_z_as_relative_to_parent(
        self, item_rid: RID, enabled: bool
    ) -> None:
        """Set if Z-index is relative to parent"""
        if item_rid in self._items:
            self._items[item_rid].z_relative = enabled

    def canvas_item_set_sort_children_by_y(self, item_rid: RID, enabled: bool) -> None:
        """Enable Y-sorting for this item's children"""
        if item_rid in self._items:
            self._items[item_rid].sort_y = enabled

    def canvas_item_set_draw_behind_parent(self, item_rid: RID, enabled: bool) -> None:
        """Draw this item behind its parent"""
        if item_rid in self._items:
            self._items[item_rid].behind = enabled

    def canvas_item_set_modulate(self, item_rid: RID, modulate: Color) -> None:
        """Set modulate color (multiplied with children)"""
        if item_rid in self._items:
            self._items[item_rid].modulate = modulate

    def canvas_item_set_self_modulate(self, item_rid: RID, modulate: Color) -> None:
        """Set self modulate (not inherited by children)"""
        if item_rid in self._items:
            self._items[item_rid].self_modulate = modulate

    def canvas_item_set_default_texture_filter(
        self, item_rid: RID, filter: CanvasItemTextureFilter
    ) -> None:
        """Set texture filtering mode"""
        if item_rid in self._items:
            self._items[item_rid].texture_filter = filter

    def canvas_item_set_default_texture_repeat(
        self, item_rid: RID, repeat: CanvasItemTextureRepeat
    ) -> None:
        """Set texture repeat mode"""
        if item_rid in self._items:
            self._items[item_rid].texture_repeat = repeat

    def canvas_item_set_copy_to_backbuffer(
        self, item_rid: RID, enabled: bool, rect: Rect2
    ) -> None:
        """
        Copy screen contents before drawing this item
        Used for blur effects, etc.
        """
        if item_rid in self._items:
            self._items[item_rid].copy_back_buffer = rect if enabled else None

    def canvas_item_clear(self, item_rid: RID) -> None:
        """Clear all drawing commands"""
        if item_rid in self._items:
            self._items[item_rid].commands.clear()
            self._items[item_rid].rect_dirty = True

    def canvas_item_add_line(
        self, item_rid: RID, from_pos: Vector2, to_pos: Vector2, color: Color
    ) -> None:
        """
        Add line drawing command.
        Mapped to CommandPrimitive with PRIMITIVE_LINES.
        """
        if item_rid not in self._items:
            return

        cmd = CommandPrimitive(
            points=[from_pos, to_pos],
            colors=[color, color],
            uvs=[Vector2(0, 0), Vector2(0, 0)],
            texture=None,
            primitive_type=1,
        )
        self._items[item_rid].commands.append(cmd)
        self._items[item_rid].rect_dirty = True

    def canvas_item_add_polyline(
            self,
            item_rid: RID,
            points: List[Vector2],
            colors: List[Color],
            width: float = 1.0,
            antialiased: bool = False,
    ) -> None:
        """
        Draws a connected set of lines with specific width.
        """
        if item_rid not in self._items:
            return

        from engine.servers.rendering.canvas.commands import CommandPolyline

        cmd = CommandPolyline(
            points=points,
            colors=colors,
            width=width,
            antialiased=antialiased
        )
        self._items[item_rid].commands.append(cmd)
        self._items[item_rid].rect_dirty = True

    def canvas_item_add_circle(
        self,
        item_rid: RID,
        position: Vector2,
        radius: Union[float, Vector2],
        color: Color,
    ) -> None:
        """
        Add circle or ellipse drawing command.
        :param radius: If float, creates a circle. If Vector2, creates an ellipse (rx, ry).
        """
        if item_rid not in self._items:
            return

        from engine.servers.rendering.canvas.commands import CommandCircle
        final_radius = radius if isinstance(radius, Vector2) else Vector2(radius, radius)
        cmd = CommandCircle(position=position, radius=final_radius, color=color)
        self._items[item_rid].commands.append(cmd)
        self._items[item_rid].rect_dirty = True

    def canvas_item_add_rect(self, item_rid: RID, rect: Rect2, color: Color) -> None:
        """Add colored rectangle"""
        if item_rid not in self._items:
            return

        cmd = CommandRect(rect=rect, modulate=color)
        self._items[item_rid].commands.append(cmd)
        self._items[item_rid].rect_dirty = True

    def canvas_item_add_texture_rect(
        self,
        item_rid: RID,
        rect: Rect2,
        texture: RID,
        tile: bool = False,
        modulate: Color = None,
    ) -> None:
        """Add textured rectangle"""
        if item_rid not in self._items:
            return

        if modulate is None:
            modulate = Color(1, 1, 1, 1)

        w, h = rect.size.x, rect.size.y
        cmd = CommandPrimitive(
            points=[
                rect.position,
                Vector2(rect.position.x + w, rect.position.y),
                Vector2(rect.position.x + w, rect.position.y + h),
                rect.position + Vector2(0, h),
            ],
            uvs=[
                Vector2(0, 0),
                Vector2(1, 0),
                Vector2(1, 1),
                Vector2(0, 1),
            ],
            colors=[modulate] * 4,
            texture=texture,
            primitive_type=4,
        )
        self._items[item_rid].commands.append(cmd)
        self._items[item_rid].rect_dirty = True

    def canvas_item_add_texture_rect_region(
        self,
        item_rid: RID,
        rect: Rect2,
        texture: RID,
        src_rect: Rect2,
        modulate: Color = None,
    ) -> None:
        """Add textured rectangle with source region"""
        if item_rid not in self._items:
            return

        if modulate is None:
            modulate = Color(1, 1, 1, 1)

        w, h = rect.size.x, rect.size.y
        cmd = CommandPrimitive(
            points=[
                rect.position,
                Vector2(rect.position.x + w, rect.position.y),
                Vector2(rect.position.x + w, rect.position.y + h),
                rect.position + Vector2(0, h),
            ],
            uvs=[
                Vector2(src_rect.position.x, src_rect.position.y),
                Vector2(src_rect.position.x + src_rect.size.x, src_rect.position.y),
                Vector2(
                    src_rect.position.x + src_rect.size.x,
                    src_rect.position.y + src_rect.size.y,
                ),
                Vector2(src_rect.position.x, src_rect.position.y + src_rect.size.y),
            ],
            colors=[modulate] * 4,
            texture=texture,
            primitive_type=4,
        )
        self._items[item_rid].commands.append(cmd)
        self._items[item_rid].rect_dirty = True

    def canvas_item_add_nine_patch(
        self,
        item_rid: RID,
        rect: Rect2,
        source: Rect2,
        texture: RID,
        topleft: Vector2,
        bottomright: Vector2,
        x_axis_mode: int = 0,
        y_axis_mode: int = 0,
        draw_center: bool = True,
        modulate: Color = None,
    ) -> None:
        """Add nine-patch (9-slice) rectangle"""
        if item_rid not in self._items:
            return

        if modulate is None:
            modulate = Color(1, 1, 1, 1)

        cmd = CommandNinePatch(
            rect=rect,
            source=source,
            texture=texture,
            margins=(topleft.x, topleft.y, bottomright.x, bottomright.y),
            draw_center=draw_center,
            modulate=modulate,
        )
        self._items[item_rid].commands.append(cmd)
        self._items[item_rid].rect_dirty = True

    def canvas_item_add_primitive(
        self,
        item_rid: RID,
        points: List[Vector2],
        colors: List[Color],
        uvs: List[Vector2],
        texture: Optional[RID] = None,
    ) -> None:
        """Add custom primitive (triangles)"""
        if item_rid not in self._items:
            return

        cmd = CommandPrimitive(
            points=points,
            colors=colors,
            uvs=uvs,
            texture=texture,
            primitive_type=3,  # TRIANGLES
        )
        self._items[item_rid].commands.append(cmd)
        self._items[item_rid].rect_dirty = True

    def canvas_item_add_polygon(
        self,
        item_rid: RID,
        points: List[Vector2],
        colors: List[Color],
        uvs: List[Vector2] = None,
        texture: Optional[RID] = None,
    ) -> None:
        if item_rid not in self._items:
            return

        if uvs is None:
            uvs = [Vector2(0, 0)] * len(points)

        cmd = CommandPolygon(
            points=points, colors=colors, uvs=uvs, indices=[], texture=texture
        )
        self._items[item_rid].commands.append(cmd)
        self._items[item_rid].rect_dirty = True

    def canvas_item_add_set_transform(
        self, item_rid: RID, transform: Transform2D
    ) -> None:
        pass

    def canvas_item_add_clip_ignore(self, item_rid: RID, ignore: bool) -> None:
        """Disable clipping for subsequent commands"""
        if item_rid not in self._items:
            return

        cmd = CommandClipIgnore(ignore=ignore)
        self._items[item_rid].commands.append(cmd)

    def canvas_layer_create(self) -> RID:
        """Create canvas layer"""
        rid = RID()
        self._canvas_layers[rid] = CanvasLayer(rid=rid)
        return rid

    def canvas_layer_set_layer(self, layer_rid: RID, layer: int) -> None:
        if layer_rid in self._canvas_layers:
            self._canvas_layers[layer_rid].layer = layer

    def canvas_layer_set_transform(
        self, layer_rid: RID, transform: Transform2D
    ) -> None:
        if layer_rid in self._canvas_layers:
            self._canvas_layers[layer_rid].transform = transform

    def cull_canvas(
        self, canvas_rid: RID, viewport_transform: Transform2D, viewport_rect: Rect2
    ) -> List[Tuple[Item, Transform2D, int]]:
        """
        Build sorted render list for a canvas
        Returns: List of (Item, global_transform, final_z)
        """
        if canvas_rid not in self._canvases:
            return []

        canvas = self._canvases[canvas_rid]
        render_list = []
        root_transform = viewport_transform @ canvas.transform
        for item_rid in canvas.root_items:
            if item_rid in self._items:
                item = self._items[item_rid]
                self._cull_item_recursive(
                    item,
                    root_transform,
                    0,
                    Color(1, 1, 1, 1),
                    viewport_rect,
                    render_list,
                )

        render_list.sort(key=lambda x: (x[2], x[0].index))
        return render_list

    def _cull_item_recursive(
            self,
            item: Item,
            parent_transform: Transform2D,
            parent_z: int,
            parent_modulate: Color,
            viewport_rect: Rect2,
            render_list: List,
    ) -> None:
        """Recursively cull and add items to render list"""
        if not item.visible or not item.visible_in_tree:
            return

        item.global_transform = parent_transform @ item.transform
        if item.z_relative:
            final_z = parent_z + item.z_index
        else:
            final_z = item.z_index

        final_z = max(self.z_range[0], min(self.z_range[1], final_z))

        item.final_modulate = Color(
            parent_modulate.r * item.modulate.r * item.self_modulate.r,
            parent_modulate.g * item.modulate.g * item.self_modulate.g,
            parent_modulate.b * item.modulate.b * item.self_modulate.b,
            parent_modulate.a * item.modulate.a * item.self_modulate.a,
        )

        if item.commands:
            render_list.append((item, item.global_transform, final_z))

        children = item.children[:]
        if item.sort_y:
            children.sort(key=lambda child: child.transform.origin.y)
        behind = [c for c in children if c.behind]
        normal = [c for c in children if not c.behind]
        child_modulate = Color(
            item.modulate.r * parent_modulate.r,
            item.modulate.g * parent_modulate.g,
            item.modulate.b * parent_modulate.b,
            item.modulate.a * parent_modulate.a,
        )
        for child in behind:
            self._cull_item_recursive(
                child,
                item.global_transform,
                final_z,
                child_modulate,
                viewport_rect,
                render_list,
            )
        for child in normal:
            self._cull_item_recursive(
                child,
                item.global_transform,
                final_z,
                child_modulate,
                viewport_rect,
                render_list,
            )

    def _mark_transform_dirty(self, item: Item) -> None:
        """Mark item and children as needing transform update"""
        item.rect_dirty = True
        for child in item.children:
            self._mark_transform_dirty(child)

    def _update_visibility_recursive(self, item: Item) -> None:
        """Update inherited visibility"""
        if item.parent:
            item.visible_in_tree = item.visible and item.parent.visible_in_tree
        else:
            item.visible_in_tree = item.visible

        for child in item.children:
            self._update_visibility_recursive(child)

    def free_rid(self, rid: RID) -> None:
        """Free any resource"""
        if rid in self._items:
            item = self._items[rid]
            if item.parent:
                item.parent.children.remove(item)
            elif item.parent_rid and item.parent_rid in self._canvases:
                self._canvases[item.parent_rid].root_items.discard(rid)
            del self._items[rid]

        elif rid in self._canvases:
            del self._canvases[rid]

        elif rid in self._canvas_layers:
            del self._canvas_layers[rid]

        elif rid in self._lights:
            del self._lights[rid]
import pygame
from typing import Optional
from engine.ui.containers.base_container import Container
from engine.ui.widgets.scrollbar import VScrollBar, HScrollBar
from engine.ui.control import Control
from engine.math.datatypes.vector2 import Vector2
from engine.ui.enums import MouseFilter, ScrollMode, SizeFlag


class ScrollContainer(Container):
    """
    A Container that clips its content and allows scrolling via ScrollBars.
    """

    def __init__(self, name: str = "ScrollContainer"):
        super().__init__(name)
        self.clip_contents = True
        self.mouse_filter = MouseFilter.PASS

        self._horizontal_scroll_mode: ScrollMode = ScrollMode.AUTO
        self._vertical_scroll_mode: ScrollMode = ScrollMode.AUTO

        self._scroll_horizontal: int = 0
        self._scroll_vertical: int = 0

        self._h_scroll = HScrollBar("HScrollBar")
        self._h_scroll.visible = False
        self._h_scroll.value_changed.connect(self._on_scroll_h_changed)

        self._v_scroll = VScrollBar("VScrollBar")
        self._v_scroll.visible = False
        self._v_scroll.value_changed.connect(self._on_scroll_v_changed)

        super().add_child(self._h_scroll)
        super().add_child(self._v_scroll)

    @property
    def horizontal_scroll_mode(self) -> ScrollMode:
        return self._horizontal_scroll_mode

    @horizontal_scroll_mode.setter
    def horizontal_scroll_mode(self, value: ScrollMode):
        if self._horizontal_scroll_mode != value:
            self._horizontal_scroll_mode = value
            self.queue_sort()

    @property
    def vertical_scroll_mode(self) -> ScrollMode:
        return self._vertical_scroll_mode

    @vertical_scroll_mode.setter
    def vertical_scroll_mode(self, value: ScrollMode):
        if self._vertical_scroll_mode != value:
            self._vertical_scroll_mode = value
            self.queue_sort()

    def _get_content_node(self) -> Optional[Control]:
        """Returns the first child that isn't a scrollbar."""
        for child in self.children:
            if child is not self._h_scroll and child is not self._v_scroll and isinstance(child, Control):
                return child
        return None

    def _calculate_min_size(self):
        """
        Calculates minimum size.
        ScrollContainer min_size is driven by the 'ALWAYS' visible scrollbars
        or strictly by the visible scrollbars if determined by previous layout.
        It does NOT include the content size, as the point is to scroll.
        """
        ms = Vector2(0, 0)

        if self._horizontal_scroll_mode == ScrollMode.ALWAYS:
            ms.y += self._h_scroll.min_size.y
        elif self._h_scroll.visible:
             ms.y += self._h_scroll.min_size.y

        if self._vertical_scroll_mode == ScrollMode.ALWAYS:
            ms.x += self._v_scroll.min_size.x
        elif self._v_scroll.visible:
            ms.x += self._v_scroll.min_size.x

        self._cached_min_size = ms

    def _reflow_children(self):
        content = self._get_content_node()

        size = self.size
        content_min = content.get_combined_minimum_size() if content else Vector2(0, 0)

        h_mode = self._horizontal_scroll_mode
        v_mode = self._vertical_scroll_mode

        h_scroll_min = self._h_scroll.min_size.y
        v_scroll_min = self._v_scroll.min_size.x

        h_visible = (h_mode == ScrollMode.ALWAYS)
        v_visible = (v_mode == ScrollMode.ALWAYS)

        if not v_visible and v_mode == ScrollMode.AUTO:
            if content_min.y > size.y:
                v_visible = True

        if not h_visible and h_mode == ScrollMode.AUTO:
            avail_w = size.x - (v_scroll_min if v_visible else 0.0)
            if content_min.x > avail_w:
                h_visible = True

        if not v_visible and v_mode == ScrollMode.AUTO:
            avail_h = size.y - (h_scroll_min if h_visible else 0.0)
            if content_min.y > avail_h:
                v_visible = True

        if not h_visible and h_mode == ScrollMode.AUTO:
            avail_w = size.x - (v_scroll_min if v_visible else 0.0)
            if content_min.x > avail_w:
                h_visible = True

        if h_mode == ScrollMode.DISABLED: h_visible = False
        if v_mode == ScrollMode.DISABLED: v_visible = False

        self._h_scroll.visible = h_visible
        self._v_scroll.visible = v_visible

        viewport_w = size.x - (v_scroll_min if v_visible else 0.0)
        viewport_h = size.y - (h_scroll_min if h_visible else 0.0)

        if content:
            final_w = content_min.x
            final_h = content_min.y

            h_expand = bool(content.size_flags_horizontal & SizeFlag.EXPAND)
            v_expand = bool(content.size_flags_vertical & SizeFlag.EXPAND)

            if h_mode != ScrollMode.DISABLED:
                if h_expand and viewport_w > final_w:
                    final_w = viewport_w
            else:
                final_w = max(viewport_w, final_w)

            if v_mode != ScrollMode.DISABLED:
                if v_expand and viewport_h > final_h:
                    final_h = viewport_h
            else:
                final_h = max(viewport_h, final_h)

            content.size = Vector2(final_w, final_h)

            max_scroll_x = max(0, final_w - viewport_w)
            max_scroll_y = max(0, final_h - viewport_h)

            self._scroll_horizontal = max(0, min(self._scroll_horizontal, max_scroll_x))
            self._scroll_vertical = max(0, min(self._scroll_vertical, max_scroll_y))

            content.position = Vector2(-self._scroll_horizontal, -self._scroll_vertical)
        else:
            self._scroll_horizontal = 0
            self._scroll_vertical = 0

        if h_visible:
            self._h_scroll.position = Vector2(0, viewport_h)
            self._h_scroll.size = Vector2(viewport_w, h_scroll_min)
            self._h_scroll.min_value = 0
            self._h_scroll.max_value = content.size.x if content else 0
            self._h_scroll.page = viewport_w
            self._h_scroll.value = self._scroll_horizontal

        if v_visible:
            self._v_scroll.position = Vector2(viewport_w, 0)
            self._v_scroll.size = Vector2(v_scroll_min, viewport_h)
            self._v_scroll.min_value = 0
            self._v_scroll.max_value = content.size.y if content else 0
            self._v_scroll.page = viewport_h
            self._v_scroll.value = self._scroll_vertical

    def _on_scroll_v_changed(self, value: float):
        self._scroll_vertical = int(value)
        content = self._get_content_node()
        if content:
            content.position = Vector2(content.position.x, -self._scroll_vertical)

    def _on_scroll_h_changed(self, value: float):
        self._scroll_horizontal = int(value)
        content = self._get_content_node()
        if content:
            content.position = Vector2(-self._scroll_horizontal, content.position.y)

    def _gui_input(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4:
                if self._v_scroll.visible or self._vertical_scroll_mode != ScrollMode.DISABLED:
                    self._v_scroll.value -= self._v_scroll.step
                    self.accept_event()
                elif self._h_scroll.visible or self._horizontal_scroll_mode != ScrollMode.DISABLED:
                    self._h_scroll.value -= self._h_scroll.step
                    self.accept_event()

            elif event.button == 5:
                if self._v_scroll.visible or self._vertical_scroll_mode != ScrollMode.DISABLED:
                    self._v_scroll.value += self._v_scroll.step
                    self.accept_event()
                elif self._h_scroll.visible or self._horizontal_scroll_mode != ScrollMode.DISABLED:
                    self._h_scroll.value += self._h_scroll.step
                    self.accept_event()

    def add_child(self, child):
        super().add_child(child)
        self.queue_sort()

    @property
    def scroll_vertical(self) -> int:
        return self._scroll_vertical

    @scroll_vertical.setter
    def scroll_vertical(self, value: int):
        self._scroll_vertical = value
        self._v_scroll.value = value
        content = self._get_content_node()
        if content:
            content.position = Vector2(content.position.x, -self._scroll_vertical)
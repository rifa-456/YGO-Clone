from engine.ui.containers.base_container import Container
from engine.ui.control import Control
from engine.math.datatypes.vector2 import Vector2
from engine.math.datatypes.rect2 import Rect2


class PanelContainer(Container):
    """
    A container that fits its child within the area defined by a StyleBox's content margins.
    Draws the StyleBox as a background using the RenderingServer.
    """

    def __init__(self, name: str = "PanelContainer"):
        super().__init__(name)

    def _draw(self):
        """
        Draws the 'panel' StyleBox from the theme to fill the control's rect.
        """
        stylebox = self.get_theme_stylebox("panel")
        if stylebox:
            rect = Rect2(0, 0, self.size.x, self.size.y)
            self.draw_style_box(stylebox, rect)

    def _calculate_min_size(self):
        """
        Calculates min size: Max(Child Min Size) + StyleBox Margins.
        """
        stylebox = self.get_theme_stylebox("panel")
        ms_x = 0.0
        ms_y = 0.0

        for child in self.children:
            if isinstance(child, Control) and child.visible:
                child_ms = child.get_combined_minimum_size()
                if child_ms.x > ms_x:
                    ms_x = child_ms.x
                if child_ms.y > ms_y:
                    ms_y = child_ms.y

        if stylebox:
            ms_x += stylebox.content_margin_left + stylebox.content_margin_right
            ms_y += stylebox.content_margin_top + stylebox.content_margin_bottom

        self._cached_min_size = Vector2(ms_x, ms_y)

    def _reflow_children(self):
        """
        Fits children into the rect minus the StyleBox margins.
        """
        stylebox = self.get_theme_stylebox("panel")
        margin_left = 0.0
        margin_top = 0.0
        margin_right = 0.0
        margin_bottom = 0.0

        if stylebox:
            margin_left = float(stylebox.content_margin_left)
            margin_top = float(stylebox.content_margin_top)
            margin_right = float(stylebox.content_margin_right)
            margin_bottom = float(stylebox.content_margin_bottom)

        w = self.size.x
        h = self.size.y
        available_w = max(0.0, w - margin_left - margin_right)
        available_h = max(0.0, h - margin_top - margin_bottom)

        for child in self.children:
            if isinstance(child, Control) and child.visible:
                rect = Rect2(margin_left, margin_top, available_w, available_h)
                self.fit_child_in_rect(child, rect)

    def _notification(self, what: int) -> None:
        super()._notification(what)

        if what == self.NOTIFICATION_RESIZED:
            self.queue_redraw()

        elif what == Control.NOTIFICATION_THEME_CHANGED:
            self.minimum_size_changed()
            self.queue_sort()
            self.queue_redraw()
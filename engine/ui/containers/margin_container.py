from engine.ui.containers.base_container import Container
from engine.ui.control import Control
from engine.math.datatypes.vector2 import Vector2
from engine.math.datatypes.rect2 import Rect2


class MarginContainer(Container):
    def __init__(self, name="MarginContainer"):
        super().__init__(name)
        self.margin_left = 0
        self.margin_top = 0
        self.margin_right = 0
        self.margin_bottom = 0

    def add_constant_override(self, name: str, value: int):
        if name == "margin_left":
            self.margin_left = value
        elif name == "margin_top":
            self.margin_top = value
        elif name == "margin_right":
            self.margin_right = value
        elif name == "margin_bottom":
            self.margin_bottom = value
        self.on_child_min_size_changed()

    def _calculate_min_size(self):
        max_w = 0.0
        max_h = 0.0
        for child in self.children:
            if isinstance(child, Control) and child.visible:
                ms = child.get_combined_minimum_size()
                max_w = max(max_w, ms.x)
                max_h = max(max_h, ms.y)
        self._cached_min_size = Vector2(
            max_w + self.margin_left + self.margin_right,
            max_h + self.margin_top + self.margin_bottom,
        )

    def _reflow_children(self):
        rect = self.get_rect()
        w = rect.size.x
        h = rect.size.y

        for child in self.children:
            if isinstance(child, Control) and child.visible:
                c_x = float(self.margin_left)
                c_y = float(self.margin_top)
                c_w = max(0.0, w - self.margin_left - self.margin_right)
                c_h = max(0.0, h - self.margin_top - self.margin_bottom)

                target_rect = Rect2(c_x, c_y, c_w, c_h)
                self.fit_child_in_rect(child, target_rect)
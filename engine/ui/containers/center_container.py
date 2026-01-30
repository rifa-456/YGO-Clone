from engine.ui.containers.base_container import Container
from engine.ui.control import Control
from engine.math.datatypes.vector2 import Vector2
from engine.math.datatypes.rect2 import Rect2


class CenterContainer(Container):
    """
    Container that keeps all its children centered within its bounds.
    """

    def __init__(self, name="CenterContainer"):
        super().__init__(name)

    def _calculate_min_size(self):
        max_w = 0.0
        max_h = 0.0
        for child in self.children:
            if isinstance(child, Control) and child.visible:
                ms = child.get_combined_minimum_size()
                if ms.x > max_w:
                    max_w = ms.x
                if ms.y > max_h:
                    max_h = ms.y
        self._cached_min_size = Vector2(max_w, max_h)

    def _reflow_children(self):
        rect = self.get_rect()
        w = rect.size.x
        h = rect.size.y

        for child in self.children:
            if isinstance(child, Control) and child.visible:
                ms = child.get_combined_minimum_size()
                c_x = (w - ms.x) * 0.5
                c_y = (h - ms.y) * 0.5

                target_rect = Rect2(c_x, c_y, ms.x, ms.y)
                self.fit_child_in_rect(child, target_rect)
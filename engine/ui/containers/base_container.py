from engine.math.datatypes.vector2 import Vector2
from engine.math.datatypes.rect2 import Rect2
from engine.ui.control import Control


class Container(Control):
    """
    Base class for controls that arrange their children programmatically.
    """

    def __init__(self, name: str = "Container"):
        super().__init__(name)
        self._cached_min_size = Vector2(0, 0)

    def get_minimum_size(self) -> Vector2:
        return self._cached_min_size

    def add_child(self, child):
        super().add_child(child)
        if isinstance(child, Control):
            if not child.size_flags_changed.is_connected(self.queue_sort):
                child.size_flags_changed.connect(self.queue_sort)
            if not child.minimum_size_changed_signal.is_connected(
                self._on_child_minsize_changed_signal
            ):
                child.minimum_size_changed_signal.connect(
                    self._on_child_minsize_changed_signal
                )
            if not child.visibility_changed.is_connected(self.queue_sort):
                child.visibility_changed.connect(self.queue_sort)

        self._on_child_minsize_changed_signal()
        self.queue_sort()

    def remove_child(self, child):
        if isinstance(child, Control):
            if child.size_flags_changed.is_connected(self.queue_sort):
                child.size_flags_changed.disconnect(self.queue_sort)
            if child.minimum_size_changed_signal.is_connected(
                self._on_child_minsize_changed_signal
            ):
                child.minimum_size_changed_signal.disconnect(
                    self._on_child_minsize_changed_signal
                )
            if child.visibility_changed.is_connected(self.queue_sort):
                child.visibility_changed.disconnect(self.queue_sort)

        super().remove_child(child)
        self._on_child_minsize_changed_signal()
        self.queue_sort()

    def _on_child_minsize_changed_signal(self):
        """Internal handler for child min_size signal."""
        self._calculate_min_size()
        self.minimum_size_changed()
        self.queue_sort()

    def _notification(self, what: int) -> None:
        super()._notification(what)

        if what == self.NOTIFICATION_SORT_CHILDREN:
            self._reflow_children()
        elif what == self.NOTIFICATION_ENTER_TREE:
            self._calculate_min_size()
            self.queue_sort()
        elif what == self.NOTIFICATION_VISIBILITY_CHANGED:
            self.queue_sort()

    def _calculate_min_size(self):
        pass

    def _reflow_children(self):
        pass

    def fit_child_in_rect(self, child: Control, rect: Rect2) -> None:
        child.position = rect.position
        child.size = rect.size
        child.rotation = 0.0
        child.scale = Vector2(1, 1)
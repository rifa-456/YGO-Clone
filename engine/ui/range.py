import math
from engine.ui.control import Control
from engine.scene.main.signal import Signal


class Range(Control):
    """
    Base class for controls that represent a value within a range.
    """

    def __init__(self, name: str = "Range"):
        super().__init__(name)
        self._min_value: float = 0.0
        self._max_value: float = 100.0
        self._step: float = 1.0
        self._page: float = 0.0
        self._value: float = 0.0
        self._allow_greater: bool = False
        self._allow_lesser: bool = False
        self.value_changed = Signal("value_changed")
        self.changed = Signal("changed")

    @property
    def min_value(self) -> float:
        return self._min_value

    @min_value.setter
    def min_value(self, value: float):
        if self._min_value != value:
            self._min_value = value
            self._update_value()
            self.changed.emit()

    @property
    def max_value(self) -> float:
        return self._max_value

    @max_value.setter
    def max_value(self, value: float):
        if self._max_value != value:
            self._max_value = value
            self._update_value()
            self.changed.emit()

    @property
    def step(self) -> float:
        return self._step

    @step.setter
    def step(self, value: float):
        self._step = value
        self.changed.emit()

    @property
    def page(self) -> float:
        return self._page

    @page.setter
    def page(self, value: float):
        if self._page != value:
            self._page = value
            self._update_value()
            self.changed.emit()

    @property
    def value(self) -> float:
        return self._value

    @value.setter
    def value(self, val: float):
        if self._value != val:
            self._value = val
            self._update_value()
            self.value_changed.emit(self._value)

    @property
    def ratio(self) -> float:
        if math.isclose(self._max_value, self._min_value):
            return 0.0
        return (self._value - self._min_value) / (self._max_value - self._min_value)

    @ratio.setter
    def ratio(self, r: float):
        new_val = self._min_value + (self._max_value - self._min_value) * r
        self.value = new_val

    def set_value_no_signal(self, val: float):
        if self._value != val:
            self._value = val
            self._update_value()

    def _update_value(self):
        """
        Validates and clamps the value.
        """
        if not self._allow_lesser and self._value < self._min_value:
            self._value = self._min_value
        if not self._allow_greater and self._value > (self._max_value - self._page):
            self._value = self._max_value - self._page

        if (self._max_value - self._min_value) <= self._page:
            self._value = self._min_value

    def share(self, with_range: "Range"):
        with_range.value_changed.connect(self.set_value_no_signal)
        self.value_changed.connect(with_range.set_value_no_signal)

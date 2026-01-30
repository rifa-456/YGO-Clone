import math
from engine.ui.control import Control
from engine.ui.widgets.label import Label
from engine.math.datatypes.color import Color
from engine.math.datatypes.vector2 import Vector2
from engine.math.datatypes.rect2 import Rect2
from engine.ui.enums import SizeFlag, VerticalAlignment, HorizontalAlignment


class CardStatsBlock(Control):
    """
    Visual divider for the Card Info panel.
    Draws:
    1. A rect (Background)
    2. A circle (Right side)
    3. A star (Inside circle)
    4. A label (Level)
    """

    def __init__(self, name: str = "CardStatsBlock"):
        super().__init__(name)
        self.custom_minimum_size = Vector2(0, 32)
        self.size_flags_horizontal = SizeFlag.EXPAND_FILL

        self.col_rect = Color(185 / 255.0, 145 / 255.0, 75 / 255.0, 1.0)
        self.col_circle = Color(92 / 255.0, 20 / 255.0, 17 / 255.0, 1.0)
        self.col_star = Color(210 / 255.0, 229 / 255.0, 0 / 255.0, 1.0)

        self._lbl_level = Label("", "LevelLabel")
        self._lbl_level.add_theme_color_override("font_color", Color(1, 1, 1, 1))

        self._lbl_level.add_theme_font_override("font", self.get_theme_font("body_font"))
        self._lbl_level.horizontal_alignment = HorizontalAlignment.CENTER
        self._lbl_level.vertical_alignment = VerticalAlignment.CENTER
        self.add_child(self._lbl_level)

        self._level_value: int = 0
        self._show_text: bool = False

        self._star_position: Vector2 = Vector2(0, 0)
        self._star_radius: float = 0.0

    def set_stats(self, level: int):
        self._level_value = level
        self._show_text = True
        self._lbl_level.text = f"x{level}"
        self._lbl_level.visible = True
        self.queue_redraw()

    def reset(self):
        """Resets to default state: Shapes visible, text hidden."""
        self._level_value = 0
        self._show_text = False
        self._lbl_level.text = ""
        self._lbl_level.visible = False
        self.queue_redraw()

    def _draw(self):
        w = self.size.x
        h = self.size.y

        self.draw_rect(Rect2(0, 0, w, h), self.col_rect)

        if self._star_radius > 0:
            self.draw_circle(self._star_position, self._star_radius, self.col_circle)
            star_size = self._star_radius * 0.7
            self._draw_star(self._star_position, star_size, self.col_star)

    def _draw_star(self, center: Vector2, radius: float, color: Color):
        points = []
        angle_off = -math.pi / 2
        for i in range(10):
            r = radius if i % 2 == 0 else radius * 0.4
            angle = angle_off + (i * math.pi / 5)
            x = center.x + math.cos(angle) * r
            y = center.y + math.sin(angle) * r
            points.append(Vector2(x, y))

        self.draw_colored_polygon(points, color)

    def _notification(self, what: int):
        super()._notification(what)
        if what == self.NOTIFICATION_SORT_CHILDREN:
            h = self.size.y
            w = self.size.x
            padding_right = 8.0
            element_spacing = 4.0
            lbl_size = self._lbl_level.get_combined_minimum_size()
            self._star_radius = (h * 0.8) / 2.0
            label_x = w - padding_right - lbl_size.x
            label_y = (h - lbl_size.y) / 2.0
            star_center_x = label_x - element_spacing - self._star_radius
            star_center_y = h / 2.0
            self._lbl_level.position = Vector2(label_x, label_y)
            self._lbl_level.size = lbl_size
            self._star_position = Vector2(star_center_x, star_center_y)
            self.queue_redraw()
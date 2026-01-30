from engine.ui.control import Control
from engine.math.datatypes.color import Color


class Panel(Control):
    """
    Draws a background using the 'panel' StyleBox from the theme.
    """

    def __init__(self, name: str = "Panel"):
        super().__init__(name)

    def get_class(self) -> str:
        return "Panel"

    def _draw(self):
        """
        Draws the panel using the theme's stylebox or a fallback color.
        """
        style = self.get_theme_stylebox("panel")
        rect = self.get_rect()

        if style:
            self.draw_style_box(style, rect)
        else:
            bg_color = self.get_theme_color("panel_bg", "Panel")
            if (
                bg_color.a == 0
                and bg_color.r == 0
                and bg_color.g == 0
                and bg_color.b == 0
            ):
                bg_color = Color(0.15, 0.15, 0.15, 1.0)

            self.draw_rect(rect, bg_color)

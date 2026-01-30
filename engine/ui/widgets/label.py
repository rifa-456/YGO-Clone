from typing import List, Tuple, NamedTuple
import pygame
from engine.ui.control import Control
from engine.ui.enums import HorizontalAlignment, VerticalAlignment
from engine.math.datatypes.vector2 import Vector2
from engine.core.textures.image_texture import ImageTexture
from engine.core.textures.texture import Texture


class WordCache(NamedTuple):
    """
    Immutable representation of a shaped word.
    """
    text: str
    width: float
    height: float
    ascent: float


class LineCache:
    """
    Represents a single horizontal line of text in the layout.
    """

    def __init__(self):
        self.words: List[WordCache] = []
        self.width: float = 0.0
        self.height: float = 0.0
        self.ascent: float = 0.0

    def add_word(self, word: WordCache, spacing: float):
        if self.words:
            self.width += spacing
        self.words.append(word)
        self.width += word.width
        self.height = max(self.height, word.height)
        self.ascent = max(self.ascent, word.ascent)


class Label(Control):

    def __init__(self, text: str = "", name: str = "Label"):
        super().__init__(name)

        self._text: str = text
        self._autowrap_mode: bool = False
        self._uppercase: bool = False
        self._horizontal_alignment: HorizontalAlignment = HorizontalAlignment.LEFT
        self._vertical_alignment: VerticalAlignment = VerticalAlignment.TOP
        self._clip_text: bool = False

        self._word_cache: List[WordCache] = []
        self._lines_cache: List[LineCache] = []
        self._texture_cache: List[Tuple[Vector2, Texture]] = []

        self._dirty_shaping: bool = True
        self._dirty_layout: bool = True
        self._dirty_render: bool = True

        self._cached_min_size: Vector2 = Vector2(0, 0)
        self._last_layout_width: float = -1.0

        self.mouse_filter = 2

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, value: str):
        if self._text != value:
            self._text = value
            self._dirty_shaping = True
            self._dirty_layout = True
            self._dirty_render = True
            self.update_minimum_size()
            self.queue_redraw()

    @property
    def autowrap(self) -> bool:
        return self._autowrap_mode

    @autowrap.setter
    def autowrap(self, value: bool):
        if self._autowrap_mode != value:
            self._autowrap_mode = value
            self._dirty_layout = True
            self._dirty_render = True
            self.update_minimum_size()
            self.queue_redraw()

    @property
    def horizontal_alignment(self) -> HorizontalAlignment:
        return self._horizontal_alignment

    @horizontal_alignment.setter
    def horizontal_alignment(self, value: HorizontalAlignment):
        if self._horizontal_alignment != value:
            self._horizontal_alignment = value
            self._dirty_render = True
            self.queue_redraw()

    @property
    def vertical_alignment(self) -> VerticalAlignment:
        return self._vertical_alignment

    @vertical_alignment.setter
    def vertical_alignment(self, value: VerticalAlignment):
        if self._vertical_alignment != value:
            self._vertical_alignment = value
            self._dirty_render = True
            self.queue_redraw()

    @property
    def uppercase(self) -> bool:
        return self._uppercase

    @uppercase.setter
    def uppercase(self, value: bool):
        if self._uppercase != value:
            self._uppercase = value
            self._dirty_shaping = True
            self._dirty_layout = True
            self._dirty_render = True
            self.update_minimum_size()
            self.queue_redraw()

    def get_minimum_size(self) -> Vector2:
        """
        Calculates the minimum size.
        - If Autowrap is ON: Width is 1 (collapsible), Height is calculated content height.
        - If Autowrap is OFF: Width is content width, Height is content height.
        """
        if self._dirty_shaping or self._dirty_layout:
            self._ensure_layout()
        return self._cached_min_size

    def _notification(self, what: int):
        super()._notification(what)

        if what == self.NOTIFICATION_RESIZED:
            self._on_resized()

        elif what == self.NOTIFICATION_DRAW:
            self._draw_text()

        elif what == self.NOTIFICATION_THEME_CHANGED:
            self._dirty_shaping = True
            self._dirty_layout = True
            self._dirty_render = True
            self.update_minimum_size()
            self.queue_redraw()

    def _on_resized(self):
        """
        Handles the RESIZED notification.
        If autowrap is enabled and width changes, we must reflow text.
        """
        if self._autowrap_mode:
            current_width = self.size.x
            if abs(current_width - self._last_layout_width) > 0.1:
                self._dirty_layout = True
                self._dirty_render = True
                self.update_minimum_size()
                self.queue_redraw()

    def update_minimum_size(self):
        """
        Triggers layout calculation and notifies parent if min_size actually changed.
        This prevents infinite layout loops.
        """
        self._ensure_layout()
        self.minimum_size_changed()

    def _ensure_layout(self):
        """
        Orchestrates the layout pipeline: Shaping -> Flowing.
        """
        font = self.get_theme_font("font")

        if self._dirty_shaping:
            self._shape_text(font)
            self._dirty_shaping = False

        if self._dirty_layout:
            self._reflow_lines(font)
            self._dirty_layout = False

    def _shape_text(self, font: pygame.font.Font):
        """
        Pass 1: Convert raw string into WordCache objects.
        This is independent of width/layout.
        """
        self._word_cache.clear()

        source_text = self._text.upper() if self._uppercase else self._text

        if not source_text:
            return

        paragraphs = source_text.split('\n')
        for i, paragraph in enumerate(paragraphs):
            if i > 0:
                self._word_cache.append(WordCache("\n", 0.0, 0.0, 0.0))

            words = paragraph.split(' ')
            for word_str in words:
                if not word_str:
                    continue

                w, h = font.size(word_str)
                ascent = font.get_ascent()
                self._word_cache.append(WordCache(word_str, float(w), float(h), float(ascent)))

    def _reflow_lines(self, font: pygame.font.Font):
        self._lines_cache.clear()
        self._last_layout_width = self.size.x

        if not self._word_cache:
            line_height = float(font.get_height())
            lc = LineCache()
            lc.height = line_height
            self._lines_cache.append(lc)
            self._cached_min_size = Vector2(0, line_height)
            return

        available_width = max(1.0, self.size.x)
        space_width, _ = font.size(" ")

        current_line = LineCache()

        for word in self._word_cache:
            if word.text == "\n":
                self._lines_cache.append(current_line)
                current_line = LineCache()
                current_line.height = float(font.get_height())
                continue

            spacing = space_width if current_line.words else 0.0

            if self._autowrap_mode:
                if (current_line.width + spacing + word.width > available_width) and current_line.words:
                    self._lines_cache.append(current_line)
                    current_line = LineCache()
                    spacing = 0.0

            current_line.add_word(word, spacing)

        if current_line.words or (not self._lines_cache):
            self._lines_cache.append(current_line)

        max_line_width = 0.0
        total_height = 0.0

        for line in self._lines_cache:
            max_line_width = max(max_line_width, line.width)
            total_height += line.height

        min_w = 1.0 if self._autowrap_mode else max_line_width
        self._cached_min_size = Vector2(min_w, total_height)

    def _ensure_textures(self):
        """
        Generates textures for the current line layout.
        Uses cached shaping data.
        """
        if not self._dirty_render:
            return

        self._texture_cache.clear()
        font = self.get_theme_font("font")
        color = self.get_theme_color("font_color")

        color_rgba = (
            int(color.r * 255),
            int(color.g * 255),
            int(color.b * 255),
            int(color.a * 255)
        )

        space_width, _ = font.size(" ")

        total_h = self.size.y
        content_h = self._cached_min_size.y

        start_y = 0.0
        if self._vertical_alignment == VerticalAlignment.CENTER:
            start_y = (total_h - content_h) * 0.5
        elif self._vertical_alignment == VerticalAlignment.BOTTOM:
            start_y = total_h - content_h

        y_cursor = start_y

        for line in self._lines_cache:
            if not line.words:
                y_cursor += line.height
                continue

            x_cursor = 0.0
            available_w = self.size.x

            if self._horizontal_alignment == HorizontalAlignment.CENTER:
                x_cursor = (available_w - line.width) * 0.5
            elif self._horizontal_alignment == HorizontalAlignment.RIGHT:
                x_cursor = available_w - line.width

            for i, word in enumerate(line.words):
                surf = font.render(word.text, True, color_rgba)
                tex = ImageTexture(surf)
                pos = Vector2(x_cursor, y_cursor)
                self._texture_cache.append((pos, tex))

                x_cursor += word.width + space_width

            y_cursor += line.height

        self._dirty_render = False

    def _draw_text(self):
        """
        Draws the cached textures.
        """
        if self._dirty_layout:
            self._ensure_layout()

        if self._dirty_render:
            self._ensure_textures()

        for pos, tex in self._texture_cache:
            self.draw_texture(tex, pos)

    def set_text(self, text: str):
        self.text = text
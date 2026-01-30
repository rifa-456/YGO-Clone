from typing import Optional

from engine.core.resource_loader import ResourceLoader
from engine.core.textures.texture import Texture
from engine.math.datatypes.color import Color
from engine.math.datatypes.vector2 import Vector2
from engine.ui.widgets.label import Label
from engine.ui.widgets.panel import Panel
from engine.ui.widgets.texture_rect import TextureRect
from engine.ui.containers.v_box_container import VBoxContainer
from engine.ui.containers.margin_container import MarginContainer
from engine.ui.containers.panel_container import PanelContainer
from engine.ui.containers.scroll_container import ScrollContainer
from engine.ui.theme import StyleBoxFlat
from engine.ui.enums import SizeFlag, LayoutPreset, ScrollMode
from game.autoload.card_database import CardData
from game.autoload.texture_registry import TextureRegistry
from game.entities.card.card import Card
from game.scenes.duel.hud.card_stats_block import CardStatsBlock


class CardInfo(Panel):
    """
    Left Sidebar displaying the selected card details.

    Structure:
    - Card Art (Top)
    - Stats Divider (Rect/Circle/Star)
    - Description Box (Bottom, Scrollable)
    """

    CARD_PANEL_WIDTH = 300
    PREVIEW_SCALE = 1.75

    def __init__(self, name: str = "CardInfoPanel") -> None:
        super().__init__(name=name)
        self.custom_minimum_size = Vector2(self.CARD_PANEL_WIDTH, 0)
        self.size_flags_horizontal = 0
        self.size_flags_vertical = SizeFlag.EXPAND_FILL

        self._tex_card: Optional[TextureRect] = None
        self._stats_block: Optional[CardStatsBlock] = None
        self._lbl_desc: Optional[Label] = None
        self._scroll: Optional[ScrollContainer] = None

        self._build_ui()
        self.reset_state()
        self.visible = True

    def _build_ui(self) -> None:
        margin = MarginContainer("ContentMargin")
        margin.set_anchors_preset(LayoutPreset.FULL_RECT)
        margin.add_constant_override("margin_left", 0)
        margin.add_constant_override("margin_top", 12)
        margin.add_constant_override("margin_right", 0)
        margin.add_constant_override("margin_bottom", 0)
        self.add_child(margin)

        vbox = VBoxContainer(separation=0, name="CardInfoVBox")
        vbox.size_flags_horizontal = SizeFlag.EXPAND_FILL
        vbox.size_flags_vertical = SizeFlag.EXPAND_FILL
        margin.add_child(vbox)

        self._tex_card = TextureRect(None, "CardArt")
        self._tex_card.stretch_mode = True
        self._tex_card.expand_mode = True
        self._tex_card.size_flags_horizontal = SizeFlag.SHRINK_CENTER
        self._tex_card.size_flags_vertical = SizeFlag.SHRINK_CENTER
        vbox.add_child(self._tex_card)

        self._stats_block = CardStatsBlock("StatsBlock")
        vbox.add_child(self._stats_block)

        desc_box = PanelContainer("DescBox")
        desc_box.size_flags_horizontal = SizeFlag.EXPAND_FILL
        desc_box.size_flags_vertical = SizeFlag.EXPAND_FILL
        desc_box.size_flags_stretch_ratio = 1.0

        style = StyleBoxFlat()
        style.bg_color = Color(0, 0, 0, 0.7)
        desc_box.add_theme_stylebox_override("panel", style)

        desc_margin = MarginContainer("DescMargin")
        desc_margin.add_constant_override("margin_left", 8)
        desc_margin.add_constant_override("margin_right", 8)
        desc_margin.add_constant_override("margin_top", 8)
        desc_margin.add_constant_override("margin_bottom", 8)
        desc_box.add_child(desc_margin)

        self._scroll = ScrollContainer("DescScroll")
        self._scroll.size_flags_horizontal = SizeFlag.EXPAND_FILL
        self._scroll.size_flags_vertical = SizeFlag.EXPAND_FILL


        self._scroll.vertical_scroll_mode = ScrollMode.ALWAYS
        self._scroll.horizontal_scroll_mode = ScrollMode.DISABLED

        desc_margin.add_child(self._scroll)

        self._lbl_desc = Label("", "DescLabel")
        self._lbl_desc.autowrap = True
        self._lbl_desc.size_flags_horizontal = SizeFlag.EXPAND_FILL
        self._lbl_desc.size_flags_vertical = SizeFlag.EXPAND_FILL

        self._lbl_desc.add_theme_font_override("font", self.get_theme_font("body_font"))
        self._scroll.add_child(self._lbl_desc)

        vbox.add_child(desc_box)

    def set_card(self, data: CardData) -> None:
        """
        Updates the info panel with specific card data.
        """
        if not data:
            self.reset_state()
            return

        tex = ResourceLoader.load(data.texture_path, Texture)
        if not tex:
            tex = TextureRegistry.get(Card.KEY_CARD_BACK)
        self._tex_card.texture = tex
        self._apply_art_size_constraints()

        if hasattr(data, "level") and data.level > 0:
            self._stats_block.set_stats(data.level)
        else:
            self._stats_block.reset()

        self._lbl_desc.text = data.description
        self._scroll.scroll_vertical = 0

    def reset_state(self) -> None:
        """
        Restores the panel to the default state.
        - Card Art: Back
        - Stats: Divider Visible, but no text.
        - Description: Empty.
        """
        tex = TextureRegistry.get(Card.KEY_CARD_BACK)
        if not tex:
            tex = ResourceLoader.load(Card.KEY_CARD_BACK, Texture)

        if self._tex_card:
            self._tex_card.texture = tex
            self._apply_art_size_constraints()

        if self._stats_block:
            self._stats_block.reset()

        self._lbl_desc.text = ""
        self._scroll.scroll_vertical = 0

    def _apply_art_size_constraints(self) -> None:
        """Recalculates size constraints for the static texture."""
        if not self._tex_card:
            return

        target_width = Card.CARD_WIDTH * self.PREVIEW_SCALE
        target_height = target_width * Card.CARD_ASPECT_RATIO
        self._tex_card.custom_minimum_size = Vector2(
            int(target_width), int(target_height)
        )
from typing import List
from engine.ui.control import Control
from engine.math.datatypes.vector2 import Vector2
from engine.ui.enums import LayoutPreset
from game.autoload.card_database import CardData
from .deck_logic import DeckLogic
from .deck_visuals import DeckVisuals
from ..slot import Slot


class Deck(Control):
    """
    Root Entity for the Player's Deck.
    """

    def __init__(self, cards: List[CardData], name: str = "PlayerDeck"):
        super().__init__(name)
        width = Slot.SLOT_WIDTH
        height = Slot.SLOT_HEIGHT
        self.custom_minimum_size = Vector2(width, height)
        self.logic = DeckLogic(cards)
        self.visuals = DeckVisuals("DeckVisuals")
        self.add_child(self.visuals)
        self.visuals.set_anchors_preset(LayoutPreset.FULL_RECT)

        self.logic.on_count_changed.connect(self._on_count_changed)

    def set_quad_geometry(self, points: list[Vector2]) -> None:
        """
        Receives the perspective geometry from the Slot (in Slot's Local Coordinates).
        """
        if not points:
            return

        self.position = Vector2(0, 0)
        self.rotation = 0
        self.visuals.set_quad_geometry(points)

    def _ready(self):
        """
        Called when the Deck enters the Scene Tree.
        """
        super()._ready()
        self.logic.shuffle()

    def _on_count_changed(self, count: int) -> None:
        self.visuals.update_count(count)
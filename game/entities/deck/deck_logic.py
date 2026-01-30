import random
from typing import List, Optional
from engine.scene.main.signal import Signal
from game.autoload.card_database import CardData


class DeckLogic:
    def __init__(self, cards: List[CardData]) -> None:
        self.cards: List[CardData] = list(cards)
        self.on_count_changed = Signal("on_count_changed")

    def shuffle(self) -> None:
        random.shuffle(self.cards)
        self.on_count_changed.emit(len(self.cards))

    def pop_card(self) -> Optional[CardData]:
        if not self.cards:
            return None

        card = self.cards.pop()
        self.on_count_changed.emit(len(self.cards))
        return card

    def get_count(self) -> int:
        return len(self.cards)

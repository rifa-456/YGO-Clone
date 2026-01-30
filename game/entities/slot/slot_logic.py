from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from game.entities.card import Card


class SlotLogic:
    def __init__(self):
        self.card_node: Optional["Card"] = None

    def is_occupied(self) -> bool:
        """Returns True if a card is currently in this slot."""
        return self.card_node is not None

    def set_card(self, card: "Card") -> None:
        """
        Assigns a card to this slot.
        Raises ValueError if slot is already occupied.
        """
        if self.is_occupied():
            raise ValueError("Slot is already occupied")
        self.card_node = card

    def clear_card(self) -> Optional["Card"]:
        """
        Removes and returns the card from this slot.
        Returns None if slot was empty.
        """
        if not self.is_occupied():
            return None
        card = self.card_node
        self.card_node = None
        return card

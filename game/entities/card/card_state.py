from enum import IntEnum


class CardState(IntEnum):
    """
    Represents the gameplay state of a card.
    """

    HAND = 0
    FIELD_ATTACK = 1
    FIELD_DEFENSE = 2
    GRAVEYARD = 3

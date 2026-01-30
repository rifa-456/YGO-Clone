from enum import IntEnum, auto


class SlotType(IntEnum):
    MONSTER = auto()
    SPELL_TRAP = auto()
    FIELD = auto()
    DECK = auto()
    GRAVEYARD = auto()
    BANISHED = auto()
    EXTRA_DECK = auto()

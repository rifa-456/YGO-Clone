from enum import Enum, auto


class DuelInputState(Enum):
    """
    Input states for the duel FSM.
    Moves the implicit state machine from DuelScene into a formal definition.
    """

    IDLE = auto()
    WAITING_FOR_SLOT_SELECTION = auto()
    SUMMONING_GHOST = auto()
    WAITING_FOR_TRIBUTE_SELECTION = auto()

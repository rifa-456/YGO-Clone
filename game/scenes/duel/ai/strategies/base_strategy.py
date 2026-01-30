from abc import ABC, abstractmethod
from typing import Optional, List, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from game.entities.card.card import Card
    from game.entities.slot.slot import Slot
    from game.entities.board.board import Board
    from game.entities.hand.hand import Hand


class AIStrategy(ABC):
    """
    Abstract base for AI decision-making logic.
    Decouples 'Thinking' (Strategy) from 'Acting' (AIAgent).
    """

    @abstractmethod
    def decide_summon(
        self, hand: "Hand", my_board: "Board", opp_board: "Board"
    ) -> Optional[Tuple["Card", List["Slot"]]]:
        """
        Evaluates the hand and board to pick a monster to summon.
        Returns:
            (Card_to_Summon, List_of_Tribute_Slots) or None.
        """
        pass

    @abstractmethod
    def decide_attack_target(
        self, attacker: "Card", opp_board: "Board"
    ) -> Optional["Slot"]:
        """
        Selects an optimal attack target for the given attacker.
        Returns:
            Target Slot or None (if no valid target or decision to not attack).
        """
        pass

    @abstractmethod
    def should_set_in_defense(self, card: "Card", opp_board: "Board") -> bool:
        """
        Determines if a monster should be Normal Summoned (Attack) or Set (Defense).
        """
        pass

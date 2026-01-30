from dataclasses import dataclass
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from game.entities.card.card import Card
    from game.entities.board.board import Board
    from game.scenes.duel.logic.duel_mediator import DuelMediator


@dataclass
class EffectContext:
    """
    Transient state object passed through the resolution chain.
    Captures the 'Universe' at the moment of activation.
    """

    mediator: "DuelMediator"
    source_card: "Card"
    player_board: "Board"
    enemy_board: "Board"
    event_trigger_card: Optional["Card"] = None
    selected_targets: List["Card"] = None

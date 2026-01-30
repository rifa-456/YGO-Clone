from typing import Optional, TYPE_CHECKING
from engine.core.object import Object

if TYPE_CHECKING:
    from game.entities.board import Board
    from game.entities.hand import Hand
    from game.entities.deck.deck_logic import DeckLogic
    from game.scenes.duel.logic.turn_handler import TurnHandler


class GameState(Object):
    """
    Pure Data Container for the Duel's State.
    Maintains references to all gameplay entities and lifecycle data.
    """

    def __init__(self):
        super().__init__()
        self.turn_handler: Optional["TurnHandler"] = None

        self.player_board: Optional["Board"] = None
        self.player_hand: Optional["Hand"] = None
        self.player_deck: Optional["DeckLogic"] = None
        self.player_lp: int = 8000

        self.enemy_board: Optional["Board"] = None
        self.enemy_hand: Optional["Hand"] = None
        self.enemy_deck: Optional["DeckLogic"] = None
        self.enemy_lp: int = 8000

    def configure(self, turn_handler, p_board, e_board, p_hand, e_hand, p_deck, e_deck):
        self.turn_handler = turn_handler
        self.player_board = p_board
        self.enemy_board = e_board
        self.player_hand = p_hand
        self.enemy_hand = e_hand
        self.player_deck = p_deck
        self.enemy_deck = e_deck

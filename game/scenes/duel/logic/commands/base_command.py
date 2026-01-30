from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game.scenes.duel.logic.game_state import GameState
    from game.scenes.duel.logic.duel_mediator import DuelMediator


class DuelCommand(ABC):
    """Abstract base for all gameplay state mutations."""

    @abstractmethod
    def execute(self, state: "GameState", mediator: "DuelMediator") -> None:
        pass

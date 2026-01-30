import random
from enum import Enum, auto
from engine.core.object import Object
from engine.logger import Logger
from engine.scene.main.signal import Signal


class GamePhase(Enum):
    DRAW = auto()
    MAIN = auto()
    BATTLE = auto()
    END = auto()


class TurnOwner(Enum):
    PLAYER = auto()
    ENEMY = auto()


class TurnHandler(Object):
    """
    Logic Component: Manages the temporal state of the Duel.
    """

    def __init__(self):
        super().__init__()
        self.current_phase = GamePhase.DRAW
        self.current_turn_owner = TurnOwner.PLAYER
        self.turn_count = 1
        self.game_state = None

        self.on_phase_change = Signal("on_phase_change")
        self.on_turn_start = Signal("on_turn_start")
        self.on_turn_owner_changed = Signal("on_turn_owner_changed")

    def bind_game_state(self, game_state):
        """Called once by the mediator after GameState creation."""
        self.game_state = game_state

    def next_phase(self):
        old_phase = self.current_phase

        if self.current_phase == GamePhase.DRAW:
            self.current_phase = GamePhase.MAIN

        elif self.current_phase == GamePhase.MAIN:
            self.current_phase = GamePhase.BATTLE

        elif self.current_phase == GamePhase.BATTLE:
            self.current_phase = GamePhase.END

        elif self.current_phase == GamePhase.END:
            self.current_phase = GamePhase.DRAW
            self._switch_turn_owner()
            self.turn_count += 1
            self.on_turn_start.emit()

        Logger.info(
            f"Phase Switch: {old_phase.name} -> {self.current_phase.name}",
            "TurnHandler",
        )

        self.on_phase_change.emit(self.current_phase)

    def _switch_turn_owner(self):
        if self.current_turn_owner == TurnOwner.PLAYER:
            self.current_turn_owner = TurnOwner.ENEMY
        else:
            self.current_turn_owner = TurnOwner.PLAYER

        Logger.info(
            f"Turn Owner Switch: {self.current_turn_owner.name}",
            "TurnHandler",
        )
        self.on_turn_owner_changed.emit(self.current_turn_owner)
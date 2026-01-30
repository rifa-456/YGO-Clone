from typing import TYPE_CHECKING
from engine.logger import Logger
from .signals import TurnSignals, HandSignals, CombatSignals, UISignals

if TYPE_CHECKING:
    from .duel_scene import DuelScene


class DuelSceneSignals:
    """
    Central coordinator for all scene signal wiring.
    Replaces the monolithic _wire_signals() method.
    """

    def __init__(self, scene: "DuelScene"):
        self.scene = scene
        self.turn = TurnSignals(scene)
        self.hand = HandSignals(scene)
        self.combat = CombatSignals(scene)
        self.ui = UISignals(scene)

    def wire_all(self) -> None:
        """Wire all subsystems in logical execution order."""
        Logger.info("Starting Signal Wiring Sequence...", "DuelSceneSignals")
        self.turn.wire()
        self.combat.wire()
        self.hand.wire()
        self.ui.wire()

        Logger.info("Signal Wiring Complete.", "DuelSceneSignals")

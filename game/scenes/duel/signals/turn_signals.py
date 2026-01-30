from typing import TYPE_CHECKING
from engine.logger import Logger

if TYPE_CHECKING:
    from ..duel_scene import DuelScene


class TurnSignals:
    """
    Handles turn system signal wiring.
    Responsibility: Phase changes, turn owner switches.
    """

    def __init__(self, scene: "DuelScene"):
        self.scene = scene

    def wire(self) -> None:
        Logger.info("Wiring Turn Signals...", "TurnSignals")
        self.scene.turn_handler.on_turn_start.connect(self._handle_turn_start)

    def _handle_turn_start(self):
        self.scene.mediator.request_draw()
        self.scene.turn_handler.next_phase()

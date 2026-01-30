from typing import TYPE_CHECKING
from engine.logger import Logger

if TYPE_CHECKING:
    from ..duel_scene import DuelScene
    from game.entities.card import Card


class HandSignals:
    def __init__(self, scene: "DuelScene"):
        self.scene = scene

    def wire(self) -> None:
        Logger.info("Wiring Hand Signals...", "HandSignals")
        self.scene.hand.on_card_chosen.connect(self._on_hand_card_clicked)
        self.scene.hand.on_focus_state_changed.connect(self._on_hand_focus_changed)

    def _on_hand_card_clicked(self, card: "Card"):
        """
        Delegates to InputController.
        """
        self.scene.input_controller.handle_hand_card_clicked(card)

    def _on_hand_focus_changed(self, active: bool):
        """Adjusts the vertical position of the hand based on focus state."""
        hand_margin = self.scene.find_child("HandMargin", recursive=True, owned=False)
        if not hand_margin:
            return

        target_margin = -40 if active else 30
        hand_margin.add_constant_override("margin_top", target_margin)
        hand_margin.queue_sort()
